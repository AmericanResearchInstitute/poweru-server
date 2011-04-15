## amf_svc.py

from pr_services import exceptions
from pr_services.rpc.service import ServiceManagers
from pyamf.remoting.gateway.django import DjangoGateway
import facade

## Exposes methods to amf
class amf_svc:
    def __init__(self):
        self._svc_managers = ServiceManagers(facade.managers)

    def gateway(self):
        return DjangoGateway(self.get_methods(), expose_request = False)

    ## Get available methods for the gateway from managers dict
    def get_methods(self):
        gateway_methods = {}
        for m in self._svc_managers.exposed_managers:
            instance = self._svc_managers.get_manager_class(m)()
            methods = instance._get_method_list()
            for method in methods:
                gateway_methods[m + '.' + method] = getattr(instance, method)
        return gateway_methods

gateway = amf_svc().gateway()

# vim:tabstop=4 shiftwidth=4 expandtab
