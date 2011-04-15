"""
VideoSessionManager class

@copyright Copyright 2009 American Research Institute, Inc.
"""

from datetime import datetime, timedelta
from pr_services.credential_system.assignment_attempt_manager import AssignmentAttemptManager
from pr_services import pr_time
from pr_services.rpc.service import service_method
from pr_services.utils import Utils
import facade

class VideoSessionManager(AssignmentAttemptManager):
    """
    Manage VideoSessions in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        super(VideoSessionManager, self).__init__()
        self.getters.update({
            'assignment' : 'get_foreign_key',
            'date_completed' : 'get_time',
            'date_started' : 'get_time',
            'user' : 'get_foreign_key',
            'video' : 'get_foreign_key',
        })
        self.setters.update({
            'date_completed' : 'set_time',
            'date_started' : 'set_time',
        })
        self.my_django_model = facade.models.VideoSession

    @service_method
    def create(self, auth_token, assignment):
        """
        Create a new VideoSession object.

        @param auth_token   The authentication token of the acting user
        @type auth_token    facade.models.AuthToken
        @param assignment   FK for an assignment
        @type assignment    int
        @return             A dictionary with two indices.  One is 'id' and is the primary key of the VideoSession object.  The other is 'urls', and is a list of URLs that the
                            user is authorized to view under this VideoSession.
        """

        assignment_object = self._find_by_id(assignment, facade.models.Assignment)
        new_video_session = self.my_django_model(assignment=assignment_object)
        new_video_session.save()
        self.authorizer.check_create_permissions(auth_token, new_video_session)
        ret = {}
        ret['id'] = new_video_session.id
        ret['urls'] = list()
        # new_video_session.video.encoded_videos.values_list('url') doesn't
        # work since the url is a property and not a DB column
        for encoded_video in new_video_session.video.encoded_videos.all():
            ret['urls'].append(encoded_video.url)
        return ret

    @service_method
    def register_video_view(self, auth_token, video_id):
        """
        Create an assignment to watch the video, if needed; then use it to
        create a VideoSession object, if needed. If a VideoSession for this
        (user, video) combination was created in the last 12 hours, does
        nothing.

        @param auth_token   The authentication token of the acting user
        @type auth_token    facade.models.AuthToken
        @param assignment   FK for a video
        @type assignment    int
        """
        # the next line is only here so that we get an exception if the
        # video_id we are given is a valid task id but the task isn't a video
        video = facade.models.Video.objects.get(id=video_id)
        assignments = facade.models.Assignment.objects.filter(
            task__id=video_id, user__id=auth_token.user.id).order_by('-id')
        if len(assignments):
            assignment = assignments[0]
        else:
            assignment = facade.managers.AssignmentManager().create(auth_token, video_id)
        start_cutoff = datetime.utcnow() - timedelta(hours=12)
        attempts = facade.models.AssignmentAttempt.objects.filter(
            assignment__id=assignment.id,
            date_started__gt=start_cutoff).order_by('-date_started')
        if len(attempts):
            attempt = attempts[0]
        else:
            attempt = self.my_django_model.objects.create(assignment=assignment)
            self.authorizer.check_create_permissions(auth_token, attempt)
        return {'id':attempt.id}

    @service_method
    def watcher_report(self, auth_token, videos, start_date=None, end_date=None):
        """
        Returns a list of views of the given videos (optinally filtered by date)
        along with some information about the viewer.
        """
        filters = {'member' : {'assignment__task__id' : videos}}
        if start_date or end_date:
            filters = [filters]
            if start_date:
                if pr_time.is_iso8601(start_date):
                    start_date = pr_time.iso8601_to_datetime(start_date)
                filters.append({'greater_than_or_equal' :
                    {'date_started' : start_date}})
            if end_date:
                if pr_time.is_iso8601(end_date):
                    end_date = pr_time.iso8601_to_datetime(end_date)
                filters.append({'less_than_or_equal' :
                    {'date_started' : end_date}})
            filters = {'and' : filters}
        views = self.get_filtered(auth_token, filters,
            ['video', 'date_started', 'user'])
        views = Utils.merge_queries(views, facade.managers.VideoManager(),
            auth_token, ['name'], 'video')
        views = Utils.merge_queries(views, facade.managers.UserManager(),
            auth_token, ['first_name', 'last_name', 'email', 'default_username_and_domain'],
            'user')
        return views

    @service_method
    def viewing_activity_report(self, auth_token, users, start_date=None, end_date=None):
        """
        Returns a list of video views by the given users (optinally filtered
        by date) along with some information about the video.
        """
        filters = {'member' : {'assignment__user__id' : users}}
        if start_date or end_date:
            filters = [filters]
            if start_date:
                if pr_time.is_iso8601(start_date):
                    start_date = pr_time.iso8601_to_datetime(start_date)
                filters.append({'greater_than_or_equal' :
                    {'date_started' : start_date}})
            if end_date:
                if pr_time.is_iso8601(end_date):
                    end_date = pr_time.iso8601_to_datetime(end_date)
                filters.append({'less_than_or_equal' :
                    {'date_started' : end_date}})
            filters = {'and' : filters}
        views = self.get_filtered(auth_token, filters,
            ['video', 'date_started', 'user'])
        views = Utils.merge_queries(views, facade.managers.VideoManager(),
            auth_token, ['name', 'author', 'description'], 'video')
        views = Utils.merge_queries(views, facade.managers.UserManager(),
            auth_token, ['first_name', 'last_name', 'email', 'username'],
            'user')
        return views

# vim:tabstop=4 shiftwidth=4 expandtab
