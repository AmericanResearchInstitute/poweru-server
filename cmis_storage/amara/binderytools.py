"""
Convenience functions for using the Amara bindery.
"""

#
# Utility functions for common binding usage
#

import re
import time
from datetime import time as dt_time
from datetime import datetime, timedelta
from Ft.Xml import InputSource
from Ft.Xml import SplitQName
from Ft.Lib import Uri
from amara import bindery, PI_BINDING
from amara import domtools, saxtools
from Ft.Xml.XPath import Conversions
from xml.dom import Node

#FIXME: Use 4Suite L10N
def _(t): return t

try:
    #From http://labix.org/python-dateutil
    from dateutil.parser import parse as dateparse
    from dateutil.tz import tzlocal
    #Make sure parsed datatimes always have some timezone info
    DEFAULT = datetime(2000, 1, 1, tzinfo=tzlocal())

    def parse_isodate(st):
        try:
            dt = dateparse(st, default=DEFAULT)
            return dt
        except ValueError:
            return None
    parse_isotime = parse_isodate
except ImportError:
    from dateutil_standins import *

#
# Bindery convenience functions
#

def setup_binder_(rules, binderobj, prefixes, validate, binding_classes):
    if binderobj is None:
        binderobj = bindery.binder(prefixes=prefixes)
    for rule in rules:
        binderobj.add_rule(rule)
    if binding_classes:
        for ns, local in binding_classes :
            class_ = binding_classes[ns, local]
            if ns == PI_BINDING:
                binderobj.set_pi_binding_class(local, class_)
            else:
                binderobj.set_binding_class(ns, local, class_)
    return binderobj


def bind_uri(uri, rules=None, binderobj=None, prefixes=None, validate=False,
             binding_classes=None):
    """
    Create a binding from XML retrieved from a URI
    rules - a list of bindery rule objects to fine-tune the binding
    binderobj - optional binder object to control binding details,
                the default is None, in which case a binder object
                will be created
    prefixes - dictionary mapping prefixes to namespace URIs
               the default is None
    validate - True to request DTD validaton by the underlying parser
                default is False
    """
    rules = rules or []
    #Create an input source for the XML
    isrc_factory = InputSource.DefaultFactory
    isrc = isrc_factory.fromUri(uri)
    binderobj = setup_binder_(rules, binderobj, prefixes, validate, binding_classes)

    #Now bind from the XML given in the input source
    binding = binderobj.read_xml(isrc, validate)
    return binding


def bind_file(fname, rules=None, binderobj=None, prefixes=None, validate=False,
              binding_classes=None):
    """
    Create a binding from XML read from a file
    rules - a list of bindery rule objects to fine-tune the binding
    binderobj - optional binder object to control binding details,
                the default is None, in which case a binder object
                will be created
    prefixes - dictionary mapping prefixes to namespace URIs
               the default is None
    validate - True to request DTD validaton by the underlying parser
               default is False
    """
    #Create an input source for the XML
    isrc_factory = InputSource.DefaultFactory
    #Create a URI from a filename the right way
    file_uri = Uri.OsPathToUri(fname, attemptAbsolute=1)
    binding = bind_uri(file_uri, rules=rules, binderobj=binderobj,
                       prefixes=prefixes, validate=validate,
                       binding_classes=binding_classes)
    return binding

DEFAULT_URI = 'urn:bogus:unknown-resource-uri'

def bind_stream(stream, uri=None, rules=None, binderobj=None, prefixes=None,
                validate=False, binding_classes=None):
    """
    Create a binding from XML retrieved from a file-like object
    rules - a list of bindery rule objects to fine-tune the binding
    binderobj - optional binder object to control binding details,
                the default is None, in which case a binder object
                will be created
    prefixes - dictionary mapping prefixes to namespace URIs
               the default is None
    validate - True to request DTD validaton by the underlying parser
               default is False
    """
    rules = rules or []
    #Create an input source for the XML
    isrc_factory = InputSource.DefaultFactory
    isrc = isrc_factory.fromStream(stream, uri or DEFAULT_URI)

    binderobj = setup_binder_(rules, binderobj, prefixes, validate, binding_classes)

    #Now bind from the XML given in the input source
    binding = binderobj.read_xml(isrc, validate)
    return binding

