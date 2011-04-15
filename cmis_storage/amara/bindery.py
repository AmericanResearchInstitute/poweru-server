__all__ = ['binder', 'TOP', 'ANY_NAMESPACE', 'REMOVE_RULE',
           'PY_REPLACE_PAT', 'RESERVED_NAMES']
import re
import sets
import keyword
import warnings
import cStringIO
import bisect
import xml.sax
from xml.dom import Node

from Ft.Xml import InputSource, Sax, SplitQName
from Ft.Xml import XML_NAMESPACE as XML_NS
from Ft.Xml.Domlette import NonvalidatingReader, XmlStrStrip
from Ft.Xml.Xslt import PatternList, OutputParameters, XmlWriter

from amara import domtools
from amara import saxtools
#FIXME: Set up to use actual PyXML if available
from amara.pyxml_standins import *
from amara.binderyxpath import *


ANY_NAMESPACE = 'http://uche.ogbuji.net/tech/4suite/amara/reserved/any-namespace'
TOP = -1
REMOVE_RULE = True

#FIXME: Use 4Suite L10N
def _(t): return t

g_namespaces = {}


class default_naming_rule:
    '''
    Represents naming and conversion rules for Python and XML IDs
    '''
    def __init__(self):
        self.cache = {}
        return

    def xml_to_python(self, local, ns=None, check_clashes=None):
        python_id = self.cache.get((local, ns))
        if not python_id:
            python_id = PY_REPLACE_PAT.sub('_', local)
            if python_id in RESERVED_NAMES:
                python_id = python_id + '_'
            self.cache[(local, ns)] = python_id
        if check_clashes:
            while python_id in check_clashes:
                python_id += '_'
        return python_id

    def python_to_xml(self, python_id):
        #XML NMTOKENS are a superset of Python IDs
        xml_name = python_id
        return xml_name


class namespace:
    def __init__(self, nsuri, common_prefix=None):
        self.nsuri = nsuri
        self.common_prefix = common_prefix
        self.binding_classes = {}
        return

    def __unicode__():
        return self.nsuri


