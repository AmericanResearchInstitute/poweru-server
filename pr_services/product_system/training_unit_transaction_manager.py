"""
TrainingUnitTransaction manager class
"""

from pr_services.object_manager import ObjectManager
from pr_services.rpc.service import service_method
import facade

class TrainingUnitTransactionManager(ObjectManager):
    """
    Manage TrainingUnitTransactions in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        ObjectManager.__init__(self)

        self.getters.update({
            'training_unit_authorizations' : 'get_many_to_many',
            'training_unit_account' : 'get_foreign_key',
            'purchase_order' : 'get_foreign_key',
            'value' : 'get_general',
        })

        #: Dictionary of attribute names and the functions used to set them
        self.setters.update({
            'training_unit_account' : 'set_foreign_key',
            'purchase_order' : 'set_foreign_key',
            'training_unit_authorizations' : 'set_many',
        })  
        self.my_django_model = facade.models.TrainingUnitTransaction

    @service_method
    def create(self, auth_token, training_unit_account, value, purchase_order,
        optional_parameters=None):
        
        """
        Create a new TrainingUnitTransaction
        
        @param training_unit_account      Foreign Key for a training unit account
        @param value                      Value in cents
        @param purchase_order             Foreign Key for a purchase order
        @param optional_parameters        Dictionary of optional parameter values indexed by name.
        @return                           a reference to the newly created TrainingUnitTransaction
        """

        if optional_parameters is None:
            optional_parameters = {}

        tua = self._find_by_id(training_unit_account, facade.models.TrainingUnitAccount)
        po = self._find_by_id(purchase_order, facade.models.PurchaseOrder)
        t = self.my_django_model(value = value, training_unit_account = tua, purchase_order = po)
        t.blame = facade.managers.BlameManager().create(auth_token)
        t.save()
        if optional_parameters:
            facade.subsystems.Setter(auth_token, self, t, optional_parameters)
            t.save()
        self.authorizer.check_create_permissions(auth_token, t)
        return t

# vim:tabstop=4 shiftwidth=4 expandtab