def bind_string(st, uri=None, rules=None, binderobj=None, prefixes=None, validate=False, binding_classes=None):
    """
    Create a binding from XML in string (NOT unicode) form
    rules - a list of bindery rule objects to fine-tune the binding
    binderobj - optional binder object to control binding details,
                the default is None, in which case a binder object
                will be created
    prefixes - dictionary mapping prefixes to namespace URIs
               the default is None
    validate - True to request DTD validaton by the underlying parser
               default is False
    """
    import cStringIO
    stream = cStringIO.StringIO(st)
    binding = bind_stream(stream, uri=uri, rules=rules, binderobj=binderobj,
                       prefixes=prefixes, validate=validate, binding_classes=binding_classes)
    return binding


def create_document(qname=None, ns=None, content=None, attributes=None,
                    pubid=None, sysid=None, prefixes=None):
    """
    Create a document, with optional convenience arguments to create
    top-level information items
    qname - optional QName of the document element (which will be created)
            if QName is not given, no other arguments may be given
    ns - optional namespace of the document element
    content - optional Unicode that makes up text content to be set
              as the child of the document element
    pubid - optional public ID of the doctype (to be set on the document)
    sysid - optional system ID of the doctype (to be set on the document)
    prefixes - optional set of additional, preferred prefix/namespace mappings
               for the document to track
    """
    if not qname:
        doc = bindery.root_base()
        return doc
    doc = bindery.root_base(doctype_name=qname, pubid=pubid, sysid=sysid)
    prefix, local = SplitQName(qname)
    prefixes = prefixes or {}
    prefixes.update(ns and {prefix: ns} or {})
    doc.xmlns_prefixes = prefixes
    doc_elem = doc.xml_create_element(qname, ns, attributes=attributes)
    doc.xml_append(doc_elem)
    if content:
        doc_elem.xml_append(content)
    return doc


#
#Optional bindery rules
#

class xpattern_rule_base(object):
    def __init__(self, xpatterns):
        if isinstance(xpatterns, str) or isinstance(xpatterns, unicode) :
            xpatterns = [xpatterns]
        self.xpatterns = xpatterns
        return

    def add_rule_hook(self, binder):
        binder.xpatterns.extend(self.xpatterns)
        return

    def match(self, binder):
        #print binder.event
        #print (binder.state_machine.entering_xpatterns, self.xpatterns)
        for xp in binder.state_machine.entering_xpatterns:
            if xp in self.xpatterns: return True
        return False
    
    def dom_match(self, node, binder):
        #Currently not used
        plist = PatternList(self.xpatterns, binder.prefixes)
        #not not trick acts like a cast to boolean
        context = Context(node.ownerDocument,
                          processorNss=binder.prefixes)
        return not not plist.lookup(node, context)


class simple_string_element_rule(xpattern_rule_base):
    """
    An Amara bindery rule.  Bindery rules allow developers to customize how
    XML documents are translated to Python objects.
    
    This rule is pattern based.  Elements that match the pattern will
    be bound as simple Python unicode objects, rather than full
    element objects, saving memory.
    
    There is no default pattern.  You must specify one.
    """
    event_type = saxtools.START_ELEMENT
    priority = -30

    def apply(self, binder):
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return
        if not self.match(binder):
            return
        #Manage a stack of elements that match this start, so that we know
        #When we've really met our matching end element
        #Set it to 1 because we want it to roll to 0 when we meed the matching end element
        self.stack_depth = 1
        
        parent = binder.binding_stack[-1]
        if not parent: return

        (dummy, qname, ns, local, attributes) = binder.event
        prefix = qname[:qname.rindex(local)][:-1]
        ename = binder.naming_rule.xml_to_python(qname, ns)

        #Inset a trigger for handling child characters
        def handle_char(binder):
            if binder.event_completely_handled:
                return
            (dummy, text) = binder.event
            #Append current char data to any already added
            cdata = getattr(parent, ename, u'') + text
            setattr(parent, ename, cdata)
            binder.event_completely_handled = True
            return
        handle_char.priority = -31
        binder.add_rule(handle_char, saxtools.CHARACTER_DATA)

        #Inset a trigger for handling child start elements
        def handle_start(binder):
            #Skip child elements
            binder.event_completely_handled = True
            return
        handle_start.priority = -31
        binder.add_rule(handle_start, saxtools.START_ELEMENT)

        #Inset a trigger for handling the matching end element
        def handle_end(binder):
            (dummy, qname, ns, local) = binder.event
            self.stack_depth -= 1
            if not self.stack_depth:
                binder.remove_rule(handle_end, saxtools.END_ELEMENT)
                binder.remove_rule(handle_char, saxtools.CHARACTER_DATA)
                binder.remove_rule(handle_start, saxtools.START_ELEMENT)
            binder.event_completely_handled = True
            return
        handle_end.priority = -31
        binder.add_rule(handle_end, saxtools.END_ELEMENT)
        binder.event_completely_handled = True
        return


