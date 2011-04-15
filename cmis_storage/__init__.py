import os

__all__ = ('WSDL_PATH',)

this_file_path = os.path.abspath(os.path.dirname(__file__))
WSDL_PATH = os.path.join(this_file_path, 'wsdl')