class binder(LexicalHandler, object):
    def __init__(self, prefixes=None):
        self.prefixes = prefixes or {}
        self.binding = None
        self.binding_stack = []
        self.event = None
        #One list of rules for each DOM node type
        self.rules = {
            saxtools.START_ELEMENT: [(0, default_element_rule().apply)],

            saxtools.END_ELEMENT: [],
            saxtools.CHARACTER_DATA: [(0, default_text_rule().apply)],
            saxtools.PI: [(0, default_pi_rule().apply)],
            saxtools.COMMENT: [(0, default_comment_rule().apply)],
            saxtools.START_DOCUMENT: [(0, default_root_rule().apply)],
            saxtools.END_DOCUMENT: [],
            }
        
        #Preferences
        self.preserve_comments = True
        self.state_machine = None
        self.xpatterns = []
        self.naming_rule = default_naming_rule()
        self._rules_to_add = []
        self._rules_to_remove = []
        self.event_type = None
        self.first_startelement = False
        #self.unicodecache = {}
        self.pi_classes = {}
        return

    #Overridden ContentHandler methods
    def startPrefixMapping(self, prefix, uri):
        if not self.first_startelement:
            #Add prefixes discovered during parse of the top-level element
            #FIXME: What if the user does not want their manual mappings
            #Overriden by those in document?  (Probably a rare consideration)
            self.prefixes[prefix] = uri
        return

    def startDocument(self):
        if self.state_machine: self.state_machine.event(1, None, None)
        #Path components representing XPath steps to current element
        self.steps = [u'']
        self.event = (saxtools.START_DOCUMENT,)
        self.apply_rules()
        #self.binding_stack.append(self.apply_rules(saxtools.DOCUMENT_NODE))
        return

    def endDocument(self):
        if self.state_machine: self.state_machine.event(0, None, None)
        self.event = (saxtools.END_DOCUMENT,)
        self.apply_rules()
        return

    #Overridden DocumentHandler methods
    def startElementNS(self, name, qname, attribs):
        (ns, local) = name
        if self.state_machine: self.state_machine.event(1, ns, local)
        self.event = (saxtools.START_ELEMENT, qname, ns, local, attribs)
        self.apply_rules()
        if not self.first_startelement: self.first_startelement = True
        return

    def endElementNS(self, name, qname):
        (ns, local) = name
        if self.state_machine: self.state_machine.event(0, ns, local)
        self.event = (saxtools.END_ELEMENT, qname, ns, local)
        self.apply_rules()
        #self.binding_stack.pop()
        return

    def characters(self, text):
        #if len(text) < 24:
        #    text = self.unicodecache.setdefault(text, text)
        self.event = (saxtools.CHARACTER_DATA, text)
        self.apply_rules()
        return

    def processingInstruction(self, target, data):
        self.event = (saxtools.PI, target, data)
        self.apply_rules()
        return

    #Overridden LexicalHandler methods
    def comment(self, data):
        #print "COMMENT", data
        if self.preserve_comments:
            self.event = (saxtools.COMMENT, data)
            self.apply_rules()
        return

    def startDTD(self, name, public_id, system_id):
        #print "START DTD", name, public_id, system_id
        return
        
    #Bindery methods
    def _add_rule(self, event_type, priority, rule):
        if callable(rule):
            bisect.insort(self.rules[event_type], (priority, rule))
        else:
            bisect.insort(self.rules[event_type], (priority, rule.apply))
            try:
                rule.add_rule_hook(self)
            except AttributeError:
                #No hook defined
                pass
        return

    def add_rule(self, rule, event_type=None):
        """
        Add a rule for an event type.
        You can also manipulate self.rules directly, but consider details
        such as priority and add_rule hooks
        rule - the rule object.  Can be a function or an instance that
               defines an apply() function
        if you do not specify the event type, it must be set as an attribute
        on the rule
        """
        if not event_type: event_type = rule.event_type
        priority = getattr(rule, 'priority', 0)
        if event_type == self.event_type:
            self._rules_to_add.append((priority, rule))
        else:
            self._add_rule(event_type, priority, rule)
        return

    def remove_rule(self, rule_callback, event_type):
        """
        Remove a rule for a given event.  Do so smartly.
        If we're within an apply_rules, don't screw up the loop
        rule - rule callback (function or "apply" method)
        """
        priority = getattr(rule_callback, 'priority', 0)
        if event_type == self.event_type:
            self._rules_to_remove.append((priority, rule_callback))
        else:
            self.rules[event_type].remove((priority, rule_callback))
        return

    def apply_rules(self):
        self.event_completely_handled = False
        self.event_type = self.event[0]
        #List copy is wasteful, but because of the dynamics of the mutation
        #within the loop, just about inevitable
        for priority, rule_callback in self.rules[self.event_type]:
            rule_callback(self)
        for (priority, rule) in self._rules_to_add:
            self._add_rule(self.event_type, priority, rule)
        for (priority, rule) in self._rules_to_remove:
            self.rules[self.event_type].remove((priority, rule))
        self._rules_to_add = []
        self._rules_to_remove = []
        self.event_type = None
        return
        
    def set_binding_class(self, nsuri, local, class_):
        """
        Map a Python class to an element type so that each occurrence of the
        element results in an instance of the class
        """
        ns_class = g_namespaces.setdefault(nsuri, namespace(nsuri))
        ns_class.binding_classes[local] = class_
        return

    def set_pi_binding_class(self, target, class_):
        """
        Map a Python class to a processing instruction target so that each
        occurrence of a PI with that target 
        results in an instance of the class
        """
        self.pi_classes = [target] = class_
        return

    def read_xml(self, input_source, validate=False):
        if self.xpatterns:
            self.state_machine = saxtools.xpattern_state_manager(
                self.xpatterns, self.prefixes)
        parser = Sax.CreateParser()
        parser.setProperty(
            "http://xml.org/sax/properties/lexical-handler",
            self
            )
        if validate:
            parser.setFeature(xml.sax.handler.feature_validation, True)
        else:
            parser.setFeature(xml.sax.handler.feature_external_pes, False)

        parser.setContentHandler(self)
        #parser.setFeature(sax.handler.feature_namespaces, 1)
        parser.parse(input_source)
        root = self.binding_stack[0]
        if u'xml' not in self.prefixes:
            self.prefixes.update({u'xml': XML_NS})
        root.xmlns_prefixes = self.prefixes
        root.xml_namespaces = g_namespaces
        return root 


PY_REPLACE_PAT = re.compile(u'[^a-zA-Z0-9_]')

#Only need to list IDs that do not start with "xml", "XML", etc.
RESERVED_NAMES = [
    '__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__',
    '__getitem__', '__hash__', '__init__', '__iter__', '__module__',
    '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
    '__str__', '__unicode__', '__weakref__', '_childNodes', '_docIndex',
    '_localName', '_namespaceURI', '_parentNode', '_prefix', '_rootNode',
    'childNodes', 'docIndex', 
    'localName', 'namespaceURI', 'next_elem', 'nodeName', 'nodeType',
    'ownerDocument', 'parentNode', 'prefix', 'rootNode', 'locals',
    'None'
    ]

RESERVED_NAMES.extend(keyword.kwlist)

RESERVED_NAMES = sets.ImmutableSet(RESERVED_NAMES)


#Phases to which rules should be added
#Usually there should only be one MAKE_INSTANCE phase rule, and this is
#Usually the default rule
#PRE_INSTANCE rules are usually for preventing certain events from creating objects
#POST_INSTANCE rules are usually for decorating or modifying created objects
PRE_INSTANCE, MAKE_INSTANCE, POST_INSTANCE = 1, 2, 3


