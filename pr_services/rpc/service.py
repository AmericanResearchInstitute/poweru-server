"""
Class used as a shim for functions invoked via RPC

@author Chris Church <cchurch@americanri.com>
@author Michael Hrivnak <mhrivnak@americanri.com>
@copyright Copyright 2009 American Research Institute, Inc.
The wind almost took me away.
"""

# Python
import datetime
from inspect import getargspec, getdoc
import logging
import sys
import traceback

# Django
from django.conf import settings
import django.db.models
import django.db.transaction

# Power Reg
from pr_services import exceptions
from pr_services.utils import Utils
import facade

# Decorator module (included in current directory)
import decorator

logger = logging.getLogger('pr_services.rpc')

path = str(__file__) #: used to identify Power Reg instance in log messages

__all__ = ['service_method', 'wrap_service_method', 'RpcService',
    'create_rpc_service']

def service_method(f):
    """
    Decorator to mark a function as a service method.
    """
    f._service_method = True
    return f

@decorator.decorator
def _invoke_service_method(f, self, *args, **kwds):
    """
    Decorator for wrapping exposed RpcService methods with ShimInvoke.
    """
    method = getattr(self.action_object, f.func_name)
    return ShimInvoke(self.action_object, method)._run(*args, **kwds)

def wrap_service_method(f):
    """
    Decorator for exposing custom methods defined on an RpcService subclass.
    """
    return _invoke_service_method(service_method(f))

class RpcServiceMeta(type):
    """
    Metaclass for creating subclasses of RpcService.
    """
    
    def __new__(meta, classname, bases, class_dict):
        # First create the class itself.
        cls = type.__new__(meta, classname, bases, class_dict)
        act_cls = getattr(cls, 'action_class', object)
        # Copy action class docstring to service class.
        if not cls.__doc__ or classname == 'RpcService':
            cls.__doc__ = act_cls.__doc__
        # Find methods of the action_class that should be exposed via the
        # service class.
        for name in dir(act_cls):
            attr = getattr(act_cls, name)
            # Never expose attributes considered protected or private.
            if name.startswith('_'):
                continue
            # If attribute is not callable, it cannot possibly be a method.
            if not callable(attr):
                continue
            # If attribute has not been marked as a service method, do not
            # expose it.
            if not getattr(attr, '_service_method', False):
                continue
            # If the class has already defined an attribute with the same name,
            # and that attribute has not been marked as a service method, do
            # not replace it.
            if hasattr(cls, name):
                if not getattr(getattr(cls, name), '_service_method', False):
                    continue
            # Finally, wrap the action_class method's function so it can be
            # invoked as a service method.
            setattr(cls, name, _invoke_service_method(attr.im_func))
        return cls

class RpcService(object):
    """
    Base class for a service exposed via RPC.
    
    Create a service by inheriting from this class and setting the class
    variable action_class to any class or type.  Expose methods in the
    action_class by decorating those methods with the service_method
    decorator.  Additional methods can be defined in the service class itself
    by decorating those methods with the wrap_service_method decorator.

    >>> class MyActionObject(object):
    >>>     '''This docstring is copied to the service class.'''
    >>>
    >>>     @service_method
    >>>     def public(self, x, y=3):
    >>>         '''This docstring is copied to the service class method.'''
    >>>         return x + y
    >>>
    >>>     def private(self, a, b=2):
    >>>         '''This method is not available via the service class.'''
    >>>         return a + b
    >>>
    >>> class MyRpcService(RpcService):
    >>>     action_class = MyActionObject
    >>>
    >>>     @wrap_service_method
    >>>     def other(self, z=3):
    >>>         '''This method does not rely on the action_object.'''
    >>>         return z
    """

    # Metaclass to create methods based on action_object_class.
    __metaclass__ = RpcServiceMeta

    # Set this class variable in subclasses.
    action_class = object

    def _get_action_object(self):
        """
        Return the action object, or create it when first accessed.
        """
        # Use the protected name _action_object for backwards compatibility
        # with older service classes that create an instance in their __init__
        # method.
        if not hasattr(self, '_action_object'):
            self._action_object = self.action_class()
        return self._action_object

    action_object = property(_get_action_object)

    @classmethod
    def _get_service_methods(cls):
        """
        Return names of all methods exposed via this service class.
        """
        for name in dir(cls):
            if hasattr(getattr(cls, name), '_service_method'):
                yield name

    # For backwards compatibility with MethodIntrospection interface.
    def _get_method_list(self):
        ret = []
        for name in dir(self):
            method = getattr(self, name)
            if name.startswith('_') or not callable(method):
                continue
            ret.append(name)
        return ret

def create_rpc_service(action_class):
    """
    Factory function to create RpcService subclass from given action_class.
    """
    return type('%sSvc' % action_class.__name__, (RpcService,),
        dict(action_class=action_class))

class ServiceManagers(object):
    '''Dynamic representation of managers as RPC services

    Used by the facade to simplify autogeneration of service classes'''
    def __init__(self, managers):
        self._managers = managers

    def get_manager_class(self, manager_name):
        manager_cls = getattr(self._managers, manager_name)
        return create_rpc_service(manager_cls)

    @property
    def exposed_managers(self):
        return self._managers.import_map.keys()

