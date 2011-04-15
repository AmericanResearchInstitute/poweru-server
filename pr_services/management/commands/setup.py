import sys
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option
import facade

class Command(BaseCommand):
    requires_model_validation = True

    option_list = BaseCommand.option_list + (
        make_option("-p", "--password", dest="default_admin_password", default="admin",
                            type="string", metavar="PASSWORD",
                            help="'admin' account password (default=admin)"),
        make_option("-a", "--authz-only", dest="authz_only",
                    action="store_true", default=False),
        make_option("-t", "--templates-only", dest="templates_only",
                    action="store_true", default=False),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.initial_setup_machine = facade.subsystems.InitialSetupMachine()

    @transaction.commit_on_success
    def handle(self, *args, **options):
        if options.get('verbosity') not in [None, '0', '1']:
            verbose = True
        else:
            verbose = False
        try:
            self.initial_setup_machine.initial_setup(*args, **options)
            if verbose:
                print "initial_setup succeded"
        except facade.models.ModelDataValidationError, e:
            print 'Validation Error during initial_setup. Perhaps setup has already been run?'
            raise

# vim:tabstop=4 shiftwidth=4 expandtab
