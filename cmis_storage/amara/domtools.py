# -*- coding: iso-8859-1 -*-
#Required in Python 2.2, and must be the first import
from __future__ import generators
from xml.dom import Node

def doc_order_iter(node):
    """
    Iterates over each node in document order,
    yielding each in turn, starting with the given node
    node - the starting point
           (subtree rooted at node will be iterated over document order)
    """
    #Document order returns the current node,
    #then each of its children in turn
    yield node
    for child in node.childNodes:
        #Create a generator for each child,
        #Over which to iterate
        for cn in doc_order_iter(child):
            yield cn
    return


def doc_order_iter_filter(node, filter_func):
    """
    Iterates over each node in document order,
    applying the filter function to each in turn,
    starting with the given node, and yielding each node in
    cases where the filter function computes true
    node - the starting point
           (subtree rooted at node will be iterated over document order)
    filter_func - a callable object taking a node and returning
                  true or false
    """
    if filter_func(node):
        yield node
    for child in node.childNodes:
        for cn in doc_order_iter_filter(child, filter_func):
            yield cn
    return

def get_elements_by_tag_name(node, name):
    """
    Returns an iterator (in document order) over all the element nodes
    that are descendants of the given one, and have the given tag name.
y           node will be returned if it has the right name
    name - the node name to check
    """
    return doc_order_iter_filter(node, lambda n: n.nodeType == \
        Node.ELEMENT_NODE and n.nodeName == name)


def get_elements_by_tag_name_ns(node, ns, local):
    """
    Returns an iterator (in document order) over all the element nodes
    that are descendants of the given one, and have the given namespace
    and local name.
    node - the starting point (subtree rooted at node will be searched)
           node will be returned if it has the right ns and local name
    ns - the namespace to check
    local - the local name to check
    """
    return doc_order_iter_filter(node, lambda n: n.nodeType == \
        Node.ELEMENT_NODE and n.namespaceURI == ns and n.localName == local)


def get_first_element_by_tag_name_ns(node, ns, local):
    """
    Returns the first element in document order with the given namespace
    and local name
    node - the starting point (subtree rooted at node will be searched)
           node will be returned if it has the right ns and local name
    ns - the namespace to check
    local - the local name to check
    """
    return get_elements_by_tag_name_ns(node, ns, local).next()


def string_value(node):
    """
    Return the XPath string value of the given node
    This basically consists of one string comprising
    all the character data in the node and its descendants
    node - the starting point
    """
    text_nodes = doc_order_iter_filter(node, lambda n: n.nodeType == Node.TEXT_NODE)
    return u''.join([ n.data for n in text_nodes ])


def text_search(node, sought):
    """
    Return a list of descendant elements which contain a given substring
    in their text
    node - the starting point (subtree rooted at node will be searched)
    sought - the substring to find
    """
    return doc_order_iter_filter(node, lambda n: n.nodeType == Node.ELEMENT_NODE and [ 1 for cn in n.childNodes if cn.nodeType == Node.TEXT_NODE and cn.data.find(sought) != -1 ] )


def get_leaf_elements(node):
    """
    Return a list of elements that have no element children
    node - the starting point (subtree rooted at node will be searched)
    """
    return doc_order_iter_filter(node, lambda n: n.nodeType == Node.ELEMENT_NODE and not [ 1 for cn in n.childNodes if cn.nodeType == Node.ELEMENT_NODE ])


def rename_element(elem, new_ns, new_qname):
    new = elem.rootNode.createElementNS(new_ns, new_qname)
    for child in elem.childNodes:
        elem.removeChild(child)
        new.appendChild(child)
    elem.parentNode.replaceChild(new, elem)
    return new

#
# The following functions do not use the generator/iterator framework
#

#Mapping from node type to XPath node test function name
OTHER_NODES = {
    Node.TEXT_NODE: 'text',
    Node.COMMENT_NODE: 'comment',
    Node.PROCESSING_INSTRUCTION_NODE: 'processing-instruction'
    }