class omit_element_rule(xpattern_rule_base):
    """
    An Amara bindery rule.  Bindery rules allow developers to customize how
    XML documents are translated to Python objects.
    
    This rule is pattern based.  Elements that match the pattern will
    be ignored and not bound to any object at all, saving memory.
    
    There is no default pattern.  You must specify one.
    """
    event_type = saxtools.START_ELEMENT
    priority = -40

    def apply(self, binder):
        if not self.match(binder):
            return
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return

        #Manage a stack of elements that match this start, so that we know
        #When we've really met our matching end element
        #Set it to 1 because we want it to roll to 0 when we meed the matching end element
        self.stack_depth = 1
        
        #Inset a trigger for handling child characters
        def handle_char(binder):
            #Skip child characters
            binder.event_completely_handled = True
            return
        handle_char.priority = -41
        binder.add_rule(handle_char, saxtools.CHARACTER_DATA)

        #Inset a trigger for handling child start elements
        def handle_start(binder):
            self.stack_depth += 1
            binder.event_completely_handled = True
            return
        handle_start.priority = -41
        binder.add_rule(handle_start, saxtools.START_ELEMENT)

        #Inset a trigger for handling the matching end element
        def handle_end(binder):
            self.stack_depth -= 1
            if not self.stack_depth:
                binder.remove_rule(handle_end, saxtools.END_ELEMENT)
                binder.remove_rule(handle_char, saxtools.CHARACTER_DATA)
                binder.remove_rule(handle_start, saxtools.START_ELEMENT)
            binder.event_completely_handled = True
            return
        handle_end.priority = -41
        binder.add_rule(handle_end, saxtools.END_ELEMENT)
        binder.event_completely_handled = True
        return

NODETYPE_LOOKUP = {Node.COMMENT_NODE: saxtools.COMMENT,
                   Node.PROCESSING_INSTRUCTION_NODE: saxtools.PI,
                   Node.TEXT_NODE: saxtools.CHARACTER_DATA}

class omit_nodetype_rule(object):
    """
    An Amara bindery rule.  Bindery rules allow developers to customize how
    XML documents are translated to Python objects.
    
    This rule allows you to omit all comments, or all processing instructions,
    or all text nodes from the binding, for convenience or memory savings.
    """
    priority = -40
    def __init__(self, nodetype):
        self.nodetypes = nodetype
        self.event_type = NODETYPE_LOOKUP[nodetype]
        return

    def match(self, binder):
        return True
    
    def apply(self, binder):
        if not self.match(binder):
            return
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return

        binder.event_completely_handled = True
        return