#All local names in this class must be prefixed with "xml" so that they
#Don't conflict with the generated class name for the element binding object
def create_element(xmlnaming_rule, xmlqname, xmlns=None, xmlename=None):
    xmlprefix, xmllocal = SplitQName(xmlqname)
    if not xmlename: xmlename = xmlnaming_rule.xml_to_python(xmllocal, xmlns)
    xmlns_class = g_namespaces.setdefault(xmlns, namespace(xmlns, xmlprefix))
    if xmlns_class.binding_classes.has_key(xmlename):
        xmlclass = xmlns_class.binding_classes[xmlename]
    else:
        exec "class %s(element_base): pass"%xmlename in globals(), locals()
        xmlclass = locals()[xmlename]
        xmlns_class.binding_classes[xmlename] = xmlclass
    if not hasattr(xmlclass, "xml_naming_rule"):
        xmlclass.xml_naming_rule = xmlnaming_rule
    xmlinstance = xmlclass()
    xmlinstance.nodeName = xmlqname
    if xmlns:
        xmlinstance.xmlnsUri = xmlns
        xmlinstance.xmlnsPrefix = xmlprefix
        xmlinstance.xmlnsLocalName = xmllocal
    return xmlinstance


def bind_attributes(instance, parent, ename, binder):
    (dummy, qname, ns, local, attributes) = binder.event
    #Handle attributes by making them simple text data members
    #if attributes and not hasattr(instance, "xml_attributes"):
    if attributes:
        instance.xml_attributes = {}
    #No, "for aname in attributes" not possible because
    #AttributesNS diesn't play by those rules :-(
    for (ans, alocal), avalue in attributes.items():
        aqname = attributes.getQNameByName((ans, alocal))
        apyname = binder.naming_rule.xml_to_python(alocal, ans,
                                             check_clashes=dir(instance))
        #setattr(instance, apyname, avalue)
        #Bypass __setattr__
        instance.__dict__[apyname] = avalue
        instance.xml_attributes[apyname] = (aqname, ans)
    return

def is_element(obj):
    #Test for element-ness.  is there a better one?
    return hasattr(obj, "localName")

def bind_instance(instance, parent, index=-1):
    """
    Takes an instance that is fully constructed, and binds it as a child of
    a given parent instance, according to a given index within the children
    list
    """
    assert instance is not parent
    instance.xml_parent = parent
    if index == -1:
        parent.xml_children.append(instance)
    else:
        parent.xml_children[index:index] = instance
    if not is_element(instance):
        return instance
    #We now know that it's an element
    #qname = instance.nodeName
    local = instance.localName
    ns = instance.namespaceURI
    ename = parent.xml_naming_rule.xml_to_python(local)
    if hasattr(parent, ename):
        obj = getattr(parent, ename)
        if not hasattr(obj, "next_elem") or ns != obj.namespaceURI:
            ename = parent.xml_naming_rule.xml_to_python(local, check_clashes=dir(parent))
            #Bypass __setattr__
            parent.__dict__[ename] = instance
        else:
            if index == 0:
                instance.__dict__['next_elem'] = obj
                #Bypass __setattr__
                parent.__dict__[ename] = instance
            else:
                prev, curr = None, obj
                while curr.next_elem is not None:
                    if curr is curr.next_elem:
                        raise BinderException(INSTANCE_ALREADY_BOUND)
                    if index != -1 and curr.xml_parent.xml_children.index(curr) >= index:
                        #We've found where instance goes relative to other
                        #elements of the same name.  Interpolate it into the
                        #linked list
                        if prev:
                            prev.__dict__['next_elem'] = instance
                        else:
                            #Precede all other siblings with the same name
                            parent.__dict__[ename] = instance
                        instance.__dict__['next_elem'] = curr
                        break
                    prev, curr = curr, curr.next_elem
                else:
                    curr.__dict__['next_elem'] = instance
                    instance.__dict__['next_elem'] = None
    else:
        #Bypass __setattr__
        parent.__dict__[ename] = instance
        instance.__dict__['next_elem'] = None
    return instance


class default_element_rule(object):
    def apply(self, binder):
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return
        parent = binder.binding_stack[TOP]
        if not parent: return
        
        (dummy, qname, ns, local, attributes) = binder.event
        prefix = qname[:qname.rindex(local)][:-1]
        ename = binder.naming_rule.xml_to_python(local, ns)
        instance = create_element(binder.naming_rule, qname, ns, ename)
        bind_attributes(instance, parent, ename, binder)
        instance = bind_instance(instance, parent)
        binder.binding_stack.append(instance)

        #Inset a trigger for handling the matching end element
        def handle_end(binder):
            if binder.event_completely_handled:
                return
            #if binder.binding_stack[-1] is instance:
            binder.binding_stack.pop()
            binder.event_completely_handled = True
            binder.remove_rule(handle_end, saxtools.END_ELEMENT)
            return
        handle_end.priority = 10
        binder.add_rule(handle_end, saxtools.END_ELEMENT)
        return


class default_root_rule(object):
    def apply(self, binder):
        instance = root_base()
        instance.xml_naming_rule = binder.naming_rule
        binder.binding_stack.append(instance)
        return


