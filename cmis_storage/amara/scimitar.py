#!/usr/bin/env python
"""
Python compiler from ISO Schematron to a Python validator script
"""

import os
import sys
import codecs
import optparse
import warnings
import cStringIO
from Ft.Xml import Sax
from amara import saxtools
from Ft.Xml.Xslt import XSL_NAMESPACE


_ = lambda x:x.encode('utf-8')

SCRIPT_HEADER = u'#!/usr/bin/env python'

TOP_SKEL = u'''\
%s
#Warning: this is an auto-generated file.  Do not edit unless you're
#sure you know what you're doing

import sys
import codecs
import optparse
import cStringIO
from Ft.Xml import InputSource, CreateInputSource
from Ft.Xml.Xslt import PatternList, parser
from Ft.Xml.Xslt import Stylesheet, Processor, OutputHandler, OutputParameters
from Ft.Xml.XPath import Compile as CompileXPath
from Ft.Xml.XPath.Context import Context as XPathContext
from Ft.Xml.Xslt.XsltContext import XsltContext
from Ft.Xml.Domlette import NonvalidatingReader, GetAllNs
from Ft.Xml.XPath import Conversions
from Ft.Xml.XPath import Util
from Ft.Xml.XPath import CoreFunctions

from Ft.Xml.Xslt.XmlWriter import XmlWriter
from Ft.Xml.Xslt.OutputParameters import OutputParameters
from Ft.Xml.Xslt import XsltFunctions, Exslt
from Ft.Lib import Uri

from amara import domtools

XPATTERN_PARSER = parser.new()
del parser

#STRON_DOC_DUMMY_BASE = 'http://4suite.org/amara/scimitar/schematron-file'

'''%SCRIPT_HEADER

QB_SKEL = u'''\
'''

