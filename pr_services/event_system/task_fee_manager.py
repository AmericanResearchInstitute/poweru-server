"""
TaskFee manager class
"""

from pr_services.rpc.service import service_method
import facade

class TaskFeeManager(facade.managers.ProductManager):
    """
    Manage TaskFees in the Power Reg system
    """

    def __init__(self):
        """ constructor """

        super(TaskFeeManager, self).__init__()
        #: Dictionary of attribute names and the functions used to get them
        self.getters.update({
            'task' : 'get_foreign_key',
        })
        #: Dictionary of attribute names and the functions used to set them
        self.setters.update({
            'task' : 'set_foreign_key',
        })
        self.my_django_model = facade.models.TaskFee

    @service_method
    def create(self, auth_token, sku, name, description, price, cost,
            task, optional_attributes=None):
        """
        Create a new TaskFee

        You should probably define 'starting_quantity' in optional_attributes
        
        @param sku              SKU, up to 32 characters
        @param name             name of the Product, up to 127 characters
        @param description      description, text field
        @param price            price in cents that we charge
        @param cost             price in cents that it costs us to obtain this
        @param task             FK of a Task

        @return                 a reference to the newly created Product
        """

        if not optional_attributes:
            optional_attributes = dict()

        blame = facade.managers.BlameManager().create(auth_token)
        task_object = self._find_by_id(task, facade.models.Task)
        new_fee = self.my_django_model(sku=sku, name=name, description=description,
            task=task_object, price=price, cost=cost, blame=blame)
        if 'starting_quantity' in optional_attributes:
            new_fee.starting_quantity = optional_attributes['starting_quantity']
            del optional_attributes['starting_quantity']
        new_fee.save()

        if isinstance(optional_attributes, dict):
            facade.subsystems.Setter(auth_token, self, new_fee, optional_attributes)
            new_fee.save()
        self.authorizer.check_create_permissions(auth_token, new_fee)
        return new_fee

# vim:tabstop=4 shiftwidth=4 expandtab