class default_pi_rule(object):
    def apply(self, binder):
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return
        parent = binder.binding_stack[TOP]
        if not parent: return
        
        (dummy, target, data) = binder.event
        class_ = binder.pi_classes.get(target, pi_base)
        instance = class_()
        instance.target = target
        instance.data = data
        instance.xml_parent = parent
        parent.xml_children.append(instance)
        return


class default_comment_rule(object):
    def apply(self, binder):
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return
        parent = binder.binding_stack[TOP]
        if not parent: return
        
        instance = comment_base()
        (dummy, data) = binder.event
        instance.data = data
        instance.xml_parent = parent
        parent.xml_children.append(instance)
        return


class default_text_rule(object):
    def apply(self, binder):
        if binder.event_completely_handled:
            #Then another rule has already created an instance
            return
        parent = binder.binding_stack[TOP]
        if not parent: return
        
        (dummy, text) = binder.event
        parent.xml_children.append(text)
        #No actual binding object mapped to this node
        return


class default_container_node(object):
    def is_attribute(self, pyname):
        #Only elements can have attributes.  element_base overrides to check
        return False

    #Mutation
    def xml_clear(self):
        "Remove all children"
        #Tempting to do
        #for c in self.xml_children: self.xml_remove_child(c)
        #But that would just be a pig
        self.xml_children = []
        delete_attrs = []
        for attr in self.__dict__:
            if not (attr in self.xml_ignore_members or attr.startswith('xml')):
                if getattr(self.__dict__[attr], 'next_elem', None):
                    delete_attrs.append(attr)
        for attr in delete_attrs:
            #Does not unlink all the way down the next_elem chain,
            #But GC should take care of them once the first is unlinked
            del self.__dict__[attr]
        return

    def xml_append(self, new):
        """
        Append element or text
        Returns the added child
        """
        if isinstance(new, unicode):
            self.xml_children.append(new)
        elif new.nodeType == Node.ELEMENT_NODE:
            bind_instance(new, self)
        elif hasattr(new, 'nodeType'):
            new.xml_parent = self
            self.xml_children.append(new)
        return new

    def xml_insert_after(self, ref, new):
        """
        Insert an object (element or text) after another child
        ref - the existing child that marks the position for insert
        new - the new child to be inserted
        Returns the added child
        """
        index = self.xml_children.index(ref)+1
        if isinstance(new, unicode):
            self.xml_children[index:index] = [new]
        elif new.nodeType == Node.ELEMENT_NODE:
            bind_instance(new, self, index)
        elif hasattr(new, 'nodeType'):
            new.xml_parent = self
            self.xml_children[index:index] = [new]
        return new

    def xml_insert_before(self, ref, new):
        """
        Insert an object (element or text) before another child
        ref - the existing child that marks the position for insert
        new - the new child to be inserted
        Returns the added child
        """
        index = self.xml_children.index(ref)
        if isinstance(new, unicode):
            self.xml_children[index:index] = [new]
        elif new.nodeType == Node.ELEMENT_NODE:
            bind_instance(new, self, index)
        elif hasattr(new, 'nodeType'):
            new.xml_parent = self
            self.xml_children[index:index] = [new]
        return new

    def xml_append_fragment(self, text, encoding=None):
        """
        Append chunk of literal XML to the children of the node instance
        text - string (not Unicode, since this is a parse operation) fragment
               of literal XML to be parsed.  This XML fragment must be
               a well-formed external parsed entity.  Basically, multiple
               root elements are allowed, but they must be properly balanced,
               special characters escaped, and doctype declaration is
               prohibited.  According to XML rules, the encoded string is
               assumed to be UTF-8 or UTF-16, but you can override this with
               an XML text declaration ('<?xml version="1.0" encoding="ENC"?>')
               or by passing in an encoding parameter to this function.
        encoding - optional string with the encoding to be used in parsing the
               XML fragment.  Default to the standard XML rules (i.e. UTF-8,
               UTF-16, or any encoding specified in text declaration).  If this
               parameter is specified, it overrrides any text declaration in
               the XML fragment.
        """
        from Ft.Xml.Domlette import EntityReader, GetAllNs, ParseFragment
        from Ft.Xml import Sax, InputSource
        #if encoding:
            #text = '<?xml version="1.0" encoding="%s"?>'%(encoding) + text
        isrc = InputSource.DefaultFactory.fromString(text, 'urn:x-amara:amara-xml-template')
        if encoding:
            isrc.encoding = encoding
        nss = self.rootNode.xmlns_prefixes
        nss.update(GetAllNs(self))
        docfrag = ParseFragment(isrc, nss)
        def walk_domlette(node, target):
            if node.nodeType == Node.ELEMENT_NODE:
                attrs = {}
                for attr in node.xpathAttributes:
                    attrs[(attr.nodeName, attr.namespaceURI)] = attr.value
                elem = target.xml_create_element(qname=node.nodeName, ns=node.namespaceURI, attributes=attrs)
                target.xml_append(elem)
                for child in node.childNodes:
                    walk_domlette(child, elem)
            elif node.nodeType == Node.TEXT_NODE:
                target.xml_append(node.data)
            else:
                for child in node.childNodes:
                    walk_domlette(child, target)
            return
        walk_domlette(docfrag, self)
        return

    def xml_create_element(self, qname, ns=None, content=None, attributes=None):
        "Create a new, empty element (no attrs)"
        instance = create_element(self.xml_naming_rule, qname, ns)
        if content:
            if not isinstance(content, list):
                content = [ content ]
            instance.xml_children = content
        if attributes:
            instance.xml_attributes = {}
            for aname in attributes:
                if isinstance(aname, tuple):
                    aqname, ans = aname
                else:
                    aqname, ans = aname, None
                avalue = attributes[aname]
                apyname = self.xml_naming_rule.xml_to_python(
                    SplitQName(aqname)[1], ans,
                    check_clashes=dir(instance))
                #Bypass __setattr__
                instance.__dict__[apyname] = avalue
                instance.xml_attributes[apyname] = (aqname, ans)
        return instance    

    def xml_remove_child(self, obj):
        """
        Remove the child equal to the given object
        obj - any object valid as a bound element child
        returns the removed child
        """
        index = self.xml_children.index(obj)
        return self.xml_remove_child_at(index)

    def xml_remove_child_at(self, index=-1):
        """
        Remove child object at a given index
        index - optional, 0-based index of child to remove (defaults to the last child)
        returns the removed child
        """
        obj = self.xml_children[index]
        if isinstance(obj, unicode):
            removed = self.xml_children[index]
            del self.xml_children[index]
        else:
            #Remove references to the object
            #Probably a slow way to go about this
            for attr, val in self.__dict__.items():
                if not (attr.startswith('xml') or attr in self.xml_ignore_members):
                    next = getattr(val, 'next_elem', None)
                    if val == obj:
                        del self.__dict__[attr]
                        if next: self.__dict__[attr] = next
                        break
                    while next:
                        prev, val = val, next
                        next = getattr(val, 'next_elem', None)
                        if val == obj:
                            prev.next_elem = next
                            break
            removed = self.xml_children[index]
            del self.xml_children[index]
        return removed

    @property
    def xml_properties(self):
        """
        Return a dictionary whose keys are Python properties on this
        object that represent XML attributes and elements, and whose vaues
        are the corresponding objects (a subset of __dict__)
        """
        properties = {}
        for attr in self.__dict__:
            if (not (attr.startswith('xml')
                or attr in self.xml_ignore_members)):
                properties[attr] = self.__dict__[attr]
        return properties

    @property
    def xml_child_elements(self):
        child_elements = {}
        for attr, val in self.xml_properties.items():
            if is_element(val):
                child_elements[attr] = val
        return child_elements

    def xml_doc(self):
        msg = []
        xml_attrs = []
        if hasattr(self, 'xml_attributes'):
            msg.append('Object references based on XML attributes:')
            for apyname in self.xml_attributes:
                local, ns = self.xml_attributes[apyname]
                if ns:
                    source_phrase = " based on '{%s}%s' in XML"%(ns, local)
                else:
                    source_phrase = " based on '%s' in XML"%(local)
                msg.append(apyname+source_phrase)
                xml_attrs.append(apyname)
        msg.append('Object references based on XML child elements:')
        for attr, val in self.__dict__.items():
            if not (attr.startswith('xml') or attr in self.xml_ignore_members):
                if attr not in xml_attrs:
                    count = len(list(getattr(self, attr)))
                    if count == 1:
                        count_phrase = " (%s element)"%count
                    else:
                        count_phrase = " (%s elements)"%count
                    local, ns = val.localName, val.namespaceURI
                    if ns:
                        source_phrase = " based on '{%s}%s' in XML"%(ns, local)
                    else:
                        source_phrase = " based on '%s' in XML"%(local)
                    msg.append(attr+count_phrase+source_phrase)
        return u'\n'.join(msg)

    def __getitem__(self, key):
        if isinstance(key, int):
            result = list(self)[key]
        else:
            force_type = None
            if isinstance(key, tuple):
                if len(key) == 3:
                    force_type, key = key[0], key[1:]
            elif isinstance(key, basestring):
                key = (None, key)
            else:
                raise TypeError('Inappropriate key (%s)'%(key))
            for attr, obj in self.xml_properties.items():
                if self.is_attribute(attr):
                    qname, ns = self.xml_attributes.get(attr)
                    if (force_type in (None, Node.ATTRIBUTE_NODE)
                        and key == (ns, SplitQName(qname)[1])):
                        #The key references an XML attribute
                        #Bypass __setattr__
                        result = obj
                        break
                elif is_element(obj):
                    if (force_type in (None, Node.ELEMENT_NODE)
                        and key == (obj.namespaceURI, obj.localName)):
                        result = obj
                        break
            else:
                raise KeyError('namespace/local name combination not found (%s)'%(str(key)))
        return result

    def __setitem__(self, key, value):
        if isinstance(key, int):
            child = self.__getitem__(key)
            child.xml_clear()
            child.xml_children = [value]
        else:
            force_type = None
            if isinstance(key, tuple):
                if len(key) == 3:
                    force_type, key = key[0], key[1:]
            elif isinstance(key, basestring):
                key = (None, key)
            else:
                raise TypeError('Inappropriate key (%s)'%(key))
            for attr, obj in self.xml_properties.items():
                if self.is_attribute(attr):
                    qname, ns = self.xml_attributes.get(attr)
                    if (force_type in (None, Node.ATTRIBUTE_NODE)
                        and key == (ns, SplitQName(qname)[1])):
                        #The key references an XML attribute
                        #Bypass __setattr__
                        self.__dict__[attr] = value
                        break
                elif is_element(obj):
                    if (force_type in (None, Node.ELEMENT_NODE)
                        and key == (obj.namespaceURI, obj.localName)):
                        obj.xml_clear()
                        obj.xml_children = [value]
                        break
            else:
                raise KeyError('namespace/local name combination not found (%s)'%(str(key)))
        return 

    def __delitem__(self, key):
        if isinstance(key, int):
            #child = self.__getitem__(key)
            #index = self.xml_parent.xml_children.index(child)
            self.xml_parent.xml_remove_child_at(key)
        else:
            force_type = None
            if isinstance(key, tuple):
                if len(key) == 3:
                    force_type, key = key[0], key[1:]
            elif isinstance(key, basestring):
                key = (None, key)
            else:
                raise TypeError('Inappropriate key (%s)'%(key))
            for attr, obj in self.xml_properties.items():
                if self.is_attribute(attr):
                    qname, ns = self.xml_attributes.get(attr)
                    if (force_type in (None, Node.ATTRIBUTE_NODE)
                        and key == (ns, SplitQName(qname)[1])):
                        #The key references an XML attribute
                        del self.xml_attributes[attr]
                        #Bypass __delattr__
                        del self.__dict__[attr]
                        break
                elif is_element(obj):
                    if (force_type in (None, Node.ELEMENT_NODE)
                        and key == (obj.namespaceURI, obj.localName)):
                        self.xml_remove_child(obj)
                        break
            else:
                raise KeyError('namespace/local name combination not found (%s)'%(str(key)))
        return 

    def xml_xslt(self, transform, params=None, output=None):
        """
        Apply an XSLT transform directly to the bindery object
        This function is quite limited, and will only handle the
        simplest transforms.  If you find your transform does not work with it,
        serialize using xml() then use Ft.Xml.Xslt.transform, which is fully
        XSLT compliant.

        output - optional file-like object to which output is written
            (incrementally, as processed)
        if stream is given, output to stream, and return value is None
        If stream is not given return value is the transform result
        as a Python string (not Unicode)
        params - optional dictionary of stylesheet parameters, the keys of
            which may be given as unicode objects if they have no namespace,
            or as (uri, localname) tuples if they do.
        """
        from Ft.Xml.Xslt import Processor, _AttachStylesheetToProcessor
        from Ft.Xml import InputSource
        from Ft.Lib import Uri, Uuid
        from Ft.Xml.Lib.XmlString import IsXml

        params = params or {}
        processor = Processor.Processor()
        _AttachStylesheetToProcessor(transform, processor)

        return processor.runNode(self, topLevelParams=params,
                                 outputStream=output)