MAIN_SKEL = u'''
#Set up the function library for context objects according to queryBinding attr
#Determine from the query binding whether functions could require a result tree
RESULT_TREE_PROCESSOR = False
if QUERY_BINDING == u'full':
    FUNCTIONS = XsltContext.functions.copy()
    RESULT_TREE_PROCESSOR = True
elif QUERY_BINDING == u'exslt':
    FUNCTIONS = CoreFunctions.CoreFunctions.copy()
    FUNCTIONS.update(XsltFunctions.CoreFunctions)
    FUNCTIONS.update(Exslt.ExtFunctions)
    RESULT_TREE_PROCESSOR = True
elif QUERY_BINDING == u'xslt':
    FUNCTIONS = CoreFunctions.CoreFunctions.copy()
    FUNCTIONS.update(XsltFunctions.CoreFunctions)
elif QUERY_BINDING == u'xpath':
    FUNCTIONS = CoreFunctions.CoreFunctions.copy()
else:
    raise ValueError('Unknown query binding: %%s'%%repr(QUERY_BINDING))


class faux_instruction:
    baseUri = STRON_BASE_URI

class faux_root_node:
    sources = []

class faux_xslt_proc(Stylesheet.StylesheetElement, Processor.Processor):
    #Pretends to be an XSLT processor for processing keys
    def __init__(self, doc):
        self.namespaces = NSS
        #self._keys = [ (Util.ExpandQName(k[0], doc), k[1], k[2]) for k in KEYS ]
        keys = [ (Util.ExpandQName(k[0], doc), (k[1], k[2], GetAllNs(doc))) for k in KEYS ]
        self.keys = {}
        self._keys = {}
        for name, info in keys:
            self._keys.setdefault(name, []).append(info)
        #Update all the keys for all documents in the context
        #Note: 4Suite uses lazy key eval.  Consider emulating this
        for key in self._keys:
            Stylesheet.StylesheetElement.updateKey(self, doc, key[0], self)
        if RESULT_TREE_PROCESSOR:
            Processor.Processor.__init__(self)
            #Start code from Processor.runNode
            if hasattr(doc, 'baseURI'):
                node_baseUri = doc.baseURI
            elif hasattr(doc, 'refUri'):
                node_baseUri = doc.refUri
            else:
                node_baseUri = None
            sourceUri = node_baseUri or Uri.BASIC_RESOLVER.generate()
            #Create a dummy iSrc
            docInputSource = InputSource.InputSource(
                None, sourceUri, processIncludes=1,
                stripElements=self.getStripElements(),
                factory=self.inputSourceFactory)
            #return self.execute(node, docInputSource, outputStream=None)
            outputStream = cStringIO.StringIO()
            def writer_changed_handler(newWriter):
                self.writers[-1] = newWriter
            self.outputParams = OutputParameters()
            writer = OutputHandler.OutputHandler(
                self.outputParams, outputStream, writer_changed_handler)
            self.writers = [writer]
        self.initialFunctions = {}
        self.stylesheet = self
        self.root = faux_root_node()
        self._documentInputSource = InputSource.DefaultFactory.fromString('<dummy/>', Uri.OsPathToUri('.'))
        return


def validate(xmlf, reportf, phase=None):
    global WRITER, EXTFUNCTS
    oparams = OutputParameters()
    oparams.indent = 'yes'
    WRITER = XmlWriter(oparams, reportf)
    WRITER.startDocument()

    WRITER.text(u'Processing schema: ')
    WRITER.text(%(title)s)
    WRITER.text(u'\\n\\n')
    
    if xmlf == '-':
        doc = NonvalidatingReader.parseStream(sys.stdin, 'urn:stron-candidate-dummy')
    elif not isinstance(xmlf, str):
        doc = NonvalidatingReader.parseStream(xmlf, 'urn:stron-candidate-dummy')
    else:
        try:
            doc = NonvalidatingReader.parseUri(xmlf)
        except ValueError:
            doc = NonvalidatingReader.parseUri(Uri.OsPathToUri(xmlf))

    global key_handler
    key_handler = faux_xslt_proc(doc)
    #Pre-process keys, if any
    #for kname, (kuse, kmatch) in KEYS.items:

    if phase in [None, u'#DEFAULT']:
        phase = DEFAULT_PHASE
    if phase == u'#ALL':
        patterns = PATTERNS
    else:
        patterns = [ p for p in PATTERNS if p[1] in PHASES[phase] ]

    #Main rule-processing loop
    if patterns:
        for pat in patterns:
            #if not pat[2].keys():
            #    WRITER.text(_(u'Pattern context not given'))
            plist = PatternList(pat[2].keys(), NSS)
            WRITER.text(u'Processing pattern: ')
            WRITER.text(pat[0] or u'[unnamed]')
            WRITER.text(u'\\n\\n')
            for node in domtools.doc_order_iter(doc):
                matches = plist.lookup(node)
                if matches:
                    func = pat[2][matches[0]]
                    func(node)
    else:
        #Second parameter is a dictionary of prefix to namespace mappings
        plist = PatternList(CONTEXTS.keys(), {})
        for node in domtools.doc_order_iter(doc):
            #FIXME: this is a 4Suite bug work-around.  At some point remove
            #The redundant context setting
            matches = plist.lookup(node)
            if matches:
                func = CONTEXTS[matches[0]]
                func(node)
    WRITER.endDocument()
    return


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def command_line_prep():
    from optparse import OptionParser
    usage = "%%prog [options] xml-file\\nxml-file is the XML file to be validated"
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--val-output",
                      action="store", type="string", dest="val_output",
                      help="generate the validation report file FILE (XML external parsed entity format)", metavar="FILE")
    parser.add_option("-p", "--phase",
                      action="store", type="string",
                      help="Execute the schema in the specified phase", metavar="XML_ID")
    return parser

def main(argv=[__name__]):
    #Ideas borrowed from http://www.artima.com/forums/flat.jsp?forum=106&thread=4829
    if argv is None:
        argv = sys.argv
    try:
        try:
            optparser = command_line_prep()
            global OPTIONS, ARGS
            (OPTIONS, ARGS) = optparser.parse_args(argv)
            candidate_file = ARGS[1]
        except KeyboardInterrupt:
            pass
        except:
             raise Usage(optparser.format_help())
        enc, dec, inwrap, outwrap = codecs.lookup('utf-8')
        fout = OPTIONS.val_output
        phase = OPTIONS.phase
        if fout:
            fout = open(fout, 'w')
        else:
            fout = sys.stdout
        validate(candidate_file, outwrap(fout), phase=phase)
    except Usage, err:
        print >>sys.stderr, err.msg
        return 2

'''

