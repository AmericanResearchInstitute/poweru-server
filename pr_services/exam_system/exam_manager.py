"""
Exam Manager class.
"""

__docformat__ = "restructuredtext en"

# Python
import codecs
from decimal import Decimal
from cStringIO import StringIO
import sys
import xml.dom.minidom
import xml.etree.cElementTree as elementtree

# PowerReg
from pr_services.credential_system.task_manager import TaskManager
from pr_services.rpc.service import service_method
import facade

class ExamManager(TaskManager):
    """
    Manage exams in the Power Reg system.

    **Attributes:**
     * *name* -- Unique name for this exam within the system.
     * *passing_score* -- Minimum score required to pass the exam (0 to 100 inclusive).
     * *question_pools* -- List of foreign keys for question pool objects.
     * *title* -- Title of the exam.
    """

    def __init__(self):
        """constructor"""

        super(ExamManager, self).__init__()
        self.getters.update({
            'name': 'get_general',
            'passing_score': 'get_general',
            'question_pools': 'get_many_to_one',
        })
        self.setters.update({
            'name': 'set_general',
            'passing_score': 'set_general',
            'question_pools': 'set_many',
        })
        self.my_django_model = facade.models.Exam

    @service_method
    def create(self, auth_token, name, title=None, optional_parameters=None):
        """
        Create a new exam.

        :param auth_token:          The authentication token of the acting user
        :type auth_token:           pr_services.models.AuthToken
        :param name:                Unique name of the exam.
        :type name:                 unicode
        :param title:               Title of the exam.
        :type title:                unicode
        :param optional_parameters: optional parameters, possibly including:

            * passing_score
            * question_pools

        :type optional_parameters:  dict or None
        :return:                    Reference to the newly created exam.
        """

        if optional_parameters is None:
            optional_parameters = {}

        e = self.my_django_model(name=name, title=title)
        e.save()
        if optional_parameters:
            facade.subsystems.Setter(auth_token, self, e, optional_parameters)
            e.save()
        self.authorizer.check_create_permissions(auth_token, e)
        return e

    #: the XML namespace for valid exam XML documents
    xml_namespace = "http://americanri.com/2009/poweru/exam/1.0"

    @service_method
    def create_from_xml(self, auth_token, xml_data):
        """
        Create an exam session from an XML document.
        
        The XML schema is defined as a Relax-NG schema in exam_schema.xml.
        
        :param auth_token:  The authentication token of the acting user
        :type auth_token:   pr_services.models.AuthToken
        :param xml_data:    the XML document, as a string
        :type xml_data:     string
        :return:            Reference to the newly created exam.
        """

        def add_attribute(element, xml_attribute_name, django_model_instance,
                          attribute_name, attribute_type_func=lambda x: x):
            if element.attrib.has_key(xml_attribute_name):
                setattr(django_model_instance, attribute_name,
                        attribute_type_func(element.attrib[xml_attribute_name]))

        integer = lambda x: int(x)
        int_or_none = lambda x: None if str(x).lower() == 'none' else int(x)
        boolean = lambda x: True if str(x).lower() in ('true', '1') else False

        def add_string_from_child(element, tag_name, django_model_instance,
                                  attribute_name):
            child_element = element.find(tag_name)
            if child_element is not None:
                text = u'' if child_element.text is None else child_element.text.strip()
                setattr(django_model_instance, attribute_name, text)

        namespace_prefix = '{%s}' % self.__class__.xml_namespace

        raw_text = xml_data.encode('utf-8')

        exam = elementtree.fromstring(raw_text)
        assert exam.tag == namespace_prefix + 'exam'
        assert exam.attrib.has_key('id')
        new_exam = self.my_django_model.objects.create(name=exam.attrib['id'])
        exam.attrib['pk'] = str(new_exam.pk)
        add_attribute(exam, 'title', new_exam, 'title')
        add_attribute(exam, 'passing_score', new_exam, 'passing_score', int_or_none)
        add_attribute(exam, 'version_id', new_exam, 'version_id', integer)
        add_attribute(exam, 'version_label', new_exam, 'version_label')
        add_attribute(exam, 'version_comment', new_exam, 'version_comment')
        new_exam.save()

        # question pools
        for qp in exam.getiterator(namespace_prefix + 'question_pool'):
            new_qp = facade.models.QuestionPool.objects.create(
                name=qp.attrib.get('id', None), exam=new_exam,
                title=qp.attrib.get('title', None),
                randomize_questions=qp.attrib.get('randomize_questions', False))
            qp.attrib['pk'] = str(new_qp.pk)

            # questions within a question pool
            for q in qp.getiterator(namespace_prefix + 'question'):
                new_q = facade.models.Question.objects.create(
                    name=q.attrib.get('id', None), question_pool=new_qp,
                    question_type=q.attrib['type'])
                q.attrib['pk'] = str(new_q.pk)

                for aname, atype in [('min_answers', int), ('max_answers', int_or_none),
                    ('text_response', boolean), ('min_length', int), ('max_length', int),
                    ('text_regex', str), ('min_value', Decimal), ('max_value', Decimal),
                    ('widget', str), ('required', boolean)]:
                    add_attribute(q, aname, new_q, aname, atype)

                for tag in ('label', 'help_text', 'rejoinder', 'text_response_label'):
                    add_string_from_child(q, namespace_prefix + tag, new_q, tag)

                new_q.save()

                # answers
                for a in q.getiterator(namespace_prefix + 'answer'):
                    new_answer = facade.models.Answer.objects.create(
                        name=a.attrib.get('id', None), question=new_q)
                    a.attrib['pk'] = str(new_answer.pk)

                    for aname, atype in [('text_response', boolean), ('value', str),
                        ('correct', boolean), ('end_question_pool', boolean),
                        ('end_exam', boolean)]:
                        add_attribute(a, aname, new_answer, aname, atype)

                    add_string_from_child(a, namespace_prefix + 'label', new_answer, 'label')

                    new_answer.save()

        # question pools
        for qp in exam.getiterator(namespace_prefix + 'question_pool'):
            # Update the next_question_pool foreign key for question pools that
            # specify it.
            next_qp_name = qp.attrib.get('next_question_pool', None)
            if next_qp_name:
                next_qp = new_exam.question_pools.get(name=next_qp_name)
                question_pool = facade.models.QuestionPool.objects.get(pk=qp.attrib['pk'])
                question_pool.next_question_pool = next_qp
                question_pool.save()
            # questions within a question pool
            for q in qp.getiterator(namespace_prefix + 'question'):
                # answers
                for a in q.getiterator(namespace_prefix + 'answer'):
                    # Update the next_question_pool foreign key for answers that
                    # specify it.
                    next_qp_name = a.attrib.get('next_question_pool', None)
                    if next_qp_name:
                        next_qp = new_exam.question_pools.get(name=next_qp_name)
                        answer = facade.models.Answer.objects.get(pk=a.attrib['pk'])
                        answer.next_question_pool = next_qp
                        answer.save()

        return new_exam

    @service_method
    def export_to_xml(self, auth_token, exam_id, include_pk=False):
        """
        Create an XML document representing an exam that is already stored in the
        database.
        
        :param auth_token:  The authentication token of the acting user
        :type auth_token:   pr_services.models.AuthToken
        :param exam_id:     primary key of the exam
        :type exam_id:      int
        :param include_pk:  include 'pk' attribute in exported XML
        :type include_pk:   bool

        :return:            a string containing an XML document that represents the given exam
        :rtype:             unicode
        """

        exam_obj = self._find_by_id(exam_id, self.my_django_model)

        def add_attribute(xml_element, xml_attribute_name, django_object,
                          attribute_name, attribute_type_func=None):
            if attribute_type_func is None:
                attribute_type_func = lambda x: unicode(x) if x not in ('', None) else None
            value = getattr(django_object, attribute_name)
            value = attribute_type_func(value)
            if value is not None:
                xml_element.attrib[xml_attribute_name] = value

        nullboolean = lambda x: unicode(bool(x)).lower() if x is not None else None
        boolean = lambda x: u'true' if str(x).lower() in ('true', '1') else u'false'
        int_or_none = lambda x: unicode(x) if x not in ('', None) else 'none'

        def add_subelement(xml_element, xml_subelement_tag, django_object,
                           attribute_name):
            value = getattr(django_object, attribute_name)
            if value not in ('', None):
                subelement = elementtree.SubElement(xml_element, xml_subelement_tag)
                subelement.text = value

        namespace_prefix = '{%s}' % self.__class__.xml_namespace
        exam = elementtree.Element(namespace_prefix + 'exam')
        if include_pk:
            add_attribute(exam, 'pk', exam_obj, 'id')
        add_attribute(exam, 'id', exam_obj, 'name')
        add_attribute(exam, 'title', exam_obj, 'title')
        add_attribute(exam, 'passing_score', exam_obj, 'passing_score')
        add_attribute(exam, 'version_id', exam_obj, 'version_id')
        add_attribute(exam, 'version_label', exam_obj, 'version_label')
        add_attribute(exam, 'version_comment', exam_obj, 'version_comment')

        for qp_obj in exam_obj.question_pools.all():
            qp = elementtree.SubElement(exam, namespace_prefix + 'question_pool')
            if include_pk:
                add_attribute(qp, 'pk', qp_obj, 'id')
            add_attribute(qp, 'id', qp_obj, 'name')
            add_attribute(qp, 'title', qp_obj, 'title')
            add_attribute(qp, 'randomize_questions', qp_obj, 'randomize_questions')

            if qp_obj.next_question_pool:
                qp.attrib['next_question_pool'] = qp_obj.next_question_pool.name

            for q_obj in qp_obj.questions.all():
                q = elementtree.SubElement(qp, namespace_prefix + 'question')
                if include_pk:
                    add_attribute(q, 'pk', q_obj, 'id')
                add_attribute(q, 'id', q_obj, 'name')
                add_attribute(q, 'type', q_obj, 'question_type')

                for aname, atype in [('min_answers', None), ('max_answers', int_or_none),
                    ('text_response', boolean), ('min_length', None), ('max_length', None),
                    ('text_regex', None), ('min_value', None), ('max_value', None),
                    ('widget', None), ('required', boolean)]:
                    add_attribute(q, aname, q_obj, aname, atype)

                for tag in ('label', 'help_text', 'rejoinder', 'text_response_label'):
                    add_subelement(q, namespace_prefix + tag, q_obj, tag)

                for a_obj in q_obj.answers.all():
                    a = elementtree.SubElement(q, namespace_prefix + 'answer')
                    if include_pk:
                        add_attribute(a, 'pk', a_obj, 'id')
                    add_attribute(a, 'id', a_obj, 'name')
                    
                    for aname, atype in [('text_response', boolean), ('value', None),
                        ('correct', nullboolean), ('end_question_pool', boolean),
                        ('end_exam', boolean)]:
                        add_attribute(a, aname, a_obj, aname, atype)

                    add_subelement(a, namespace_prefix + 'label', a_obj, 'label')

                    if a_obj.next_question_pool:
                        a.attrib['next_question_pool'] = a_obj.next_question_pool.name

        # pretty-print the XML, and send back a unicode object from it
        out_raw = StringIO()
        out = codecs.getwriter('utf-8')(out_raw)
        raw_xml_string = elementtree.tostring(exam, 'UTF-8')
        dom = xml.dom.minidom.parseString(raw_xml_string)
        print >> out, '<?xml version="1.0" encoding="UTF-8"?>'
        dom.documentElement.writexml(out, '', '    ', '\n')
        return out_raw.getvalue().decode('utf-8')

# vim:tabstop=4 shiftwidth=4 expandtab