class element_skeleton_rule(xpattern_rule_base):
    """
    An Amara bindery rule.  Bindery rules allow developers to customize how
    XML documents are translated to Python objects.
    
    This rule is pattern based.  Elements that match the pattern and their
    children  will be bound as elements only, with no child character data
    preserved.  Use this when you only care about the element structure and
    want to save resources by not loading the character data.
    
    The default pattern is '*', meaning all elements.
    """
    event_type = saxtools.START_ELEMENT
    priority = 20

    def __init__(self, xpatterns=None):
        if not xpatterns:
            xpatterns = [u'*']
        xpattern_rule_base.__init__(self, xpatterns)
        #Track how deep we are within a matched element event
        #0 means not within a matched element event
        self.stack_depth = 0
        return
    
    def apply(self, binder):
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return
        if not self.match(binder):
            return
        #Manage a stack of elements that match this start, so that we know
        #When we've really met our matching end element
        #Set it to 1 because we want it to roll to 0 when we meed the matching end element
        self.stack_depth = 1
        
        (dummy, qname, ns, local, attributes) = binder.event
        prefix = qname[:qname.rindex(local)][:-1]
        ename = binder.naming_rule.xml_to_python(qname, ns)

        #Inset a trigger for handling child characters
        def handle_char(binder):
            binder.event_completely_handled = True
            return
        handle_char.priority = -50
        binder.add_rule(handle_char, saxtools.CHARACTER_DATA)

        #Inset a trigger for handling child start elements
        def handle_start(binder):
            binder.event_completely_handled = False
            self.stack_depth += 1
            return
        handle_start.priority = 20
        binder.add_rule(handle_start, saxtools.START_ELEMENT)

        #Inset a trigger for handling the matching end eleemnt
        def handle_end(binder):
            self.stack_depth -= 1
            if self.stack_depth == 0:
                #Back to original matching end element
                binder.remove_rule(handle_char, saxtools.CHARACTER_DATA)
                binder.remove_rule(handle_end, saxtools.END_ELEMENT)
                binder.remove_rule(handle_start, saxtools.START_ELEMENT)
                binder.event_completely_handled = False
                return
            return
        handle_end.priority = 20
        binder.add_rule(handle_end, saxtools.END_ELEMENT)
        binder.event_completely_handled = True
        return


class ws_strip_element_rule(xpattern_rule_base, bindery.default_element_rule):
    """
    An Amara bindery rule.  Bindery rules allow developers to customize how
    XML documents are translated to Python objects.
    
    This rule is pattern based.  Elements that match the pattern and
    descendants will have text children stripped if they are pure whitespace.
    In other words
    <a> <b/> <c/> </a>
    will end up with the same binding as
    <a> <b/> <c/> </a>
    but not
    <a> <b/> x <c/> </a> <!-- ' x ' is not pure whitespace -->
    Stripping whitespace saves memory and can simplify resulting bindings,
    but be sure the whitespace doesn't have a significant meeaning in the
    document.
    
    The default pattern is '*', meaning all elements.
    """
    event_type = saxtools.START_ELEMENT
    priority = -20
    
    def __init__(self, xpatterns=None):
        if not xpatterns:
            xpatterns = [u'*']
        xpattern_rule_base.__init__(self, xpatterns)
        return

    def apply(self, binder):
        if not self.match(binder):
            return
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return
        self.stack_depth = 1
        
        #Inset a trigger for handling child characters
        def handle_char(binder):
            if binder.event_completely_handled:
                return
            parent = binder.binding_stack[-1]
            if not parent: return
            (dummy, text) = binder.event
            if text.strip():
                parent.xml_children.append(text)
            binder.event_completely_handled = True
            return
        handle_char.priority = -21
        binder.add_rule(handle_char, saxtools.CHARACTER_DATA)

        #Inset a trigger for handling child start elements
        def handle_start(binder):
            self.stack_depth += 1
            if binder.event_completely_handled:
                return
            parent = binder.binding_stack[-1]
            if not parent: return
            (dummy, qname, ns, local, attributes) = binder.event
            prefix = qname[:qname.rindex(local)][:-1]
            ename = binder.naming_rule.xml_to_python(local, ns, prefix)

            instance = bindery.create_element(binder.naming_rule, qname, ns, ename)
            bindery.bind_attributes(instance, parent, ename, binder)
            instance = bindery.bind_instance(instance, parent)
            binder.binding_stack.append(instance)
            binder.event_completely_handled = True
            return
        handle_start.priority = -21
        binder.add_rule(handle_start, saxtools.START_ELEMENT)

        #Inset a trigger for handling the matching end eleemnt
        def handle_end(binder):
            self.stack_depth -= 1
            if not self.stack_depth:
                binder.remove_rule(handle_end, saxtools.END_ELEMENT)
                binder.remove_rule(handle_char, saxtools.CHARACTER_DATA)
                binder.remove_rule(handle_start, saxtools.START_ELEMENT)
            if not binder.event_completely_handled:
                #if binder.binding_stack[-1] is instance:
                binder.binding_stack.pop()
            binder.event_completely_handled = True
            return
        handle_end.priority = -21
        binder.add_rule(handle_end, saxtools.END_ELEMENT)

        handle_start(binder)

        return