SCRIPT_SKEL = u'''
if __name__ == "__main__":
    sys.exit(main(sys.argv))

'''

TEST_SCRIPT_SKEL = u'''
if __name__ == "__main__":
    if not TEST:
        sys.exit(main(sys.argv))

'''

RULE_SKEL = u'''
def %(rname)s(node):
    #For context XPattern %(context)s
    vars = {}
    xpath_ctx = XsltContext(node, processor=key_handler,
                            processorNss=NSS, varBindings=vars,
                            currentNode=node
                            )
    xpath_ctx.currentInstruction = faux_instruction()
    xpath_ctx.functions = FUNCTIONS
'''

ASSERT_SKEL = u'''\
    expr = CompileXPath(%(test)s)
    if not Conversions.BooleanValue(expr.evaluate(xpath_ctx)):
'''

REPORT_SKEL = u'''\
    expr = CompileXPath(%(test)s)
    if Conversions.BooleanValue(expr.evaluate(xpath_ctx)):
'''

DIAG_SKEL = u'''\
def diag%(diagcount)i(xpath_ctx):
    #Diagnostic named %(id)s
'''

EMIT_RULE_PATTERN_ITEM = u'''\
  XPATTERN_PARSER.parse(%(pat)s): %(func)s,
'''

EMIT_DIAG_ID_ITEM = u'''\
  %(id)s: %(func)s,
'''

EMIT_PHASE_ITEM = u'''\
  %(id)s: %(patterns)s,
'''

EMIT_START_ELEM_SKEL = u'''\
%(indent)sWRITER.startElement(%(qname)s, %(ns)s)
'''

EMIT_END_ELEM_SKEL  = u'''\
%(indent)sWRITER.endElement(%(qname)s, %(ns)s)
'''

EMIT_ATTRIBUTE_SKEL  = u'''\
%(indent)sWRITER.attribute(%(qname)s, %(ns)s, %(val)s)
'''

EMIT_TEXT_SKEL  = u'''\
%(indent)sWRITER.text(%(text)s)
'''

EMIT_NAME_SKEL  = u'''\
%(indent)sexpr = CompileXPath(%(path)s)
%(indent)sname = CoreFunctions.Name(xpath_ctx, expr.evaluate(xpath_ctx))
%(indent)sWRITER.text(name)
'''

EMIT_VALUE_OF_SKEL  = u'''\
%(indent)sexpr = CompileXPath(%(select)s)
%(indent)sval = Conversions.StringValue(expr.evaluate(xpath_ctx))
%(indent)sWRITER.text(val)
'''


OLD_STRON_NS = 'http://www.ascc.net/xml/schematron'
ISO_STRON_NS = 'http://purl.oclc.org/dsdl/schematron'

#The marker within an abstract pattern template for a chunk to be parameterized
ABSPAT_DELIMITER = u'\u0001'    #A char that cannot appear in XML


class pattern:
    def __init__(self, name, id_, abstract):
        self.name = name
        self.id = id_
        self.abstract = abstract
        self.concrete_rules = {}
        self.abstract_rules = {}
        self.rule_contexts = []


