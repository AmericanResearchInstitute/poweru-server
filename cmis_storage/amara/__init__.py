#Module amara

#all = ["parse", "parse_path", "pushbind", "pushdom", "__version__"]

RESERVED_URI = 'http://uche.ogbuji.net/tech/4suite/amara/reserved/'
PI_BINDING = RESERVED_URI + 'pi-binding'


import os

import binderytools
import domtools

create_document = binderytools.create_document
pushbind = binderytools.pushbind
pushdom = domtools.pushdom


# Convenience functions for parsing

def parse(source, uri=None, rules=None, binderobj=None, prefixes=None, validate=False, binding_classes=None):
    """
    Convenience function for parsing XML.  Use this function with a single
    argument, which is a string (not Unicode object), file-like object
    (stream), file path or URI.
    Returns a document binding object.

    Only use this function to parse self-contained  XML (i.e. not requiring
    access to any other resource).  For example, do not use it for XML with
    external entities.  If you get URI resolution errors, pass in a URI
    parameter.

    uri - establish a base URI for the XML document entity being parsed,
          required if source is a string or stream containing XML that
          uses any external resources.  If source is a path or URI, then
          this parameter, if given, is ignored
    rules - a list of bindery rule objects to fine-tune the binding
    binderobj - optional binder object to control binding details,
                the default is None, in which case a binder object
                will be created
    prefixes - dictionary mapping prefixes to namespace URIs
               the default is None
    validate - True to request DTD validaton by the underlying parser
               the default is False
    """
    from Ft.Xml import InputSource
    from Ft.Lib import Uri, Uuid
    from Ft.Xml.Lib.XmlString import IsXml
    #if isinstance(source, InputSource.InputSource):
    #    pass
    if hasattr(source, 'read'):
        return binderytools.bind_stream(
            source, uri=uri, rules=rules, binderobj=binderobj,
            prefixes=prefixes, validate=validate, binding_classes=binding_classes)
    elif IsXml(source):
        return binderytools.bind_string(
            source, uri=uri, rules=rules, binderobj=binderobj,
            prefixes=prefixes, validate=validate, binding_classes=binding_classes)
    elif Uri.IsAbsolute(source): #or not os.path.isfile(source):
        return binderytools.bind_uri(
            source, rules=rules, binderobj=binderobj,
            prefixes=prefixes, validate=validate, binding_classes=binding_classes)
    else:
        return binderytools.bind_file(
            source, rules=rules, binderobj=binderobj,
            prefixes=prefixes, validate=validate, binding_classes=binding_classes)


#Need double layer of exception checking to support freeze utils
#(In that case there would be setuptools at freeze time, but not run time)
try:
    import pkg_resources
    try:
        __version__ = pkg_resources.get_distribution('Amara').version
    except pkg_resources.DistributionNotFound:
        from __config__ import VERSION as __version__
except ImportError:
    from __config__ import VERSION as __version__


