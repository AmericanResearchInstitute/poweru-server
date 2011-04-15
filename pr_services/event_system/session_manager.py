"""
Session manager class
"""

from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.template import Template, Context
from django.template.loader import get_template
from pr_services import pr_time
from pr_services import exceptions
from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade
import logging
from pr_messaging import send_message

class SessionManager(ObjectManager):
    """
    Manage Sessions in the Power Reg system

    A Session can be associated with SessionUserRoles. That association is
    called a 'SessionUserRoleRequirement'. That allows us to define how many of
    each role we want, what credential_types we will require, and which users are
    actually going to fill the role. Because a Session can be associated with an
    SessionUserRole more than once (for example, to specify two different sets of
    credential_types), there are a few places where these methods will take or receive
    a SessionUserRoleRequirement primary key. All you really need to know is
    that each association of a Session with a SessionUserRole yields a
    SessionUserRoleRequirement.
    
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        self.getters.update( {
            'audience' : 'get_general',
            'confirmed' : 'get_general',
            'session_template' : 'get_foreign_key',
            'default_price' : 'get_general',
            'end' : 'get_time',
            'evaluation' : 'get_foreign_key',
            'modality' : 'get_general',
            'name' : 'get_general',
            'paypal_url' : 'get_paypal_url_from_session',
            'start' : 'get_time',
            'status' : 'get_general',
            'title' : 'get_general',
            'url' : 'get_general',
            'description' : 'get_general',
            'room' : 'get_foreign_key',
            'event' : 'get_foreign_key',
            'session_user_role_requirements' : 'get_many_to_one',
        } )
        #: Dictionary of attribute names and the functions used to set them
        self.setters.update({
            'audience' : 'set_general',
            'confirmed' : 'set_general',
            'session_template' : 'set_foreign_key',
            'default_price' : 'set_general',
            'end' : 'set_time',
            'modality' : 'set_general',
            'name' : 'set_general',
            'start' : 'set_time',
            'status' : 'set_general',
            'title' : 'set_general',
            'url' : 'set_general',
            'description' : 'set_general',
            'room' : 'set_foreign_key',
            'event' : 'set_foreign_key',
            'session_user_role_requirements' : 'set_many',
        })
        self.my_django_model = facade.models.Session
        self.session_user_role_requirement_manager = facade.managers.SessionUserRoleRequirementManager()
        self.logger = logging.getLogger('pr_services.SessionManager')

    @service_method
    def create(self, auth_token, start, end, status, confirmed, default_price,
            event, optional_attributes=None):
        """
        Create a new Session

        @param start                  Start time as ISO8601 string
        @type start string
        @param end                    End time as ISO8601 string
        @type end string
        @param status                 String: one of 'active', 'pending', 'canceled', 'completed'
        @param confirmed              is this Session confirmed?
        @type confirmed bool
        @param default_price          Default Price in cents
        @param event                  Foreign Key for an event
        @param optional_attributes    Optional attribute values indexed by name
        @return                       Instance of Session
                                      dict with new primary key indexed as 'id'
        """

        if optional_attributes is None:
            optional_attributes = {}

        new_session = self._create(auth_token, start, end, status, confirmed, default_price,
                event, optional_attributes)
        self.authorizer.check_create_permissions(auth_token, new_session)
        return new_session

    def _create(self, auth_token, start, end, status, confirmed, default_price,
            event, optional_attributes=None):
        """
        Create a new Session
        
        @param start          Start time, ISO8601 string
        @param end            End time, ISO8601 string
        @param status         String: one of 'active', 'pending', 'canceled', 'completed'
        @param confirmed      Boolean: is this Session confirmed?
        @param default_price  Default price for the Session in US cents
        @return               Instance of Session
        """

        if optional_attributes is None:
            optional_attributes = {}

        actor = auth_token.user
        b = facade.managers.BlameManager().create(auth_token)
        end = pr_time.iso8601_to_datetime(end)
        name = str(end.year)+str(end.month)+str(end.day)
        new_session = self.my_django_model(start = pr_time.iso8601_to_datetime(start), end=end, name=name,
                status=status, confirmed=confirmed, default_price=default_price,
                blame=b)
        if 'session_template' in optional_attributes:
            the_session_template = self._find_by_id(optional_attributes['session_template'], facade.models.SessionTemplate)
            if the_session_template.shortname:
                new_session.name = the_session_template.shortname + name
            if the_session_template.description is not None:
                new_session.description = the_session_template.description
            if (the_session_template.price is not None) and (new_session.default_price is None):
                new_session.default_price = the_session_template.price
            if (the_session_template.modality is not None) and (new_session.modality is None):
                new_session.modality = the_session_template.modality
        new_session.event = self._find_by_id(event, facade.models.Event)
        new_session.save()
        if 'session_template' in optional_attributes:
            if (the_session_template.session_template_user_role_requirements.all().count() != 0):
                # We need to create a session_user_role_requirement for each of these and associate it with this session
                for session_template_user_role_requirement in the_session_template.session_template_user_role_requirements.all():
                    new_session_user_role_requirement = self.session_user_role_requirement_manager.create(auth_token, new_session.id,
                        session_template_user_role_requirement.session_user_role.id, session_template_user_role_requirement.min, session_template_user_role_requirement.max, False)
            new_session.session_template = the_session_template
            del optional_attributes['session_template']
        new_session.name = new_session.name+new_session.mangle_id(new_session.id)
        new_session.save()
        if optional_attributes:
            facade.subsystems.Setter(auth_token, self, new_session, optional_attributes)
            new_session.save()
        return new_session

    @service_method
    def get_sessions_by_user_role(self, auth_token, user_id, session_user_role_id):
        """
        Get Sessions by user and SessionUserRole
        
        @param user_id                user primary key
        @param session_user_role_id   SessionUserRole primary key
        @return                       array of Session primary keys
        """

        try:
            e = facade.models.SessionUserRoleRequirement.objects.filter(users__id__exact=user_id,
                session_user_role__id__exact = session_user_role_id)
        except ObjectDoesNotExist:
            raise exceptions.SessionUserRoleRequirementNotFoundException()
        else:
            ids = []
            auth = self.authorizer
            for pr_object in e.iterator():
                auth.check_read_permissions(auth_token, pr_object, ['id'])
                ids.append(str(pr_object.id))
        return ids

    @service_method
    def get_user_filtered(self, auth_token, user_id, filters):
        """
        Get Sessions filtered by various limits, including a particular user.
        
        @param user_id    Primary key for a user
        @param filters    A struct of structs indexed by filter name. Each
                          filter's struct should contain values indexed by
                          field names.
        """

        if 'exact' not in filters:
            filters['exact'] = {}
        filters['exact']['session_user_role_requirements__users__id'] = user_id
        return self.filter_common(auth_token, filters)

    def _get_sessions_needing_reminders(self):
        """
        get a list of events that need reminders sent through
        lead time expiry
        """

        res = []
        # search through all events where reminders haven't
        # been sent, sending our reminders for the ones where
        # the lead time has expired
        current_time = datetime.utcnow()
        sessions = self.my_django_model.objects.filter(sent_reminders=False,
                start__gte=current_time)
        for session in sessions:
            if session.event.lead_time == None:
                continue
            expiration_time = datetime.fromordinal(session.start.toordinal()) -\
                timedelta(seconds=session.event.lead_time)
            if current_time >= expiration_time and session.status == 'active':
                res.append(session)
                
        return res

    def _process_session_reminders(self):
        """
        send Session reminders for all eligible Sessions

        This is not available via RPC.
        """

        sessions_to_process = self._get_sessions_needing_reminders()
        for session in sessions_to_process:
            recipients = set()
            for surr in session.session_user_role_requirements.all():
                for user in surr.users.all():
                    recipients.add(user)
            send_message(message_type='session-reminder',
                         context={'session': session}, recipients=recipients)
            session.sent_reminders = True
            session.save()

    @service_method
    def remind_invitees(self, auth_token, session_id):
        """
        remind invitees of an upcoming Session

         This method sends Session reminders for an Session regardless of whether
        they have already been sent and regardless of the Session's status.  This
        is mostly for demos.

         The system will not remember that it has sent Session reminders via
        this method -- they will still be sent asynchronously on lead time
        expiry if they haven't already.

        @param auth_token
        @param session_id   primary key of Session in question
        @returns            None
        """

        session = self._find_by_id(session_id)
        recipients = set()
        for surr in session.session_user_role_requirements.all():
            for user in surr.users.all():
                recipients.add(user)
        send_message(message_type='session-reminder',
                     context={'session': session}, recipients=recipients)

    @service_method
    def get_evaluation_results(self, auth_token, session):
        """
        Get the feedback that users provide through evaluations

        @param session      Primary Key for a Session.
        @return             List of response Sessions from users.  Each Session is a
                            struct with lists indexed as 'questions' and 'ratings'.
                            The 'questions' list contains structs with the user's text
                            indexed as 'response', and a struct with keys 'text' and 'id'
                            indexed as 'question'.  An example question entry:
                            {'question' : {'text' : 'Was the instructor smart?', 'id' : 523},
                            'response' : 'Yes, I thought the instructor was fairly
                            smart, but he was sure no Pete Miller.'}

                            The 'ratings' list will be a list of structs similar to
                            that described above for questions. An example:
                            {'rating' : {'text' : 'How likely is it that the IT
                            department will go to Vegas to celebrate power reg?',
                            'id' : 53, 'seek' : 1, 'limit' : 9}, 'selection' : 8,
                            'response' : 'This is my text response'}
                            Note that the 'selection' key is optional. In its place,
                            you may see " 'na' : True " if the user responded with N/A.
                            Also, the selection returned is 0-based, as is the limit.
                            In the above example, the user's choices were [1, 2,
                            3, 4, 5, 6, 7, 8, 9, 10], and they chose '9'. We store
                            this on a scale from 0-9 with a seek of 1.
        """

        s = self._find_by_id(session)
        self.authorizer.check_read_permissions(auth_token, s, ['evaluation'])

        if not isinstance(s.evaluation, facade.models.Exam):
            raise exceptions.ObjectNotFoundException('Evaluation')

        evals = []
        for assignment in s.evaluation.assignments.all():
            try:
                evaluation = assignment.assignment_attempts.get(date_completed__isnull=False).downcast_completely()
            except (facade.models.AssignmentAttempt.DoesNotExist, facade.models.AssignmentAttempt.MultipleObjectsReturned):
                continue

            eval_dict = {'id': evaluation.id, 'questions': []}

            for q in evaluation.response_questions.all():
                q_dict = {'id': q.id, 'question_type': q.question_type,
                          'label': q.label}
                r = q.responses.get(exam_session=evaluation)
                r_dict = {'value': r.value, 'text': r.text, 'valid': r.valid}
                eval_dict['questions'].append({'question': q_dict,
                                               'response': r_dict})
            evals.append(eval_dict)
        return evals


# vim:tabstop=4 shiftwidth=4 expandtab