def infer_data_from_string(value):
    if not isinstance(value, basestring):
        return value
    data_value = None
    try:
        data_value = int(value)
    except (TypeError, ValueError):
        try:
            data_value = float(value)
        except (TypeError, ValueError):
            data_value = parse_isodate(value)
            if not data_value:
                data_value = parse_isotime(value)
    return data_value


class type_inference(xpattern_rule_base):
    """
    An Amara bindery rule.  Bindery rules allow developers to customize how
    XML documents are translated to Python objects.
    
    This rule is pattern based.  Children of elements that match
    the pattern are checked to see if they could be a more specialized
    type, such as int, float or date
    
    The default pattern is '*', meaning all elements.
    """
    event_type = saxtools.START_ELEMENT
    priority = 30

    def __init__(self, xpatterns=None):
        if not xpatterns:
            xpatterns = [u'*']
        xpattern_rule_base.__init__(self, xpatterns)
        return
    
    def apply(self, binder):
        if not self.match(binder):
            return
        self.stack_depth = 1

        #Inset a trigger for handling contained matching elements
        def handle_start(binder):
            self.stack_depth += 1
            (dummy, qname, ns, local, attributes) = binder.event
            #Assume a previous rule handler has added
            #The current instance to the stack
            instance = binder.binding_stack[-1]
            #key_list = [ binder.naming_rule.xml_to_python() for qn in attributes.getQNames() ]
            if hasattr(instance, "xml_attributes"):
                for attr, (qname, ns) in instance.xml_attributes.items():
                    value = getattr(instance, attr)
                    data_value = infer_data_from_string(value)
                    if data_value is not None:
                        setattr(instance, attr, data_value)
            #print "start", self.stack_depth, binder.event[2:4], instance.__class__, binder.binding_stack, instance.xml_attributes
            binder.event_completely_handled = True
            return
        #Rule must be added to the end, after the default (which does the usual
        #element handling)
        handle_start.priority = 30
        binder.add_rule(handle_start, saxtools.START_ELEMENT)
        #binder.rules[saxtools.START_ELEMENT].append(handle_start)
        #print binder.rules
        #Even though we've added it to the rules list, it won't be immediately executed
        handle_start(binder)

        #Inset a trigger for handling the matching end eleemnt
        def handle_end(binder):
            self.stack_depth -= 1
            if not self.stack_depth:
                binder.remove_rule(handle_start, saxtools.START_ELEMENT)
                binder.remove_rule(handle_end, saxtools.END_ELEMENT)
            (dummy, qname, ns, local) = binder.event
            prefix = qname[:qname.rindex(local)][:-1]
            ename = binder.naming_rule.xml_to_python(qname, ns)

            #print "end", self.stack_depth, binder.event[2:4], binder.rules[saxtools.END_ELEMENT]
            instance = binder.binding_stack[-1]
            #Only infer a type for an element if it has all text node children
            #And no attributes
            if ( not hasattr(instance, "xml_attributes") and
                 not [ child for child in instance.xml_children
                             if not isinstance(child, unicode) ] ):
                #No child elements
                value = u"".join(instance.xml_children)
                data_value = infer_data_from_string(value)
                if data_value is None:
                    data_value = value
                parent = instance.xml_parent
                if len(list(getattr(parent, ename))) == 1:
                    parent.__dict__[ename] = data_value
                    i = parent.xml_children.index(instance)
                    parent.xml_children[i] = data_value
                binder.binding_stack.pop()
                binder.event_completely_handled = True
            return
        handle_end.priority = -60
        binder.add_rule(handle_end, saxtools.END_ELEMENT)
        binder.event_completely_handled = True
        return


#General utility functions for bindery

def fixup_namespaces(node):
    """
    reduces namespace clutter in documents by looking for duplicate namespace
    declarations and preferring those set as document prefixes
    """
    doc = node.rootNode
    nss = dict(zip(doc.xmlns_prefixes.values(), doc.xmlns_prefixes.keys()))
    #FIXME: handle attributes as well
    if node.namespaceURI in nss:
        node.xmlnsPrefix = nss[node.namespaceURI]
        node.nodeName = node.prefix and node.prefix + ':' + node.localName or node.localName
    for child in node.xml_child_elements.value(): fixup_namespaces(child)
    return


