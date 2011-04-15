"""
TrainingVoucher manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import random
import facade

class TrainingVoucherManager(ObjectManager):
    """
    Manage TrainingVouchers in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)
        #: Dictionary of attribute names and the functions used to set them
        self.setters.update({
            'session_user_role_requirement' : 'set_foreign_key',
            'purchase_order' : 'set_foreign_key',
        }) 

        #: Dictionary of attribute names and the functions used to get them
        self.getters.update({
            'price' : 'get_session_price_from_training_voucher',
            'session_user_role_requirement' : 'get_foreign_key',
            'purchase_order' : 'get_foreign_key',
            'code' : 'get_general',
        })
        self.my_django_model = facade.models.TrainingVoucher

    @service_method
    def create(self, auth_token, surr):
        """
        Create a new TrainingVoucher
        
        @param surr                   Primary Key for a session_user_role_requirement
        @return                       A reference to the newly created TrainingVoucher
        """

        s = self._find_by_id(surr, facade.models.SessionUserRoleRequirement)
        
        # Generate a unique 10-character code
        code = ''
        banned = set(['l', '1', 'i', 'I', '5', 'S', 's', '0', 'o', 'O'])

        while True:
            while len(code) < 10:
                x = random.randint(0, 61)

                if x <= 9:
                    num = x + 48
                elif x <= 35:
                    num = x + 55
                elif x <= 61:
                    num = x + 61

                char = chr(num)
                if char not in banned:
                    code = code + char

            if self.my_django_model.objects.filter(code__exact = code).count():
                code = ''
            else:
                break

        t = self.my_django_model(session_user_role_requirement = s, code = code)
        t.blame = facade.managers.BlameManager().create(auth_token)
        t.save()
        self.authorizer.check_create_permissions(auth_token, t)
        return t

    @service_method
    def get_voucher_by_code(self, auth_token, code):
        """
        Get a training voucher by code
        
        @param code   The 10-character code associated with a voucher
        
        @return A dictionary including 'id' and 'session_user_role_requirement'
        """

        try:
            voucher = self.my_django_model.objects.get(code = code)
        except self.my_django_model.DoesNotExist:
            raise exceptions.TrainingVoucherNotFoundException()
        except self.my_django_model.MultipleObjectsReturned:
            raise exceptions.TrainingVoucherNotFoundException()
            
        if hasattr(voucher, 'purchase_order') and voucher.purchase_order:
            raise exceptions.TrainingVoucherAlreadyUsedException()
        
        self.authorizer.check_read_permissions(auth_token, voucher, ['id', 'session_user_role_requirement'])

        return {'id' : voucher.id, 'session_user_role_requirement' : voucher.session_user_role_requirement.id}

# vim:tabstop=4 shiftwidth=4 expandtab
