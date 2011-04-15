from django.core.urlresolvers import reverse
from django.template import Context, loader
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseNotFound
from pr_services import exceptions
from pr_services.utils import Utils
import datetime
import settings
import urllib
import facade

class ScormServer(object):
    def db_post_form(self, request, auth_token, sco_session_id, shared_object=''):
        """
        This method loads the webform that is used to post data back to us, and fills out some
        info about the sco_session to it.
        """
        t = loader.get_template('db_post_form')
        c = Context({
            'auth_token' : auth_token,
            'sco_session_id' : sco_session_id,
            'shared_object' : shared_object,
        })
        return HttpResponse(t.render(c))

    def lms_commit(self, request):
        """
        This is how the SCORM player is able to push data back to us when a commit call happens.
        """
        try:
            if request.method != 'POST' or 'auth_token' not in request.POST or 'flashSO' not in request.POST or \
                    'sco_session_id' not in request.POST:
                return HttpResponseBadRequest('Your request must include strings labeled "auth_token", "sco_session_id" and "flashSO".')
            auth_token = Utils.get_auth_token_object(request.POST['auth_token'])
            the_sco_session = Utils.find_by_id(request.POST['sco_session_id'], facade.models.ScoSession)
            the_sco_session.shared_object = request.POST['flashSO']
            shared_object_assignments = the_sco_session.shared_object.split(';')
            # Here we are going to look at the shared object and try to split it out and store it into individual fields in our DB for
            # reporting
            for shared_object_assignment in shared_object_assignments:
                # The last split will be an empty string, so let's make sure we aren't looking at that one
                if len(shared_object_assignment) > 0:
                    try:
                        # Let's get the field name and the value to store in it split by the '=' symbol
                        field_value_pair = shared_object_assignment.split('=')
                        setattr(the_sco_session, field_value_pair[0], field_value_pair[1])
                    except:
                        # If we get an exception here, it is most certainly due to us not having a matching field in our DB, so we'd rather
                        # ignore
                        continue
            the_sco_session.save()
            redirect_url = reverse('db_post_form',
                args=[auth_token.session_id, the_sco_session.id, urllib.quote(the_sco_session.shared_object)])
            return HttpResponse('<meta http-equiv="Refresh" content="0; url=%s">'%(redirect_url))
        except exceptions.AuthTokenExpiredException:
            return HttpResponseNotFound('Your session has expired.  Please log in again!')

    def return_player(self, request, auth_token, sco_id):
        """
        Handle requests by returning the scorm player.
        """
        try:
            the_sco = facade.models.Sco.objects.get(id__exact=sco_id)
            auth_token = Utils.get_auth_token_object(auth_token)
            assignments = facade.models.Assignment.objects.filter(task__id=the_sco.id, user=auth_token.user).order_by('-effective_date_assigned')
            if len(assignments) == 0:
                return HttpResponseNotFound('There is no assignment to view this SCO')
            assignment = assignments[0]
            # Let's try to find an existing sco_session for this SCO and user.  If there isn't one,
            # let's create one.
            potential_sco_sessions = assignment.assignment_attempts.all()
            if len(potential_sco_sessions) == 0:
                the_sco_session = facade.models.ScoSession(assignment=assignment,
                    date_started=datetime.datetime.utcnow())
                the_sco_session.save()
            elif len(potential_sco_sessions) == 1:
                the_sco_session = potential_sco_sessions[0]
            else:
                raise multiple_scorm_sco_sessions_exception
            the_sco_session = the_sco_session.downcast_completely()
            # Form the URL to the HTTP form that will be used to store and POST data to us
            db_form_url = reverse('db_post_form', args=[auth_token.session_id, the_sco_session.id,
                urllib.quote(the_sco_session.shared_object)])

            t = loader.get_template('scorm_player')
            c = Context({
                'user' : auth_token.user,
                'sco_url' : settings.SECURE_MEDIA_URL + the_sco_session.sco.url,
                'auth_token' : auth_token.session_id,
                'db_form_url' : db_form_url,
                'api_adapter_url' : settings.SECURE_MEDIA_URL + 'scorm_player/API_ADAPTER.htm',
                'cmi_db_url' : settings.SECURE_MEDIA_URL + 'scorm_player/CMIDB.html',
            })
            return HttpResponse(t.render(c))
        except facade.models.Sco.DoesNotExist, e:
            return HttpResponseNotFound('The requested Sco does not exist.')
        except exceptions.NotLoggedInException, e:
            return HttpResponseNotFound('The auth_token is invalid.')

# vim:tabstop=4 shiftwidth=4 expandtab