def quick_xml_scan(source, field, filter=None, display=None, **kwargs):
    """
    Scan through an XML file to extract the first occurrence of single field,
    without loading more of the file than needed to find the data
    field - a Uncode object representing an XSLT pattern
    filter - an optional XPath expression for filtering results from the pattern
    display - an optional XPath expression indicating what value to display, with the matching node from the pattern as the context
    """
    #A n elaboration of
    # http://copia.ogbuji.net/blog/2006-01-08/Recipe__fa
    nodes = pushbind(source, field, **kwargs)
    for node in nodes:
        if not xpath or node.xml_xpath(filter):
            if display:
                #Print specified subset
                result = Conversions.StringValue(node.xml_xpath(display))
            else:
                result = Conversions.StringValue(node)
    return result


#
# Pushbind
#

import os
import xml.sax
from Ft.Xml import Sax
from amara.saxtools import sax2dom_chunker
from Ft.Xml import InputSource
from Ft.Lib import Uri, Uuid
from Ft.Xml.Lib.XmlString import IsXml
from Ft.Xml.XPath import Context, Compile


def pushbind(source, xpatterns, prefixes=None, rules=None, event_hook=None, validate=False):
    """
    Generator that yields subtrees of Python object bindings from XML
    according to the given pattern.  The patterns are must be XSLT patterns
    matching elements.
    
    Example: for an xml document
    
    XML = '<a> <b><c/></b> <b><c/></b> <b><c/></b> </a>'
    
    pushbind('b', string=XML)
    Will return a generator that yields the first, second and third b
    element in turn as Python objects containing the full subtree.
    
    Warning: this function uses threads and only works in Python distros
    with threading support.

    lookahead - how far ahead the SAX engine looks for events before waiting
    for the user to request another subtree from the generator.  0 means
    the SAX engine will just load and queue up object for
    the entire file in the background.
    """
    parser = Sax.CreateParser()
    parser.setFeature(Sax.FEATURE_GENERATOR, True)

    if validate:
        parser.setFeature(xml.sax.handler.feature_validation, True)
    else:
        parser.setFeature(xml.sax.handler.feature_external_pes, False)

    def handle_chunk(node):
        parser.setProperty(Sax.PROPERTY_YIELD_RESULT, node)

    #Create an instance of the chunker
    handler = saxbind_chunker(xpatterns=xpatterns, prefixes=prefixes,
        chunk_consumer=handle_chunk, rules=rules, event_hook=event_hook
    )

    parser.setContentHandler(handler)
    if isinstance(source, InputSource.InputSource):
        pass
    elif hasattr(source, 'read'):
        #Create dummy Uri to use as base
        dummy_uri = 'urn:uuid:'+Uuid.UuidAsString(Uuid.GenerateUuid())
        source = InputSource.DefaultFactory.fromStream(source, dummy_uri)
    elif IsXml(source):
        #Create dummy Uri to use as base
        dummy_uri = 'urn:uuid:'+Uuid.UuidAsString(Uuid.GenerateUuid())
        source = InputSource.DefaultFactory.fromString(source, dummy_uri)
    elif Uri.IsAbsolute(source): #or not os.path.isfile(source):
        source = InputSource.DefaultFactory.fromUri(source)
    else:
        source = InputSource.DefaultFactory.fromUri(Uri.OsPathToUri(source))
    return parser.parse(source)


from amara.binderyxpath import xpath_attr_wrapper
class dummy_element(object):
    nodeType = Node.ELEMENT_NODE
    def __init__(self, name, attribs, root):
        self._root = root
        self.xpathAttributes = [
            xpath_attr_wrapper(
                attribs.getQNameByName((ns, local)), ns, value, self
                )
            for (ns, local), value in attribs.items()
            ]
        #self.attributes = dict([
        #    (1, attr) for attr in self.xpathAttributes
        #    ])
    
    def _rootNode(self):
        return self._root