class ShimInvoke:
    """
    Calls methods, catches exceptions, and returns XML struct
    """

    def __init__(self, instance, method):
        """ constructor """

        self.instance = instance
        self.method = method

    def _run(self, *parameters):
        """
        Execute a call
        
        @param parameters    All of the parameters that were passed
        
        @return               An XML struct indicating status as well
                              as a return value if the invocation was
                              successful.
        """

        start_time = datetime.datetime.utcnow()

        parameters = list(parameters)

        if (len(parameters) > 0 and getargspec(self.method)[0][1] == 'auth_token' and
            isinstance(parameters[0], basestring) and parameters[0]):

            try:
                at = Utils.get_auth_token_object(parameters[0], start_time)
                parameters[0] = at
            except exceptions.PrException, e:
                stop_time = datetime.datetime.utcnow()
                rpc_ret = {}
                rpc_ret['status'] = 'error'
                rpc_ret['error'] = [e.get_error_code(), e.get_error_msg()]
                logger.info(self.format_trace_log_message(start_time,
                    stop_time, rpc_ret, *parameters))
                return rpc_ret

        rpc_ret = {}
        try:
            ret = self._run_transaction_protected_method(self.method, *parameters)
        except exceptions.PrException, e:
            stop_time = datetime.datetime.utcnow()
            rpc_ret['status'] = 'error'
            rpc_ret['error'] = [e.get_error_code(), e.get_error_msg(), e.get_details()]
            logger.info(self.format_trace_log_message(start_time, stop_time,
                rpc_ret, *parameters))
        except facade.models.ModelDataValidationError, e:
            stop_time = datetime.datetime.utcnow()
            rpc_ret['status'] = 'error'
            pr_exception = exceptions.ValidationException(e)
            rpc_ret['error'] = [pr_exception.get_error_code(), pr_exception.get_error_msg(),
                pr_exception.get_details()]
            logger.info(self.format_trace_log_message(start_time, stop_time,
                rpc_ret, *parameters))
        except Exception, e:
            stop_time = datetime.datetime.utcnow()
            ie = exceptions.InternalErrorException(str(e))
            rpc_ret['status'] = 'error'
            rpc_ret['error'] = [ie.get_error_code(), ie.get_error_msg(), ie.get_details()]
            stack_trace = traceback.format_exc()
            log_message = u'INTERNAL ERROR: [%s] stack trace [%s]' % (
                self.format_trace_log_message(start_time, stop_time, rpc_ret, *parameters), stack_trace)
            logger.error(log_message)
        else:
            stop_time = datetime.datetime.utcnow()
            rpc_ret['status'] = 'OK'
            if ret != None:
                # If this is a Django model, return its primary key cast as a string instead
                if isinstance(ret, django.db.models.Model):
                    rpc_ret['value'] = {'id' : ret.id}
                else:
                    rpc_ret['value'] = ret
            else:
                rpc_ret['value'] = {}
            if settings.RPC_TRACE == True:
                logger.info(self.format_trace_log_message(start_time, stop_time, rpc_ret, *parameters))
        
        return rpc_ret

    def blank_out_sensitive_parameters(self, *method_parameters):
        ret = list(method_parameters)
        if isinstance(self.instance, facade.managers.UserManager):
            # hide the initial password for a create call
            if self.method.__name__ == 'create':
                ret[2] = 'xxxxxxxx'
            # hide the password for a login call
            elif self.method.__name__ == 'login':
                ret[1] = 'xxxxxxxx'
            # hide the password(s) for a change password call
            elif self.method.__name__ == 'change_password':
                ret[2] = 'xxxxxxxx'
                if len(ret) > 3 and ret[3] is not None:
                    ret[3] = 'xxxxxxxx'
            # hide the password for an obtain_auth_token_voucher call
            elif self.method.__name__ == 'obtain_auth_token_voucher':
                ret[2] = 'xxxxxxxx'
            # hide the password for a check_password_against_policy call
            elif self.method.__name__ == 'check_password_against_policy':
                ret[0] = 'xxxxxxxx'
        elif isinstance(self.instance, facade.managers.DomainManager):
            # hide the password for a change_password call
            if self.method.__name__ == 'change_password':
                ret[2] = 'xxxxxxxx'
        # hide all of the parameters for any call to the payment manager
        elif isinstance(self.instance, facade.managers.PaymentManager):
            ret = ['xxxxxxxx [all parameters hidden] xxxxxxxx'] 
        return ret

    def truncate_rpc_return_value(self, rpc_ret):
        max_rpc_return_log_length = getattr(settings, 'MAX_RPC_RETURN_LOG_LENGTH',
            None)
        if max_rpc_return_log_length is not None:
            log_rpc_ret = unicode(rpc_ret)[:max_rpc_return_log_length]
        else:
            log_rpc_ret = unicode(rpc_ret)
        return log_rpc_ret

    def format_trace_log_message(self, start_time, stop_time, rpc_ret, *method_parameters):
        return u"pr[%s]: %s [%s elapsed]: %s.%s%s = %s\n" % (unicode(path),
            unicode(stop_time),
            unicode(stop_time - start_time),
            unicode(self.method.im_class),
            unicode(self.method.__name__),
            unicode(self.blank_out_sensitive_parameters(*method_parameters)),
            unicode(self.truncate_rpc_return_value(rpc_ret)))

    @django.db.transaction.commit_on_success
    def _run_transaction_protected_method(self, method, *parameters):
        return method(*parameters)

# vim:tabstop=4 shiftwidth=4 expandtab