class root_base(default_container_node, xpath_wrapper_container_mixin):
    """
    Base class for root nodes (similar to DOM documents
    and document fragments)
    """
    nodeType = Node.DOCUMENT_NODE
    xml_ignore_members = RESERVED_NAMES
    def __init__(self, naming_rule=None, doctype_name=None,
                 pubid=None, sysid=None, xmlns_prefixes=None):
        if not naming_rule: naming_rule = default_naming_rule()
        self.xml_children = []
        self.nodeName = u'#document'
        self.xml_naming_rule = naming_rule
        self.xmlns_prefixes = xmlns_prefixes or {}
        if doctype_name:
            self.xml_pubid = pubid
            self.xml_sysid = sysid
            self.xml_doctype_name = doctype_name
        return

    def xml(self, stream=None, writer=None, force_nsdecls=None, **wargs):
        """
        serialize back to XML
        if stream is given, output to stream.  Function return value is None
        You can then set the following output parameters (among others):
            encoding - output encoding: default UTF-8
            omitXmlDeclaration - u'yes' to omit the XML decl (default u'no')
            cdataSectionElements - A list of element (namespace, local-name)
                                   And all matching elements are outptu as
                                   CDATA sections
            indent - u'yes' to pretty-print the XML (default u'no')
        other output parameters are supported, based on XSLT 1.0's xsl:output
        instruction, but use fo the others is encouraged only for very advanced
        users

        You can also just pass in your own writer instance, which might
        be useful if you want to output a SAX stream or DOM nodes

        If writer is given, use it directly (encoding can be set on the writer)
        if neither a stream nor a writer is given, return the output text
        as a Python string (not Unicode) encoded as UTF-8
        
        You can force Amara to emit particular namespace declarations on the
        top-level element using the optional force_nsdecls argument.  This
        is a dictionary with unicode prefix as the key and unicode namespace URI
        as the value.  You can, for example, use the xmlns_prefixes dictionary from
        any root node.
        """
        temp_stream = None
        if not writer:
            #As a convenience, allow cdata section element defs to be simple QName
            if wargs.get('cdataSectionElements'):
                cdses = wargs['cdataSectionElements']
                cdses = [ isinstance(e, tuple) and e or (None, e)
                          for e in cdses ]
                wargs['cdataSectionElements'] = cdses
            if hasattr(self, "xml_sysid"):
                sysid, pubid = self.xml_sysid, self.xml_pubid
            else:
                sysid, pubid = None, None
            if stream:
                writer = create_writer(stream, wargs, pubid=pubid,
                                       sysid=sysid)
            else:
                temp_stream = cStringIO.StringIO()
                writer = create_writer(temp_stream, wargs,
                                       pubid=pubid,
                                       sysid=sysid)

        writer.startDocument()
        for child in self.xml_children:
            if isinstance(child, unicode):
                writer.text(child)
            else:
                child.xml(writer=writer, force_nsdecls=force_nsdecls)
        writer.endDocument()
        return temp_stream and temp_stream.getvalue()

    #Needed for Print and PrettyPrint
    #But should we support these, since we have xml(),
    #which can take a writer with indent="yes?"
    def _doctype(self):
        class doctype_wrapper(object):
            def __init__(self, name, pubid, sysid):
                self.name = name
                self.publicId = pubid
                self.systemId = sysid
                return
        if hasattr(self, "xml_sysid"):
            return doctype_wrapper(self.xml_doctype_name, self.xml_pubid,
                                   self.xml_sysid)
        else:
            return None

    doctype = property(_doctype)