class saxbind_chunker(bindery.binder, saxtools.sax2dom_chunker):
    """
    Note: Ignores nodes prior to the document element, such as PIs and
    text nodes.  Collapses CDATA sections into plain text
    Only designed to work if you set the feature
      sax.handler.feature_namespaces
    to 1 on the parser you use.

    xpatterns - list of XSLT Patterns.  Only portions of the
        tree within these patterns will be instantiated as DOM (as
        chunks fed to chunk_consumer in sequence)
        If None (the default, a DOM node will be created representing
        the entire tree.

    prefixes - a dictionary of prefix -> namespace name mappings used to
        interpret XPatterns
    
    chunk_consumer - a callable object taking an XML root object.  It will be
        invoked as each chunk is prepared.
    """
    def __init__(self,
                 xpatterns=None,
                 prefixes=None,
                 chunk_consumer=None,
                 rules=None,
                 event_hook=None,
                 ):
        bindery.binder.__init__(self, prefixes)
        #Add patterns from the push match specs
        if isinstance(xpatterns, str) or isinstance(xpatterns, unicode):
            xpatterns = [xpatterns]
        self.xpatterns.extend(xpatterns)
        rules = rules or []
        for rule in rules:
            self.add_rule(rule)
        prefixes = prefixes or {}
        #print self.xpatterns
        self.state_machine = saxtools.xpattern_state_manager(self.xpatterns, prefixes)
        self._chunk_consumer = chunk_consumer
        self.event_hook = event_hook
        return

    #Overridden ContentHandler methods
    def startDocument(self):
        bindery.binder.startDocument(self)
        if self.event_hook:
            try:
                self.event_hook.startDocument()
            except AttributeError:
                pass
        return

    def endDocument(self):
        bindery.binder.endDocument(self)
        if self.event_hook:
            try:
                self.event_hook.endDocument()
            except AttributeError:
                pass
        return

    def startElementNS(self, (ns, local), qname, attribs):
        #print "startElementNS", (self, (ns, local), qname, attribs)
        self.state_machine.event(1, ns, local)
        if not self.state_machine.status():
            if self.event_hook:
                try:
                    self.event_hook.startElementNS((ns, local), qname, attribs)
                except AttributeError:
                    pass
            for attrtest in self.state_machine.attribute_tests:
                root = self.binding_stack[0]
                e = dummy_element(qname, attribs, root)
                matched = attrtest.evaluate(Context.Context(e))
                if matched:
                    #Feed the consumer
                    attr = matched[0]
                    root.xmlns_prefixes = self.prefixes
                    root.xml_append(dummy_element)
                    self._chunk_consumer(attr)
                    #Start over with new doc frag so old memory can be reclaimed
                    self.binding_stack = []
                    self.event = (saxtools.START_DOCUMENT,)
                    self.apply_rules()
            return
        self.event = (saxtools.START_ELEMENT, qname, ns, local, attribs)
        self.apply_rules()
        return

    def endElementNS(self, (ns, local), qname):
        self.state_machine.event(0, ns, local)
        if not self.state_machine.status():
            #print (self.state_machine._state, self.state_machine.entering_xpatterns, self.state_machine.leaving_xpatterns)
            if (self._chunk_consumer and
                self.state_machine.leaving_xpatterns):
                self.event = (saxtools.END_ELEMENT, qname, ns, local)
                self.apply_rules()
                self.event = (saxtools.END_DOCUMENT,)
                self.apply_rules()
                root = self.binding_stack[0]
                elem = root.xml_children[-1]
                del root
                elem.xmlns_prefixes = self.prefixes
                elem.xml_parent = None
                self._chunk_consumer(elem)
                #Start all over with a new container so the old
                #One's memory can be reclaimed
                self.binding_stack = []
                self.event = (saxtools.START_DOCUMENT,)
                self.apply_rules()
            else:
                if self.event_hook:
                    try:
                        self.event_hook.endElementNS((ns, local), qname)
                    except AttributeError:
                        pass
            return
        self.event = (saxtools.END_ELEMENT, qname, ns, local)
        self.apply_rules()
        return

    def characters(self, chars):
        if self.state_machine.status():
            bindery.binder.characters(self, chars)
        else:
            if self.event_hook:
                try:
                    self.event_hook.characters(chars)
                except AttributeError:
                    pass
        return


