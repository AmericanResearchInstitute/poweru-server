## xmlrpc_svc.py

from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from django.http import HttpResponse
from pr_services.rpc.service import ServiceManagers
import facade
import settings
import sys

if sys.version_info[:2] == (2, 4):
    dispatcher = SimpleXMLRPCDispatcher()
elif sys.version_info[:2] >= (2, 5):
    dispatcher = SimpleXMLRPCDispatcher(allow_none = True, encoding = 'utf-8')
dispatcher.register_introspection_functions()
dispatcher.register_multicall_functions()

def gateway(request):
    response = HttpResponse()
    if len(request.POST):
        response = HttpResponse(mimetype="application/xml")  # Cleaner to reinstantiate than to add seemingly useless else clause
        response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
    elif settings.DEBUG:
        response.write("<b>This is an XML-RPC Service.</b><br>")
        response.write("The following methods are available:<ul>")
        methods = dispatcher.system_listMethods()

        for method in methods:
            help =  dispatcher.system_methodHelp(method)
            response.write("<li><b>%s</b>: <pre>%s</pre>" % (method, help))
        response.write("</ul>")
    response['Content-length'] = str(len(response.content))
    return response

svc_managers = ServiceManagers(facade.managers)

# Iterate through the managers dict and register methods with the xmlrpc gateway
for m in svc_managers.exposed_managers:
    instance = svc_managers.get_manager_class(m)()
    methods = instance._get_method_list()
    for method in methods:
        dispatcher.register_function(getattr(instance, method), '%s.%s' % (m,method))

# vim:tabstop=4 shiftwidth=4 expandtab