class stron_consumer:
    """
    Encapsulation of a set of semi-co-routines designed to handle SAX
    Events from Schematron
    """
    def __init__(self, output):
        self.top_dispatcher = {
            (saxtools.START_ELEMENT, STRON_NS, u'schema'):
            self.handle_schema,
            }
        if STRON_NS != OLD_STRON_NS:
            self.top_dispatcher[(saxtools.START_ELEMENT, OLD_STRON_NS, u'schema')] = self.handle_obsolete_schema
        self.output = output
        self.rule_contexts = {}
        self.rule_count = 1
        self.diag_ids = {}
        self.diag_count = 1
        self.event = None
        self.schema_title = u''
        self.patterns = []
        self.abstract_patterns = {}
        self.curr_pattern = None
        self.nss = {}
        self.keys = []
        self.vars = {}
        self.phases = {}
        self.root_schema_element_count = 0
        return

    def handle_obsolete_schema(self, end_condition):
        warnings.warn('You appear to be using the obsolete Schematron namespace "%s", which is no longer supported by Scimitar.  Please use the correct namespace "%s".'%(OLD_STRON_NS, STRON_NS), DeprecationWarning)
        yield None
        return

    def handle_schema(self, end_condition):
        #Check that there is one, and only one root sch:schema element
        self.root_schema_element_count += 1
        dispatcher = {
            (saxtools.START_ELEMENT, STRON_NS, u'title'):
            self.handle_title,
            (saxtools.START_ELEMENT, STRON_NS, u'phase'):
            self.handle_phase,
            (saxtools.START_ELEMENT, STRON_NS, u'pattern'):
            self.handle_pattern,
            (saxtools.START_ELEMENT, STRON_NS, u'rule'):
            self.handle_rule,
            (saxtools.START_ELEMENT, STRON_NS, u'diagnostic'):
            self.handle_diagnostic,
            (saxtools.START_ELEMENT, STRON_NS, u'ns'):
            self.handle_ns,
            (saxtools.START_ELEMENT, OLD_STRON_NS, u'key'):
            self.handle_key,
            (saxtools.START_ELEMENT, XSL_NAMESPACE, u'key'):
            self.handle_key,
            }
        #Initial call corresponds to the start schema element
        #Update the version, if specified.  Default version is ISO
        self.version = self.params.get((None, 'schemaVersion'), u'ISO')
        self.id = self.params.get((None, 'id'))
        self.query_binding = self.params.get((None, 'queryBinding'), u'xslt')
        self.default_phase = self.params.get((None, 'defaultPhase'), u'#ALL')
        self.output.write(TOP_SKEL)
        self.output.write(u'STRON_BASE_URI = \'%s\''%self.baseUri)
        self.output.write(u'\nQUERY_BINDING = %s\n\n'%repr(self.query_binding))
        self.output.write(QB_SKEL)
        curr_gen = None
        yield None
        while not self.event == end_condition:
            #print "schema", self.event
            curr_gen = saxtools.tenorsax.event_loop_body(dispatcher, curr_gen, self.event)
            yield None
        #Element closed.  Wrap up
        self.output.write(u'\nPATTERNS = [\n')
        for pat in self.patterns:
            pname = pat.name; pid = pat.id; pcontexts = pat.concrete_rules
            self.output.write(u'(\n %s, %s, {\n'%(repr(pname), repr(pid)))
            for rc in pcontexts:
                self.output.write(EMIT_RULE_PATTERN_ITEM%{'pat': repr(rc), 'func': pcontexts[rc]})
            self.output.write(u'}),\n')
        self.output.write(u']\n')
        self.output.write(u'\nPHASES = {\n')
        for id in self.phases:
            self.output.write(EMIT_PHASE_ITEM%{'id': repr(id), 'patterns': repr(self.phases[id])})
        self.output.write(u'}\n')
        self.output.write(u'\nCONTEXTS = {\n')
        for rc in self.rule_contexts:
            self.output.write(EMIT_RULE_PATTERN_ITEM%{'pat': repr(rc), 'func': self.rule_contexts[rc]})
        self.output.write(u'}\n')
        self.output.write(u'\nDIAGNOSTICS = {\n')
        for id in self.diag_ids:
            self.output.write(EMIT_DIAG_ID_ITEM%{'id': repr(id), 'func': self.diag_ids[id]})
        self.output.write(u'}\n')
        self.output.write(u'\nNSS = {\n')
        for prefix in self.nss:
            ns = self.nss[prefix]
            self.output.write(u'%(prefix)s: %(ns)s, '%{'prefix': repr(prefix), 'ns': ns and repr(ns)})
        self.output.write(u'}\n')
        self.output.write(u'\nKEYS = [\n')
        for n, m, u in self.keys:
            self.output.write(u'(%(n)s, %(m)s, CompileXPath(%(u)s)),'%{'n': repr(n), 'm': repr(m), 'u': repr(u)})
        self.output.write(u']\n')
        
        self.output.write(u'\nDEFAULT_PHASE = %s\n\n'%repr(self.default_phase))
        self.output.write(BOTTOM_SKEL%{'title': repr(self.schema_title)})
        raise StopIteration

    def handle_pattern(self, end_condition):
        name = self.params.get((None, 'name'))
        id_ = self.params.get((None, 'id'))
        abstract = self.params.get((None, 'abstract')) == u'true'
        isa = self.params.get((None, 'is-a'))
        self.curr_pattern = pattern(name, id_, abstract)
        if abstract:
            save_output = self.output
            self.output = cStringIO.StringIO()
        if isa:
            params = {}
        def handle_param(end_condition):
            formal = self.params.get((None, 'formal'))
            actual = self.params.get((None, 'actual'))
            if formal is None or actual is None:
                raise ValueError(_(u"sch:param must have 'formal' and 'actual' attributes."))
            params[formal] = actual
            yield None
            return
        dispatcher = {
            (saxtools.START_ELEMENT, STRON_NS, 'rule'):
            self.handle_rule,
            (saxtools.START_ELEMENT, STRON_NS, 'param'):
            handle_param,
            }
        curr_gen = None
        yield None
        while not self.event == end_condition:
            #print "pattern", self.event
            curr_gen = saxtools.tenorsax.event_loop_body(dispatcher, curr_gen, self.event)
            yield None
        #Element closed.  Wrap up
        if abstract:
            #Create a closure for resolving the abstract pattern
            def resolve_abspat(
                    params, template=self.output.getvalue(),
                    rule_contexts=self.curr_pattern.rule_contexts):
                #print >> sys.stderr, 'Resolving abstract pattern', template, params
                #Must sort param keys so that e.g. given one formal param $a
                #and another $ab, processing the first doesn't break
                #processing of the second
                param_keys = params.keys()
                param_keys.sort(lambda a, b: cmp(len(b), len(a)))

                rule_contexts = iter(rule_contexts)
                chunks = template.split(ABSPAT_DELIMITER)
                for count, chunk in enumerate(chunks):
                    if count % 2:
                        if chunk == '$':
                            rfunc = u'rule' + str(self.rule_count)
                            context = rule_contexts.next()
                            for formal in param_keys:
                                context = context.replace('$'+formal, params[formal])
                            self.curr_pattern.concrete_rules[context] = rfunc
                            self.output.write(str(self.rule_count))
                            self.rule_count += 1
                        else:
                            for formal in param_keys:
                                chunk = chunk.replace('$'+formal, params[formal])
                            self.output.write(repr(chunk))
                    else:
                        self.output.write(chunk)
            self.output = save_output
            self.abstract_patterns[id_] = resolve_abspat
        if isa:
            #FIXME: assumes abs pattern is defined before the parameter pattern
            #Probably not a valid restriction
            resolve = self.abstract_patterns[isa]
            resolve(params)
        if not self.curr_pattern.abstract:
            self.patterns.append(self.curr_pattern)
        self.curr_pattern = None
        raise StopIteration

    def handle_rule(self, end_condition):
        dispatcher = {
            (saxtools.START_ELEMENT, STRON_NS, 'assert'):
            self.handle_assert,
            (saxtools.START_ELEMENT, STRON_NS, 'report'):
            self.handle_report,
            (saxtools.START_ELEMENT, STRON_NS, 'let'):
            self.handle_rule_let,
            (saxtools.START_ELEMENT, STRON_NS, 'extends'):
            self.handle_extends,
            }
        id_ = self.params.get((None, 'id'))
        context = self.params.get((None, 'context'))
        abstract = self.params.get((None, 'abstract'), 'no') == 'yes'
        if abstract and context:
            raise TypeError(_(u'An abstract rule cannot have a context'))
        if not abstract and not context:
            raise TypeError(_(u'A non-abstract rule must have a context'))
        save_vars = self.vars
        if self.curr_pattern and self.curr_pattern.abstract:
            #Handle parameterization for context in abstract patterns
            marked_context = ABSPAT_DELIMITER + context + ABSPAT_DELIMITER
            rfunc_name = u'rule' + ABSPAT_DELIMITER + '$' + ABSPAT_DELIMITER
            self.output.write(RULE_SKEL%{'rname': rfunc_name, 'context': marked_context})
            self.curr_pattern.rule_contexts.append(context)
        else:
            if id_:
                rfunc_name = u'rule_' + id_
            else:
                rfunc_name = u'rule' + str(self.rule_count)
                self.rule_count += 1
            self.output.write(
                RULE_SKEL%{'rname': rfunc_name,
                           'context': repr(context)})
            if abstract:
                self.curr_pattern.abstract_rules[id] = rfunc_name
            else:
                self.curr_pattern.rule_contexts.append(context)
                self.curr_pattern.concrete_rules[context] = rfunc_name
        curr_gen = None
        yield None
        while not self.event == end_condition:
            curr_gen = saxtools.tenorsax.event_loop_body(dispatcher, curr_gen, self.event)
            yield None
        #Element closed.  Wrap up
        self.output.write(u'\n    return\n\n')
        self.vars = save_vars
        raise StopIteration

    def handle_extends(self, end_condition):
        rule = self.params.get((None, 'rule'))
        self.output.write(u'    rule_' + rule + '(node)\n')
        yield None
        return

    def handle_assert(self, end_condition):
        test = self.params.get((None, 'test'))
        diagnostics = self.params.get((None, 'diagnostics'))
        #FIXME: should use NMTOKENS savvy splitter
        diagnostics = diagnostics and diagnostics.split() or []
        #We want to capture all char data and markup children, so register a
        #special handler for this purpose
        curr_gen = self.xml_repeater(' '*8)
        if self.curr_pattern and self.curr_pattern.abstract:
            #Handle parameterization for asserts in abstract patterns
            marked_test = ABSPAT_DELIMITER + test + ABSPAT_DELIMITER
            self.output.write(ASSERT_SKEL%{'test': marked_test})
        else:
            self.output.write(ASSERT_SKEL%{'test': repr(test)})
        self.output.write(EMIT_TEXT_SKEL%{'indent': ' '*8, 'text': repr(u'Assertion failure:\n')})
        yield None
        while not self.event == end_condition:
            #if curr_gen: curr_gen = tenorsax.delegate(curr_gen)
            curr_gen.next()
            yield None
        #Element closed.  Wrap up
        self.output.write(EMIT_TEXT_SKEL%{'indent': ' '*8, 'text': repr(u'\n')})
        for diag_id in diagnostics:
            self.output.write(u'\n%(indent)sDIAGNOSTICS[%(id)s](xpath_ctx)\n'%{'indent': ' '*8, 'id': repr(diag_id)})
        self.output.write(EMIT_TEXT_SKEL%{'indent': ' '*8, 'text': repr(u'\n')})
        #del curr_gen
        raise StopIteration

    def handle_report(self, end_condition):
        test = self.params.get((None, 'test'))
        #We want to capture all char data and markup children, so register a
        #special handler for this purpose
        curr_gen = self.xml_repeater(' '*8)
        if self.curr_pattern and self.curr_pattern.abstract:
            #Handle parameterization for reports in abstract patterns
            marked_test = ABSPAT_DELIMITER + test + ABSPAT_DELIMITER
            self.output.write(REPORT_SKEL%{'test': marked_test})
        else:
            self.output.write(REPORT_SKEL%{'test': repr(test)})
        self.output.write(EMIT_TEXT_SKEL%{'indent': ' '*8, 'text': repr(u'Report:\n')})
        yield None
        while not self.event == end_condition:
            curr_gen.next()
            yield None
        #Element closed.  Wrap up
        self.output.write(EMIT_TEXT_SKEL%{'indent': ' '*8, 'text': repr(u'\n\n')})
        #del curr_gen
        raise StopIteration

    def handle_diagnostic(self, end_condition):
        id = self.params.get((None, 'id'))
        #We want to capture all char data and markup children, so register a
        #special handler for this purpose
        curr_gen = self.xml_repeater(' '*4)
        self.output.write(DIAG_SKEL%{'diagcount': self.diag_count, 'id': repr(id)})
        self.output.write(EMIT_TEXT_SKEL%{'indent': ' '*4, 'text': repr(u'Diagnostic message:\n')})
        self.diag_ids[id] = 'diag' + str(self.diag_count)
        self.diag_count += 1
        yield None
        while not self.event == end_condition:
            curr_gen.next()
            yield None
        #Element closed.  Wrap up
        self.output.write(EMIT_TEXT_SKEL%{'indent': ' '*4, 'text': repr(u'\n')})
        self.output.write(u'\n    return\n\n')
        #del curr_gen
        raise StopIteration

    def handle_phase(self, end_condition):
        id = self.params.get((None, 'id'))
        self.phases[id] = []
        def handle_active(end_condition):
            pattern = self.params.get((None, 'pattern'))
            self.phases[id].append(pattern)
            yield None
            return
        dispatcher = {
            (saxtools.START_ELEMENT, STRON_NS, 'active'):
            handle_active,
            }
        curr_gen = None
        yield None
        while not self.event == end_condition:
            curr_gen = saxtools.tenorsax.event_loop_body(dispatcher, curr_gen, self.event)
            yield None
        raise StopIteration

    def handle_title(self, end_condition):
        yield None
        while not self.event == end_condition:
            if self.event[0] == (saxtools.CHARACTER_DATA):
                self.schema_title += self.params
            yield None

    def handle_key(self, end_condition):
        name = self.params.get((None, 'name'))
        use = self.params.get((None, 'use'))
        match = self.params.get((None, 'match'))
        self.keys.append((name, match, use))
        yield None
        return

    def handle_ns(self, end_condition):
        prefix = self.params.get((None, 'prefix'))
        ns = self.params.get((None, 'uri'))
        self.nss[prefix] = ns
        yield None
        return

    def handle_rule_let(self, end_condition):
        name = self.params.get((None, 'name'))
        value = self.params.get((None, 'value'))
        #self.output.write(' '*4 + 'xpath_ctx.currentInstruction = faux_instruction()\n')
        self.output.write(' '*4 + 'xpath_ctx.varBindings[(None, ' + repr(name) + ')] = CompileXPath(' + repr(value) + ').evaluate(xpath_ctx)\n')
        #self.output.write(' '*4 + 'vars[(None, ' + repr(name) + ')] = CompileXPath(' + repr(value) + ').evaluate(xpath_ctx)\n')
        #self.output.write(' '*4 + 'xpath_ctx = XsltContext(node, currentNode=node, processor=key_handler, processorNss=NSS, varBindings=vars)\n')
        #self.output.write(' '*4 + 'xpath_ctx.functions = FUNCTIONS\n')
        #self.vars[name] = value
        yield None
        return

    def xml_repeater(self, indent):
        #print "xml_repeater"
        while 1:
            if self.event[0] == saxtools.START_ELEMENT:
                #emph, name and value-of are special cases
                if self.event[1:3] == (STRON_NS, u'name'):
                    path = self.params.get((None, 'path'), u'.')
                    if self.curr_pattern and self.curr_pattern.abstract:
                        #Handle parameterization in abstract patterns
                        marked_path = ABSPAT_DELIMITER + path + ABSPAT_DELIMITER
                        self.output.write(EMIT_NAME_SKEL%{'indent': indent, 'path': marked_path})
                    else:
                        self.output.write(EMIT_NAME_SKEL%{'indent': indent, 'path': repr(path)})
                elif self.event[1:3] == (STRON_NS, u'value-of'):
                    select = self.params.get((None, 'select'))
                    if self.curr_pattern and self.curr_pattern.abstract:
                        #Handle parameterization in abstract patterns
                        marked_select = ABSPAT_DELIMITER + select + ABSPAT_DELIMITER
                        self.output.write(EMIT_VALUE_OF_SKEL%{'indent': indent, 'select': marked_select})
                    else:
                        self.output.write(EMIT_VALUE_OF_SKEL%{'indent': indent, 'select': repr(select)})
                elif self.event[1:3] == (STRON_NS, u'emph'):
                    self.output.write(EMIT_START_ELEM_SKEL%{'indent': indent, 'qname': repr(self.event[2]), 'ns': repr(None)})
                else:
                    #Using local name for qname for now
                    self.output.write(EMIT_START_ELEM_SKEL%{'indent': indent, 'qname': repr(self.event[2]), 'ns': repr(self.event[1])})
            if self.event[0] == saxtools.END_ELEMENT:
                if not self.event[1:3] in [(STRON_NS, u'name'), (STRON_NS, u'value-of')]:
                    self.output.write(EMIT_END_ELEM_SKEL%{'indent': indent, 'qname': repr(self.event[2]), 'ns': repr(self.event[1])})
            if self.event[0] == saxtools.CHARACTER_DATA:
                self.output.write(EMIT_TEXT_SKEL%{'indent': indent, 'text': repr(self.params)})
            yield None


