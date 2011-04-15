def authz(func):
    """
    This indicates that the marked setup method does authz setup and that it
    is idempotent with regard to any changes it makes to non-authz tables.
    """
    func.authz = True
    return func