from Ft.Xml.Domlette import GetAllNs, SeekNss
DEFAULT_GENERATED_PREFIX = u"amara.4suite.org.ns%i"

def abs_path(node, prefixes=None):
    #based on code developed by Florian Bosch on XML-SIG
    #http://mail.python.org/pipermail/xml-sig/2004-August/010423.html
    #Significantly enhanced to use Unicode properly, support more
    #node types, use safer node type tests, etc.
    """
    Return an XPath expression that provides a unique path to
    the given node (supports elements, attributes, root nodes,
    text nodes, comments and PIs) within a document

    prefixes - optional hint dictionary from prefix to namespace
               if the document uses the default namespace, this function
               might need to come up with a prefix for the QName for certain
               nodes.  You can help control such prefix selection by passing in
               this dictionary.  Prefixes found in this dictionary will
               be used to reconcile default namespace usage
               WARNING: this value may be mutated by this function--key/value
               pairs might be added to the dictionary
    """
    if node.nodeType == Node.ELEMENT_NODE:
        count = 1
        #Count previous siblings with same node name
        previous = node.previousSibling
        while previous:
            if ((previous.namespaceURI, previous.localName)
                == (node.namespaceURI, node.localName)):
                count += 1
            previous = previous.previousSibling
        qname = node.nodeName
        if node.namespaceURI and not node.prefix:
            if prefixes is None:
                prefixes = GetAllNs(node)
            #nicer code, but maybe slower than iterating items()
            nss = dict([(n,p) for (p,n) in prefixes.items()])
            #must provide a prefix for XPath
            prefix = nss.get(node.namespaceURI)
            if not prefix:
                prefix_count = 1
                prefix = DEFAULT_GENERATED_PREFIX%count
                while prefix in prefixes:
                    prefix_count += 1
                    prefix = DEFAULT_GENERATED_PREFIX%count
            prefixes[prefix] = node.namespaceURI
            qname = prefix + u':' + node.localName
        step = u'%s[%i]' % (qname, count)
        ancestor = node.parentNode
    elif node.nodeType == Node.ATTRIBUTE_NODE:
        step = u'@%s' % (node.nodeName)
        ancestor = node.ownerElement
    elif node.nodeType in OTHER_NODES:
        #Text nodes, comments and PIs
        count = 1
        #Count previous siblings of the same node type
        previous = node.previousSibling
        while previous:
            if previous.nodeType == node.nodeType: count += 1
            previous = previous.previousSibling
        test_func = OTHER_NODES[node.nodeType]
        step = u'%s()[%i]' % (test_func, count)
        ancestor = node.parentNode
    elif not node.parentNode:
        #Root node
        step = u''
        ancestor = node
    else:
        raise TypeError('Unsupported node type for abs_path')
    if ancestor.parentNode:
        return abs_path(ancestor, prefixes) + u'/' + step
    else:
        return u'/' + step


import xml.sax
from Ft.Xml import Sax
from amara.saxtools import sax2dom_chunker
from Ft.Xml import InputSource
from Ft.Lib import Uri, Uuid
from Ft.Xml.Lib.XmlString import IsXml

def pushdom(source, xpatterns, prefixes=None, validate=False):
    parser = Sax.CreateParser()
    if validate:
        parser.setFeature(xml.sax.handler.feature_validation, True)
    else:
        parser.setFeature(xml.sax.handler.feature_external_pes, False)
    parser.setFeature(Sax.FEATURE_GENERATOR, True)

    def handle_chunk(docfrag):
        parser.setProperty(Sax.PROPERTY_YIELD_RESULT, docfrag)

    handler = sax2dom_chunker(xpatterns=xpatterns,
                              nss=prefixes,
                              chunk_consumer=handle_chunk)
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


#def insert_xml(node, position, text):
#    """
#    Parse some text and insert it as a child of an element
#    """

