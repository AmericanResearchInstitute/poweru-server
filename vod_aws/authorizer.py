import facade
from pr_services import exceptions
from pr_services.authorizer_decorators import *

class Authorizer(facade.subsystems.Authorizer):
    def assignment_is_not_video(self, auth_token, actee):
        """Returns True iff the actee is an Assignment the Task in which is not a Video"""

        if not isinstance(actee, facade.models.Assignment):
            raise exceptions.InvalidActeeTypeException()
        task = actee.task.downcast_completely()
        if isinstance(task, facade.models.Video):
            return False
        return True

    def actor_is_manager_of_actee_related_category(self, auth_token, actee):
        """
        Returns True iff the actor is a manager of a category that the
        actee is directly or indirectly related to, and the relationship
        is not through a deleted video.
        """

        if isinstance(actee, facade.models.Assignment):
            task = actee.task.downcast_completely()
            if not isinstance(task, facade.models.Video):
                return False
            if task.deleted:
                return False
            categories = task.categories.all()
        elif isinstance(actee, facade.models.EncodedVideo):
            if actee.video.deleted:
                #should not be possible but it doesn't hurt to be paranoid
                return False
            categories = actee.video.categories.all()
        elif isinstance(actee, facade.models.Video):
            if actee.deleted:
                return False
            categories = actee.categories.all()
        elif isinstance(actee, facade.models.VideoCategory):
            if actee.video.deleted:
                return False
            categories = [actee.category]
        elif isinstance(actee, facade.models.Category):
            categories = [actee]
        elif isinstance(actee, facade.models.VideoSession):
            if actee.video.deleted:
                return False
            categories = actee.video.categories.all()
        elif isinstance(actee, facade.models.User):
            categories = set()
            for group in actee.groups.all():
                categories.update(group.categories.all())
        else:
            raise exceptions.InvalidActeeTypeException()

        for cat in categories:
            if cat.managers.filter(id=auth_token.user.id).count() > 0:
                return True
        return False

    def actor_is_member_of_actee_related_category_authorized_groups(self, auth_token, actee):
        """
        Returns true iff the actor is a member of an authorized group on a
        category that's in an approved relationship to the actee.
        """

        if isinstance(actee, facade.models.Assignment):
            task = actee.task.downcast_completely()
            if not isinstance(task, facade.models.Video):
                return  False
            approved = filter(lambda cr: cr.status == 'approved',
                task.category_relationships.all())
            categories = [cr.category for cr in approved]
        elif isinstance(actee, facade.models.EncodedVideo):
            approved = filter(lambda cr: cr.status == 'approved',
                actee.video.category_relationships.all())
            categories = [cr.category for cr in approved]
        elif isinstance(actee, facade.models.Video):
            approved = filter(lambda cr: cr.status == 'approved',
                actee.category_relationships.all())
            categories = [cr.category for cr in approved]
        elif isinstance(actee, facade.models.Category):
            categories = [actee]
        else:
            raise exceptions.InvalidActeeTypeException()

        cat_groups = set()
        for cat in categories:
            cat_groups.update(cat.authorized_groups.values_list('id', flat=True))
        user_groups = set(auth_token.user.groups.values_list('id', flat=True))
        if len(cat_groups & user_groups):
            return True
        return False

    @does_not_use_actee
    def actor_is_member_of_any_organization(self, auth_token, actee):
        """
        Returns true iff the actor is a member of any Organization
        """

        if auth_token.user.organizations.count() > 0:
            return True
        return False
