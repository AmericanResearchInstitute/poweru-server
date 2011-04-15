import codecs
import getpass
from optparse import make_option
import sys
from django.db import transaction
from django.core.management.base import BaseCommand
import facade
from pr_services import exceptions

class Command(BaseCommand):
    requires_model_validation = True
    option_list = BaseCommand.option_list + (
        make_option("-m", "--model", dest="model_name",
                    type="string", metavar="MODEL_NAME",
                    help="model name (for example, 'user' or 'event')"),
        make_option("-u", "--username", dest="username",
                    type="string", metavar="USERNAME",
                    help="username to log in as"),
        make_option("-d", "--domain", dest="domain",
                    type="string", metavar="DOMAIN",
                    help="optional domain name for user to log in as"),
        make_option("-p", "--password", dest="password",
                    type="string", metavar="PASSWORD",
                    help="password to use for logging in (will be prompted for if not supplied)"),
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        )
    args = 'filename_1 [filename_2 ... filename_n]'
    help = 'Imports data from one or more CSV files.'
    
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
    
    @transaction.commit_on_success
    def handle(self, *args, **options):
        interactive = options.get('interactive')
        
        username = options.get("username")
        if username is None:
            print >> sys.stderr, "error: You must supply a username.\n"
            sys.exit(1)
            
        password = options.get('password', None)
        if password is None:
            if interactive:
                password = getpass.getpass()
            else:
                print >> sys.stderr, "error: No password supplied and --noinput specified.  Exiting."
                sys.exit(1)
        
        domain = options.get('domain')
        
        user_manager = facade.managers.UserManager() 
        
        if domain:
            ret = user_manager.login(username, password, domain)
        else:
            ret = user_manager.login(username, password)
        
        auth_token = facade.models.AuthToken.objects.get(session_id=ret['auth_token'])
        
        import_manager = facade.managers.ImportManager()
        
        model_name = options.get('model_name', None)
        if not model_name:
            print >> sys.stderr, "error: You must specify a model name."
            sys.exit(1)
        
        for filename in args:
            input_file = codecs.open(filename, 'r', encoding="utf-8")
            csv_data = facade.models.CSVData(text=input_file.read(), user=auth_token.user)
            f = getattr(import_manager, 'import_%ss' % model_name, None)
            if f and callable(f):
                try:
                    f(auth_token, csv_data, interactive=True)
                except exceptions.InvalidDataException, e:
                    if interactive:
                        print >> sys.stdout, (
                            "file [%s] ERROR: code [%d] message [%s] details [%s]" % (
                            filename, e.error_code, e.error_msg, unicode(e.details)))
                    
            else:
                print >> sys.stderr, "error: Unrecognized model name [%s]" % model_name
                sys.exit(1)
            