from Ft.Xml import InputSource, CreateInputSource
from Ft.Lib import Uri, Uuid

def run(stron_src, validator_outf, legacy_ns=False, prep_for_test=0):
    global BOTTOM_SKEL, STRON_NS
    if legacy_ns:
        STRON_NS = OLD_STRON_NS
    else:
        STRON_NS = ISO_STRON_NS
    if prep_for_test:
        BOTTOM_SKEL = MAIN_SKEL + TEST_SCRIPT_SKEL
    else:
        BOTTOM_SKEL = MAIN_SKEL + SCRIPT_SKEL
    parser = Sax.CreateParser()
    consumer = stron_consumer(validator_outf)
    handler = saxtools.tenorsax(consumer)
    parser.setContentHandler(handler)
    source = CreateInputSource(stron_src)
    consumer.baseUri = source.uri
    parser.parse(source)
    if not consumer.root_schema_element_count:
        raise RuntimeError('No Schematron schema was found')
    elif consumer.root_schema_element_count > 1:
        raise RuntimeError('More than one Schematron schema was found.')
    return


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def command_line_prep():
    from optparse import OptionParser
    usage = "%prog [options] schematron-file"
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--val-script",
                      action="store", type="string", dest="stron_script",
                      help="generate the XML validator script FILE", metavar="FILE")
    parser.add_option("--legacy-ns",
                      action="store_true", dest="legacy_ns", default=0,
                      help="Use the legacy Schematron namespace")
    parser.add_option("--test",
                      action="store_true", dest="test_ready", default=0,
                      help="generate hooks for unit tests in the validator")
    #parser.add_option("-q", "--quiet",
    #                  action="store_false", dest="verbose", default=1,
    #                  help="don't print status messages to stdout")
    return parser

        
def main(argv=None):
    if argv is None:
        argv = sys.argv
    # By default, optparse usage errors are terminated by SystemExit
    try:
        optparser = command_line_prep()
        options, args = optparser.parse_args(argv[1:])
        # Process mandatory arguments with IndexError try...except blocks
        try:
            stron_fname = args[0]
        except IndexError:
            optparser.error("Missing schematron filename")
    except SystemExit, status:
        return status

    # Perform additional setup work here before dispatching to run()
    # Detectable errors encountered here should be handled and a status
    # code of 1 should be returned. Note, this would be the default code
    # for a SystemExit exception with a string message.
    fout = options.stron_script
    if not fout:
        fout = os.path.splitext(stron_fname)[0] + '-stron.' + 'py'
    fout = codecs.open(fout, 'w', 'utf-8')

    if stron_fname == '-':
        stronf = sys.stdin
    else:
        stronf = open(stron_fname, 'r')
    run(stronf, fout, options.legacy_ns, options.test_ready)

    # A status code of 0 indicates successful completion
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))