class pi_base(dummy_node_wrapper):
    nodeType = Node.PROCESSING_INSTRUCTION_NODE
    def __init__(self, target=None, data=None):
        self.target = target
        self.data = data
        return

    def xml(self, stream=None, writer=None, **wargs):
        """
        If writer is None, stream cannot be None
        """
        if not writer: writer = create_writer(stream)
        writer.processingInstruction(self.target, self.data)
        return

    def __cmp__(self, other):
        return cmp(id(self), id(other))


class comment_base(dummy_node_wrapper):
    nodeType = Node.COMMENT_NODE
    def __init__(self, data=None):
        self.data = data
        return

    def xml(self, stream=None, writer=None, **wargs):
        """
        If writer is None, stream cannot be None
        """
        if not writer: writer = create_writer(stream)
        writer.comment(self.data)
        return

    def __cmp__(self, other):
        return cmp(id(self), id(other))


class element_iterator:
    def __init__(self, start):
        self.curr = start
        return

    def __iter__(self):
        return self

    def next(self):
        if not self.curr:
            raise StopIteration()
        result = self.curr
        if self.curr.next_elem is not None:
            self.curr = self.curr.next_elem
        else:
            self.curr = None
        return result


class element_base(default_container_node, xpath_wrapper_container_mixin):
    nodeType = Node.ELEMENT_NODE
    #xml_ignore_members = ['nodeName']
    xml_ignore_members = RESERVED_NAMES
    def __init__(self):
        self.xml_children = []
        self.next_elem = None
        return

    def __iter__(self):
        return element_iterator(self)

    def __len__(self):
        count = 1
        curr = self
        while curr.next_elem is not None:
            count += 1
            curr = curr.next_elem
        return count

    def __delattr__(self, key):
        if key.startswith('xml') or key in RESERVED_NAMES:
            del self.__dict__[key]
            return
        ref = getattr(self, key)
        if is_element(ref):
            self.xml_remove_child(ref)
        elif isinstance(ref, unicode):
            del self.__dict__[key]
            del self.xml_attributes[key]
        return

    def __setattr__(self, key, value):
        if key.startswith('xml') or key in RESERVED_NAMES:
            self.__dict__[key] = value
            return
        if hasattr(self, key):
            ref = getattr(self, key)
            if is_element(ref):
                ref.xml_clear()
                ref.xml_children = [value]
            #elif isinstance(ref, unicode):
            else:
                self.__dict__[key] = value
            return
        elif isinstance(value, unicode):
            self.__dict__[key] = value
            if not hasattr(self, 'xml_attributes'):
                self.xml_attributes = {}
            self.xml_attributes[key] = (key.decode('iso-8859-1'), None)
        else:
            raise ValueError('Inappropriate set attribute request: key (%s), value (%s)'%(key, value))
        return

    def xml_set_attribute(self, aname, avalue):
        "Set (or create) an attribute on ana element"
        if isinstance(aname, tuple):
            aqname, ans = aname
        else:
            aqname, ans = aname, None
        prefix, local = SplitQName(aqname)
        if prefix == u'xml':
            ans = XML_NS
        elif ans and not prefix and ans in self.rootNode.xmlns_prefixes.values():
            #If the user specified a namespace URI and not a prefix, they would
            #Usually get an ugly generated prefix.  Check the document for a nicer
            #Alternative
            #Note: this could cause spurious namespace declarations if the document is not sane
            prefix = [ p for p, u in self.rootNode.xmlns_prefixes.items() if u == ans ][0]
            aqname = prefix + u':' + local
        apyname = self.xml_naming_rule.xml_to_python(
            local, ans,
            check_clashes=dir(self))
        #Bypass __setattr__
        self.__dict__[apyname] = avalue
        if not hasattr(self, 'xml_attributes'):
            self.xml_attributes = {}
        self.xml_attributes[apyname] = (aqname, ans)
        return apyname

    #def __setattr__(self, attr, value):
        #Equivalent to creating a bound attribute
    #    self.__dict__[attr] = value
    #    return

    #def count(self):
    #    return len(list(self))

    def is_attribute(self, pyname):
         #Test a Python property (specified by name) to see whether it comes
         #from and XML attribute
         return (hasattr(self, 'xml_attributes') and self.xml_attributes.has_key(pyname))

    @property
    def xml_index_on_parent(self):
        try:
            index = self.xml_parent.xml_children.index(self)
        except ValueError: #Not found
            raise
        return index

    @property
    def xml_child_text(self):
        return u''.join([ ch for ch in self.xml_children
                            if isinstance(ch, unicode)])

    @property
    def xml_text_content(self):
        warnings.warn('This property will be eliminated soon.  Please use the unicode conversion function instead')
        return self.xml_child_text

    def __unicode__(self):
        '''
        Returns a Unicode object with the text contents of this node and
        its descendants, if any.
        Equivalent to DOM .textContent or XPath string() conversion
        '''
        return u''.join([ unicode(ch) for ch in self.xml_children
                          if not isinstance(ch, pi_base) and not isinstance(ch, comment_base)])

    def __str__(self):
        #Should we make the encoding configurable? (self.defencoding?)
        return unicode(self).encode('utf-8')

    def xml(self, stream=None, writer=None, force_nsdecls=None, **wargs):
        """
        serialize back to XML
        if stream is given, output to stream.  Function return value is None
        You can then set the following output parameters (among others):
            encoding - output encoding: default u'UTF-8'
            omitXmlDeclaration - u'no' to include an XML decl (default u'yes')
            cdataSectionElements - A list of element (namespace, local-name)
                                   And all matching elements are outptu as
                                   CDATA sections
            indent - u'yes' to pretty-print the XML (default u'no')
        other output parameters are supported, based on XSLT 1.0's xsl:output
        instruction, but use fo the others is encouraged only for very advanced
        users

        You can also just pass in your own writer instance, which might
        be useful if you want to output a SAX stream or DOM nodes

        If writer is given, use it directly (encoding can be set on the writer)
        if neither a stream nor a writer is given, return the output text
        as a Python string (not Unicode) encoded as UTF-8
        
        You can force Amara to emit particular namespace declarations on the
        top-level element using the optional force_nsdecls argument.  This
        is a dictionary with unicode prefix as the key and unicode namespace URI
        as the value.  You can, for example, use the xmlns_prefixes dictionary from
        any root node.
        """
        temp_stream = None
        close_document = 0
        if not writer:
            #Change the default to *not* generating an XML decl
            if not wargs.get('omitXmlDeclaration'):
                wargs['omitXmlDeclaration'] = u'yes'
            if stream:
                writer = create_writer(stream, wargs)
            else:
                temp_stream = cStringIO.StringIO()
                writer = create_writer(temp_stream, wargs)

            writer.startDocument()
            close_document = 1
        writer.startElement(self.nodeName, self.namespaceURI,
                            extraNss=force_nsdecls)
        if hasattr(self, 'xml_attributes'):
            for apyname in self.xml_attributes:
                aqname, ans = self.xml_attributes[apyname]
                val = self.__dict__[apyname]
                writer.attribute(aqname, val, ans)
        for child in self.xml_children:
            if isinstance(child, unicode):
                writer.text(child)
            else:
                child.xml(writer=writer)
        writer.endElement(self.nodeName, self.namespaceURI)
        if close_document:
            writer.endDocument()
        return temp_stream and temp_stream.getvalue()
    

def create_writer(stream, wargs=None, pubid=None, sysid=None, encoding="UTF-8"):
    wargs = wargs or {}
    if not stream:
        raise BinderException(NO_STREAM_GIVEN_FOR_UNBIND)
    op = OutputParameters.OutputParameters()
    for arg in wargs:
        setattr(op, arg, wargs[arg])
    #Doctype info in the document object override any given explicitly
    if sysid: op.doctypeSystem = sysid
    if pubid: op.doctypePublic = pubid
    #writer = XmlWriter.XmlWriter(op, stream)
    writer = XmlWriter.CdataSectionXmlWriter(op, stream)
    return writer


class BinderException(Exception):
    pass


#CLASH_BETWEEN_SCALAR_AND_SUBELEM = _('Bindery does not yet handle a name clash between an attribute and a child element')
NO_STREAM_GIVEN_FOR_UNBIND = _('You must provide a stream for the output of the xml method (serialization)')
INSTANCE_ALREADY_BOUND = _('Instance already bound to parent')

