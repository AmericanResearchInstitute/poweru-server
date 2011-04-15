#!/usr/bin/python

#########################################################################
# Decorators
#########################################################################

def does_not_use_actee(func):
    """
    This indicates that the ac_check_method does not use the
    actee parameter.  This is good for checks that don't care
    about the actee, such as group membership checks.
    """

    func.does_not_use_actee = True 
    return func 

def uses_update_dict(func):
    """
    This indicates that the ac_check_method needs to see the update
    dictionary to inspect the new values when the auth system is
    being used for validation.  For example, only users in a
    given role may be allowed to set an attribute to a particular
    value.
    """

    func.uses_update_dict = True 
    return func 

def allow_guests(func):
    """  
    This is a method decorator that is used to set the
    method's allow_guests attribute to True.  If a method
    is for guests, it will not accept an actor as its
    first parameter, but an actee instead.
    
    @param func   The function being decorated, duh!
    """

    func.allow_guests = True 
    return func

# vim:tabstop=4 shiftwidth=4 expandtab
