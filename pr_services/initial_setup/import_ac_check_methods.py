from __future__ import with_statement
import codecs
import os.path
from decorators import authz

@authz
def setup(machine):
    filename = os.path.join(os.path.dirname(__file__), 'ac_check_methods.xml')
    with codecs.open(filename, encoding = 'utf-8') as f:
        machine.import_manager._import_ac_check_methods(f.read())
