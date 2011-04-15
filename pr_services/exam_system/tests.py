"""
Non-RPC unit tests for Power Reg exam system.
"""

__docformat__ = "restructuredtext en"

# Python
import codecs
from decimal import Decimal
import random

# Django
from django.conf import settings

# PowerReg
from pr_services import exceptions
from pr_services import pr_tests
import facade

_default = object() # dummy object used as default for optional keyword args.

class TestExamModels(pr_tests.TestCase):
    """Test behavior of exam system models."""

    def _create_any(self, model_class, **kwargs):
        """Helper method to create an instance and verify the attributes."""
        instance = model_class.objects.create(**kwargs)
        for k,v in kwargs.items():
            if k == 'name' and isinstance(instance, facade.models.Exam) and v == '':
                continue
            self.assertEquals(getattr(instance, k), v)
        return instance

    def _create_exam(self, **kwargs):
        """Helper method to create an exam."""
        return self._create_any(facade.models.Exam, **kwargs)

    def _create_question_pool(self, exam, **kwargs):
        """Helper method to create a question pool."""
        return self._create_any(facade.models.QuestionPool, exam=exam, **kwargs)

    def _create_question(self, question_pool, question_type, **kwargs):
        """Helper method to create a question."""
        return self._create_any(facade.models.Question,
            question_pool=question_pool, question_type=question_type, **kwargs)

    def _create_answer(self, question, **kwargs):
        """Helper method to create an answer."""
        if 'value' in kwargs and kwargs['value'] is not None:
            kwargs['value'] = str(kwargs['value'])
        return self._create_any(facade.models.Answer, question=question, **kwargs)

    def _create_exam_session(self, assignment, **kwargs):
        """Helper method to create an exam session."""
        return self._create_any(facade.models.ExamSession,
            assignment=assignment, **kwargs)

    def _create_response(self, **kwargs):
        """Helper method to create a response."""
        return self._create_any(facade.models.Response, **kwargs)

    def test_exam(self):
        #"""Test validation for creating/saving an exam."""

        # Create an exam with valid options.
        exam = self._create_exam(name='my_exam', title='My Exam',
                                 passing_score=90)

        # Create an exam with invalid options.
        self.assertRaises(facade.models.ModelDataValidationError,
            self._create_exam, name='my_exam')
        self._create_exam(name='my_exam', version_id=1, version_label='1.0',
            title='My Exam', passing_score=90)
        self.assertRaises(facade.models.ModelDataValidationError,
            self._create_exam, name='test_exam', passing_score=-1)
        self.assertRaises(facade.models.ModelDataValidationError,
            self._create_exam, name='test_exam_2', passing_score=101)

    def test_order_field(self):
        #"""Test creating an exam with question pools, questions and answers."""

        # Create an exam.
        exam = self._create_exam(name='my_exam', title='My Exam',
                                 passing_score=90)

        # Create a question pool.
        qp1 = self._create_question_pool(exam, title='First Section')
        self.assertEquals(qp1.order, 0)

        # Create a char question in the pool.
        q1_1 = self._create_question(qp1, question_type='char',
                                     label='What up homey?', required=True,
                                     help_text='Just say what up',
                                     rejoinder='You didn\'t say what up')
        self.assertEquals(q1_1.order, 0)

        # Create another question pool.
        qp2 = self._create_question_pool(exam, title='Second Section')
        self.assertEquals(qp2.order, 1)

        # Create a rating question in the pool.
        q2_1 = self._create_question(qp2, question_type='rating',
                                     label='Pick a digit, k?',
                                     text_response=True, min_value=1,
                                     max_value=10)
        self.assertEquals(q2_1.order, 0)

        # Create a choice question in the pool and some answers.
        q2_2 = self._create_question(qp2, question_type='choice',
                                     label='How are you?', text_response=True)
        self.assertEquals(q2_2.order, 1)
        q2_2_a1 = self._create_answer(q2_2, label='Fine')
        self.assertEquals(q2_2_a1.order, 0)
        q2_2_a2 = self._create_answer(q2_2, label='Good')
        self.assertEquals(q2_2_a2.order, 1)
        q2_2_a3 = self._create_answer(q2_2, label='OK')
        self.assertEquals(q2_2_a3.order, 2)

        # Update the order of the answers.  Note: we have to check in a way that
        # executes a query, since the in-memory objects created earlier will not
        # see the update to the order field.
        q2_2_a3.order = 1
        q2_2_a3.save()
        self.assertEquals(q2_2.answers.get(id=q2_2_a1.id).order, 0)
        self.assertEquals(q2_2.answers.get(id=q2_2_a2.id).order, 2)
        self.assertEquals(q2_2.answers.get(id=q2_2_a3.id).order, 1)

        # Update the order to move this question to the beginning of pool.
        q2_2.order = 0
        q2_2.save()
        self.assertEquals(qp2.questions.get(id=q2_1.id).order, 1)
        self.assertEquals(qp2.questions.get(id=q2_2.id).order, 0)

        # Update the order to make this question pool first in the exam.
        qp2.order = 0
        qp2.save()
        self.assertEquals(exam.question_pools.get(id=qp1.id).order, 1)
        self.assertEquals(exam.question_pools.get(id=qp2.id).order, 0)

        # Check the default ordering of question pools.
        for x, y in zip((qp2, qp1), exam.question_pools.all()):
            self.assertEquals(x, y)
        
        # Check the default ordering of questions in a pool.
        for x, y in zip((q2_2, q2_1), qp2.questions.all()):
            self.assertEquals(x, y)

        # Check the default ordering of answers for a question.
        for x, y in zip((q2_2_a1, q2_2_a3, q2_2_a2), q2_2.answers.all()):
            self.assertEquals(x, y)

    def test_create_questions(self):
        #"""Test logic for creating questions of all supported types."""

        # Create an initial exam and question pool.
        exam = self._create_exam(name='exam_exam', title='The Exam Exam')
        qp = self._create_question_pool(exam, title='Lots of Questions')

        def create_q(qtype, *args, **kwargs):
            """Helper to create questions for this test."""
            if 'label' not in kwargs:
                kwargs['label'] = 'What is the answer?'
            return self._create_question(qp, qtype, *args, **kwargs)

        # Create bool questions.
        q = create_q('bool', label='Do you like tests?')
        self.assertEquals(q.widget, 'CheckboxInput')
        create_q('bool', widget='RadioSelect')
        create_q('bool', widget='Select')
        self.assertRaises(facade.models.ModelDataValidationError, create_q,
            'bool', widget='Textarea')

        # Create char/text questions.
        for qt in ('char', 'text'):
            q = create_q(qt, label='Why?')
            self.assertEquals(q.text_response, False)
            if qt == 'char':
                self.assertEquals(q.widget, 'TextInput')
                create_q(qt, widget='Textarea')
            elif qt == 'text':
                self.assertEquals(q.widget, 'Textarea')
                create_q(qt, widget='TextInput')
            self.assertRaises(facade.models.ModelDataValidationError, create_q,
                qt, widget='RadioSelect')
            create_q(qt, min_length=2)
            create_q(qt, min_length=2, max_length=10)
            self.assertRaises(facade.models.ModelDataValidationError, create_q,
                qt, min_length=2, max_length=1)
            create_q(qt, text_regex=r'^[A-Za-z0-9]*$')
            self.assertRaises(facade.models.ModelDataValidationError, create_q,
                qt, text_regex=r'..?*')

        # Create choice questions.
        q = create_q('choice', label='What would be worse?')
        self.assertEquals(q.widget, 'Select')
        create_q('choice', widget='CheckboxSelectMultiple')
        create_q('choice', widget='RadioSelect')
        self.assertRaises(facade.models.ModelDataValidationError, create_q,
                          'choice', widget='Textarea')
        create_q('choice', min_answers=2, max_answers=2)
        create_q('choice', min_answers=2, max_answers=4)
        self.assertRaises(facade.models.ModelDataValidationError, create_q,
                          'choice', min_answers=2, max_answers=1)
        self.assertRaises(facade.models.ModelDataValidationError, create_q,
                          'choice', max_answers=0)

        # Create date/datetime/time questions.
        for qt in ('date', 'datetime', 'time'):
            q = create_q(qt, label='When?')
            if qt == 'date':
                self.assertEquals(q.widget, 'DateInput')
            elif qt == 'datetime':
                self.assertEquals(q.widget, 'DateTimeInput')
            elif qt == 'time':
                self.assertEquals(q.widget, 'TimeInput')
            create_q(qt, widget='TextInput')
            self.assertRaises(facade.models.ModelDataValidationError, create_q,
                qt, widget='Textarea')

        # Create decimal/float/int questions.
        for qt in ('decimal', 'float', 'int'):
            q = create_q(qt, label='How much?')
            self.assertEquals(q.widget, 'TextInput')
            create_q(qt, widget='Select')
            create_q(qt, min_value=-273)
            create_q(qt, max_value=100)
            create_q(qt, min_value=-100, max_value=100)
            self.assertRaises(facade.models.ModelDataValidationError, create_q,
                qt, min_value=10, max_value=0)

        # Create rating questions.
        q = create_q('rating', label='What did ya think?')
        self.assertEquals(q.widget, 'RadioSelect')
        create_q('rating', widget='Select')
        self.assertRaises(facade.models.ModelDataValidationError, create_q,
                          'rating', widget='Textarea')
        create_q('rating', min_value=0)
        create_q('rating', max_value=100)
        create_q('rating', min_value=0, max_value=100)
        self.assertRaises(facade.models.ModelDataValidationError, create_q,
                          'rating', min_value=-100)
        self.assertRaises(facade.models.ModelDataValidationError, create_q,
                          'rating', min_value=10, max_value=0)

    def test_create_answers(self):
        #"""Test various options for creating answers to a question."""
        
        # Create initial exams, question pools and questions.
        e1 = self._create_exam(name='e1', title='The Exam Answers')
        e1_qp1 = self._create_question_pool(e1, title='Questions-R-Us')
        e1_qp2 = self._create_question_pool(e1, title='Questions-R-Us 2')
        e1_qp3 = self._create_question_pool(e1, title='Questions-R-Us 3')
        e1_q1 = self._create_question(e1_qp2, 'choice',
                                      label='Which door will you choose?')
        e2 = self._create_exam(name='e2', title='The Exam Answers 2')
        e2_qp1 = self._create_question_pool(e2, title='No Questions Here')

        # Create some answers.
        a1 = self._create_answer(e1_q1, label='Door #1', end_question_pool=True)
        a2 = self._create_answer(e1_q1, label='Door #2', correct=True)
        a3 = self._create_answer(e1_q1, label='Door #3', end_exam=True)

        # Test next_question_pool attribute.
        a1.next_question_pool = e1_qp1
        self.assertRaises(facade.models.ModelDataValidationError, a1.save)
        a1.next_question_pool = e1_qp2
        self.assertRaises(facade.models.ModelDataValidationError, a1.save)
        a1.next_question_pool = e2_qp1
        self.assertRaises(facade.models.ModelDataValidationError, a1.save)
        a1.next_question_pool = e1_qp3
        a1.save()
        
        # Test validation of exam and all questions and answers.
        e1.validate(related=True)

    def _take_exam(self, auth_token, assignment_id, answer_key, score=None, passed=None):
        """
        Take the exam using the given answer key and verify the score.
        
        :param auth_token: auth token for the current user
        :type auth_token: facade.models.AuthToken
        :param assignment_id: primary key of the assigment of the user to the exam
        :type assignment_id: int
        :param answer_key: answer key to the exam
        :type answer_key: dict
        :param score: [OUT] output parameter for the exam score if passed as None
        :type score: None (if any other type will not be modified)
        :param passed: [OUT] output parameter for whether the exam was passed if passed in as None 
        :type passed: None (if any other type will not be modified)
        
        :returns: the exam session (also has two output parameters)
        :rtype: facade.models.ExamSession
        """

        # Create the exam session and answer the questions according to the
        # answer key.
        
        assignment = facade.models.Assignment.objects.get(id=assignment_id)
        exam_session = self._create_exam_session(assignment)
        next_questions = exam_session.get_next_questions()
        while next_questions:
            for question in next_questions:

                # Get the possible answer parameters from the answer key.
                answer = answer_key.get(question.id, None)
                if answer is None:
                    continue
                value = answer.get('value', None)
                if callable(value):
                    value = value()
                text = answer.get('text', None)
                valid = answer.get('valid', True)
                correct = answer.get('correct', True) if valid else None

                # Submit a response and verify the expected valid/correct flags.
                response = exam_session.submit_response(question, value, text)
                self.assertEquals(response.value, response._to_python(value))
                self.assertEquals(response.text, text)
                self.assertEquals(response.valid, valid)
                self.assertEquals(response.correct, correct)

            next_questions = exam_session.get_next_questions()

        self.exam_session_manager.finish(auth_token, exam_session.id)
        exam_session = facade.models.ExamSession.objects.get(id=exam_session.id)

        # Check the exam score and passed flag.
        my_score = exam_session.calculate_score()
        if my_score is not None:
            if score is None:
                score = exam.passing_score
            self.assertEquals(my_score, score)
            if passed is None:
                passed = my_score >= exam_session.exam.passing_score
            self.assertEquals(exam_session.passed, passed)
        else:
            self.assertEquals(exam_session.assignment.status, 'pending')

        return exam_session

    def test_exam_session(self):
        """Test basic exam session and response model functions.

        WARNING: This test always fails when using sqlite3 databases.

        """
        # First create the exam for this test case.
        exam = self._create_exam(name='three', title='Do You Know Your Threes?',
                                 passing_score=75)
        qp1 = self._create_question_pool(exam, title='Math')
        # Create a bool question with a correct answer.
        q1 = self._create_question(qp1, 'bool', label='1 + 2 = 3?')
        q1_a1 = self._create_answer(q1, correct=True, value=True)
        # Create a char question with a correct answer.
        q2 = self._create_question(qp1, 'char', label='Spell "3"')
        q2_a1 = self._create_answer(q2, correct=True, value='three')
        qp2 = self._create_question_pool(exam, title='Stooges')
        # Create an int question with choices listed and a correct answer.
        q3 = self._create_question(qp2, 'int', label='Number of stooges?')
        q3_a1 = self._create_answer(q3, value=2, label='two')
        q3_a2 = self._create_answer(q3, value=3, correct=True, label='three')
        q3_a3 = self._create_answer(q3, value=4, label='four')
        # Create a question with choices not included in scoring.
        q4 = self._create_question(qp2, 'choice', label='Which one is your ' + \
                                   'favorite stooge?')
        q4_a1 = self._create_answer(q4, label='Larry')
        q4_a2 = self._create_answer(q4, label='Curly')
        q4_a3 = self._create_answer(q4, label='Moe')
        q4_a4 = self._create_answer(q4, label='None of the Above',
                                    text_response=True)
        qp3 = self._create_question_pool(exam, title='Mice')
        # Create a question
        q5 = self._create_question(qp3, 'int', label='How many blind mice?',
                                   help_text='Please enter the correct ' + \
                                             'number of visually impaired ' + \
                                             'rodents.')
        q5_a1 = self._create_answer(q5, value=3, correct=True)

        # Take the exam with all answers correct.
        answer_key = {
            q1.id: {'value': True},
            q2.id: {'value': 'three'},
            q3.id: {'value': 3},
            q4.id: {'value': lambda: random.choice(q4.answers.values_list( \
                                                   'id', flat=True)),
                    'correct': None},
            q5.id: {'value': 3}
        }

        student, student_at = self.create_student()
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        self._take_exam(student_at, assignment.id, answer_key, 100, True)

        # Now miss one question.
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        answer_key[q1.id].update({'value': False, 'correct': False})
        exam_session = self._take_exam(student_at, assignment.id, answer_key, 75, True)
        ret = self.exam_session_manager.get_filtered(student_at, {'exact' : {'id' : exam_session.id}}, ['score', 'number_correct', 'passed', 'passing_score'])
        self.assertEquals(len(ret), 1)
        self.assertEquals(Decimal(ret[0]['score']), Decimal('75.00'))
        self.assertEquals(ret[0]['passing_score'], 75)
        self.assertEquals(ret[0]['number_correct'], 3)
        self.assertEquals(ret[0]['passed'], True)

        # Now miss two questions.
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        answer_key[q2.id].update({'value': 'four', 'correct': False})
        exam_session = self._take_exam(student_at, assignment.id, answer_key, 50, False)
        ret = self.exam_session_manager.get_filtered(student_at, {'exact' : {'id' : exam_session.id}}, ['score', 'number_correct', 'passed', 'passing_score'])
        self.assertEquals(len(ret), 1)
        self.assertEquals(Decimal(ret[0]['score']), Decimal('50.00'))
        self.assertEquals(ret[0]['passing_score'], 75)
        self.assertEquals(ret[0]['number_correct'], 2)
        self.assertEquals(ret[0]['passed'], False)

        # Now miss three questions.
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        answer_key[q3.id].update({'value': 4, 'correct': False})
        self._take_exam(student_at, assignment.id, answer_key, 25, False)

        # Now miss four questions.
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        answer_key[q5.id].update({'value': 2, 'correct': False})
        es = self._take_exam(student_at, assignment.id, answer_key, 0, False)

        # For an exam with possible correct answers, we cannot submit a response
        # or calculate the score after the exam is completed.
        self.assertRaises(exceptions.ExamSessionAlreadyFinishedException,
                          self.exam_session_manager.add_response, student_at, es.id, q5.id, 3)

    def test_exam_session_survey(self):
        #"""Test an exam session when used for a survey or application."""
        # (No answers are labelled as correct or incorrect.)

        # First create the exam for this test case.
        exam = self._create_exam(name='favorites', title='What do you like?')
        qp1 = self._create_question_pool(exam, title='Numbers')
        # Create an int question.
        q1 = self._create_question(qp1, 'int',
                                   label='What is your lucky number?')
        # Create a bool question.
        q2 = self._create_question(qp1, 'bool',
                                   label='Is the number 13 unlucky?')
        qp2 = self._create_question_pool(exam, title='Colors')
        # Create a question with choices not included in scoring.
        q3 = self._create_question(qp2, 'choice',
                                   label='Which color is your favorite?')
        q3_a1 = self._create_answer(q3, value='red', label='Red')
        q3_a2 = self._create_answer(q3, value='green', label='Green')
        q3_a3 = self._create_answer(q3, value='blue', label='Blue')
        q3_a4 = self._create_answer(q3, value='other', label='Other',
                                    text_response=True)
        q4 = self._create_question(qp2, 'char',
                                   label='What is your least favorite color?')

        # Take the exam with some answers.
        answer_key = {
            q1.id: {'value': 13, 'correct': None},
            q2.id: {'value': False, 'correct': None},
            q3.id: {'value': q3_a4.id, 'text': 'orange', 'correct': None},
            q4.id: {'value': 'hot pink', 'correct': None},
        }

        student, student_at = self.create_student()
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        es = self._take_exam(student_at, assignment.id, answer_key)

        # We cannot submit another response, because the exam has been completed
        self.assertEquals(es.assignment.status, 'pending')
        self.assertRaises(exceptions.ExamSessionAlreadyFinishedException, es.submit_response, q4, 'carolina blue')

    def _create_eq(self, *args, **kwargs):
        """Create an exam with a single question for testing responses."""
        passing_score = kwargs.pop('passing_score', 100)
        name = 'one_q_' + hex(random.randint(0, 2**31-1))
        exam = self._create_exam(name=name, title='Single Question Exam',
                                 passing_score=passing_score)
        qp = self._create_question_pool(exam, title='THE Question')
        q = self._create_question(qp, *args, **kwargs)
        return exam, q

    def _test_question_responses(self, q_type, q_kw={}, q_extra_kw={},
                                 answers=[], invalid=[], valid=[], incorrect=[],
                                 correct=[], response_key='value'):
        """Test validation and correctness checks for given question type."""
        kwargs = dict(q_kw.items())
        kwargs.update(dict(q_extra_kw.items()))
        # Create the question with the given parameters.
        e, q = self._create_eq(q_type, **kwargs)
        # Create any answers required for this test.
        for a_kw in answers:
            self._create_answer(q, **a_kw)
        correct_answers = any(a_kw.get('correct', False) for a_kw in answers)
        # Create parameters for testing invalid, valid, incorrect and correct
        # response values.
        response_types = [
            # (value list, answer key params, score)
            (invalid, {'valid': False}, 0 if correct_answers else None),
            (valid, {'valid': True, 'correct': None}, None),
            (incorrect, {'correct': False}, 0),
            (correct, {'correct': True}, 100),
        ]
        # Take the exam for each value for each response type.
        student, student_at = self.create_student()
        for rt in response_types:
            for v in rt[0]:
                ak = {q.id: {response_key: v}}
                ak[q.id].update(rt[1])
                assignment = self.assignment_manager.create(self.admin_token, e.id, student.id)
                self._take_exam(student_at, assignment.id, ak, rt[2])

    def _test_response_options(self, q_type, q_kw={}, test_cases=[], **kwargs):
        """
        Run response option tests using a test case array.
        
        :param q_type: question type
        :type q_type: string
        :param q_kw: keyword arguments to pass to facade.models.Question.objects.create()
        :type q_kw: dict
        :param test_cases: array of data about tests to perform, see below
        :type test_cases: list
        :param **kwargs: these will be passed to self._test_quesetion_responses()
        :type **kwargs: variable keyword argument list
        
        Takes a test case array similar to the following:
        [
            (
                {}, # Additional question keyword arguments.
                [], # List of answer dictionaries.
                [], # Invalid values.
                [], # Valid values, cannot determine if correct.
                [], # Incorrect values.
                []. # Correct values.
            ),
        ]
        """

        for tc in test_cases:
            self._test_question_responses(q_type, q_kw, *tc, **kwargs)

    def test_response_types(self):
        #"""Test response handling for all supported response types. This one takes for frickin ever."""

        # Test bool response.
        bool_null_values = [None, 'none', 'null', 'nil']
        bool_true_values = [True, 1, '1', 'true', 't', 'yes', 'y']
        bool_false_values = [False, 0, '0', 'false', 'f', 'no', 'n']
        bool_test_cases = [
            (   # Test a simple bool question with no answers.
                {},
                [],
                bool_null_values,
                bool_true_values + bool_false_values,
            ),
            (   # Test a simple bool question with an answer.
                {},
                [{'value': True, 'correct': True}],
                bool_null_values,
                [],
                bool_false_values,
                bool_true_values,
            ),
            (   # Test an optional bool question with no answers.
                {'required': False},
                [],
                [],
                bool_null_values + bool_true_values + bool_false_values,
            ),
            (   # Test an optional bool question with an answer.
                {'required': False},
                [{'value': False, 'correct': True}],
                [],
                [],
                bool_null_values + bool_true_values,
                bool_false_values,
            ),
        ]
        self._test_response_options('bool', {}, bool_test_cases)

        # Test choice response.
        choice_test_cases = [
            # FIXME
        ]
        self._test_response_options('choice', {}, choice_test_cases)

        # Test date response.
        date_test_cases = [
            (   # Test a simple date question with no answers.
                {},
                [],
                [None],
                ['2009-12-23'],
            ),
            # FIXME
        ]
        self._test_response_options('date', {}, date_test_cases)

        # Test datetime response.
        datetime_test_cases = [
            (   # Test a simple datetime question with no answers.
                {},
                [],
                [None],
                ['2009-12-23 01:23:45'],
            ),
            # FIXME
        ]
        self._test_response_options('datetime', {}, datetime_test_cases)

        # Common test cases for numeric responses.
        numeric_test_cases = [
            (   # Test a simple numeric question with no answers.
                {},
                [],
                [None],
                [0],
            ),
            # FIXME
        ]
        
        # Test decimal response.
        decimal_test_cases = numeric_test_cases + [
            # FIXME
        ]
        self._test_response_options('decimal', {}, decimal_test_cases)

        # Test float response.
        float_test_cases = numeric_test_cases + [
            # FIXME
        ]
        self._test_response_options('float', {}, float_test_cases)

        # Test int response.
        int_test_cases = numeric_test_cases + [
            # FIXME
        ]
        self._test_response_options('int', {}, int_test_cases)

        # Test rating response.
        rating_test_cases = numeric_test_cases + [
            # FIXME
        ]
        self._test_response_options('rating', {}, rating_test_cases)

        # Test time response.
        time_test_cases = [
            (   # Test a simple time question with no answers.
                {},
                [],
                [None],
                ['01:23:45'],
            ),
            # FIXME
        ]
        self._test_response_options('time', {}, time_test_cases)

        # Test any field with a free-text response.  We should validate the
        # free text response against the min_length, max_length and text_regex
        # parameters.
        text_response_test_cases = [
            (   # Test a basic text response with no extra validation.
                {},
                [],
                [],
                [None, '', 'this is some text'],
            ),
            (   # Test min_length validation.
                {'min_length': 2},
                [],
                [None, '', 'x'],
                ['xy', 'xyz'],
            ),
            (   # Test max_length validation.
                {'max_length': 10},
                [],
                ['1234567890A', 'X'*255],
                [None, '', 'x', '1234567890'],
            ),
            (   # Test regular expression validation.
                {'text_regex': r'^[A-Za-z]+$'},
                [],
                [None, '', '1', 'A1'],
                ['X', 'XYZ'],
            ),
        ]
        for qt in ('bool', 'date', 'datetime', 'decimal', 'float', 'int',
                   'rating', 'time'):
            self._test_response_options(qt, {'required': False,
                                             'text_response': True},
                                        text_response_test_cases,
                                        response_key='text')
            
        # Test responses that are simply text fields.
        text_test_cases = [
            # FIXME
        ]
        for qt in ('char', 'text'):
            self._test_response_options(qt, {'required': False},
                                        text_response_test_cases)
            self._test_response_options(qt, {}, text_test_cases)

class TestExamManagers(pr_tests.TestCase):
    
    def setUp(self):
        super(TestExamManagers, self).setUp()
        if not hasattr(self, 'exam_manager'):
            self.exam_manager = facade.managers.ExamManager()
        if not hasattr(self, 'question_pool_manager'):
            self.question_pool_manager = facade.managers.QuestionPoolManager()
        if not hasattr(self, 'question_manager'):
            self.question_manager = facade.managers.QuestionManager()
        if not hasattr(self, 'answer_manager'):
            self.answer_manager = facade.managers.AnswerManager()
        if not hasattr(self, 'exam_session_manager'):
            self.exam_session_manager = facade.managers.ExamSessionManager()
        if not hasattr(self, 'response_manager'):
            self.response_manager = facade.managers.ResponseManager()
        if not hasattr(self, 'form_page_manager'):
            self.form_page_manager = facade.managers.FormPageManager()
        if not hasattr(self, 'form_widget_manager'):
            self.form_widget_manager = facade.managers.FormWidgetManager()

    def _create_exam(self, name=None, title=None, opts=None, **kwargs):
        name = name or kwargs.pop('name')
        title = title or kwargs.pop('title')
        opts = opts or {}
        opts.update(kwargs)
        return self.exam_manager.create(self.admin_token, name, title, opts)

    def _create_question_pool(self, exam=None, title=None, opts=None, **kwargs):
        exam = exam or kwargs.pop('exam')
        exam = getattr(exam, 'pk', exam)
        title = title or kwargs.pop('title')
        opts = opts or {}
        opts.update(kwargs)
        return self.question_pool_manager.create(self.admin_token, exam, title,
                                                 opts)

    def _create_question(self, question_pool=None, question_type=None,
                         label=None, opts=None, **kwargs):
        question_pool = question_pool or kwargs.pop('question_pool')
        question_pool = getattr(question_pool, 'pk', question_pool)
        question_type = question_type or kwargs.pop('question_type')
        label = label or kwargs.pop('label')
        opts = opts or {}
        opts.update(kwargs)
        return self.question_manager.create(self.admin_token, question_pool,
                                            question_type, label, opts)

    def _create_answer(self, question=None, label=None, opts=None, **kwargs):
        question = question or kwargs.pop('question')
        question = getattr(question, 'pk', question)
        label = label or kwargs.pop('label', None)
        opts = opts or {}
        opts.update(kwargs)
        return self.answer_manager.create(self.admin_token, question, label,
                                          opts)

    def test_exam_creation_managers(self):
        e = self._create_exam('mother_exam', 'The Mother of All Exams',
                              passing_score=90)
        qp = self._create_question_pool(e, "Mama's Question Pool")
        q = self._create_question(qp, 'bool', 'Is mama always right?')
        a = self._create_answer(q, 'Yes', correct=True)
        a = self._create_answer(q, 'No')

    def _take_exam(self, auth_token, assignment, answer_key, score=_default, passed=_default,
                   resume=False):
        """
        Take the exam using the given answer key and verify the score.
        
        :param auth_token: auth token for the acting user
        :type auth_token: facade.models.AuthToken
        :param assignment: the assignment to the exam for the actor
        :type assignment: facade.models.Assignment
        :param answer_key: the answers to the questions (format??)
        :type answer_key: dict
        :param score: [OUT or in] if passed in as _default, will be set to the score of the exam session.
                      If not passed in as _default, the exam score will be asserted equal to this.
        :type score: bool or object (_default) (this module has a _default variable defined)
        :param passed: [OUT or IN] if passed in as _default, will be set to whether the score was
                       sufficiently high to pass the exam.  If not passed in as _default, whether
                       the exam is passed will be asserted equal to this.
        :type passed: bool or object (_default) (this modules has a _default variable defined)
        :param resume: whether to resume any suitable existing exam sessions
        :type resume: bool
        """

        # Create the exam session and answer the questions according to the
        # answer key.
        result = self.exam_session_manager.create(auth_token, assignment.id,
                                                  True, resume)
        if isinstance(result, dict):
            exam_session_id = result['id']
            next_questions = result
        else:
            exam_session_id = result.id
            next_questions = None

        # Iterate over question pools and questions.
        while next_questions:
            for k in ('id', 'title', 'question_pools'):
                self.assertTrue(k in next_questions)
            for question_pool in next_questions['question_pools']:
                for k in ('id', 'title', 'questions'):
                    self.assertTrue(k in question_pool)
                for question in question_pool['questions']:
                    for k in ('id', 'label'):
                        self.assertTrue(k in question)

                    # Get the possible answer parameters from the answer key.
                    answer = answer_key.get(question['id'], None)
                    if answer is None:
                        continue
                    value = answer.get('value', None)
                    if callable(value):
                        value = value()
                    text = answer.get('text', None)
                    valid = answer.get('valid', True)
                    correct = answer.get('correct', True) if valid else None

                    # Submit a response and verify the expected valid/correct
                    # flags.
                    response = self.exam_session_manager.add_response(\
                        auth_token, exam_session_id, question['id'],
                        {'value': value, 'text': text})
                    # FIXME
                    #self.assertEquals(response['value'], response._to_python(value))
                    #self.assertEquals(response.get('text', None), text)
                    #self.assertEquals(response.get('valid', None), valid)
                    #self.assertEquals(response.get('correct', None), correct)

            result = self.exam_session_manager.finish(auth_token,
                                                      exam_session_id)
            if result.get('question_pools', []):
                next_questions = result
            else:
                next_questions = None

        # Check the exam score and passed flag.
        if 'score' in result:
            if score is _default:
                score = exam.passing_score
            self.assertEquals(result['score'], score)
            if passed is _default:
                passed = result['score'] >= exam.passing_score
            self.assertEquals(result['passed'], passed)

        # Check the exam score and passed flag returned from get_results.
        result = self.exam_session_manager.get_results(self.admin_token,
                                                       exam_session_id)
        if score is _default:
            score = exam.passing_score
        if score is None:
            self.assertEquals(result['score'], score)
        else:
            self.assertEquals(Decimal(result['score']), Decimal(score))
        if passed is _default:
            passed = Decimal(result['score']) >= Decimal(exam.passing_score)
        self.assertEquals(result['passed'], passed)
        # FIXME: Actually check the questions returned in these lists.
        self.assertTrue('missed_questions' in result)
        self.assertTrue('invalid_questions' in result)
        return exam_session_id

    def test_exam_manager_xml(self):
        # import a new exam
        xml_data = codecs.open('pr_services/test_data/complex_exam.xml', 'r',
                               encoding='utf-8').read()
        exam = self.exam_manager.create_from_xml(u'', xml_data)
        qs = facade.models.Answer.objects.all()
        qs = qs.filter(question__question_pool__exam=exam)
        qs = qs.filter(next_question_pool__isnull=False)
        self.assertTrue(qs.count() > 0)
        for a in qs:
            qs2 = facade.models.QuestionPool.objects.all()
            self.assertEquals(qs2.filter(randomize_questions=True).count(), 1)
            qs2 = qs2.filter(exam=exam)
            qs2 = qs2.filter(pk=a.next_question_pool.pk)
            self.assertEquals(qs2.count(), 1)
        new_xml_data = self.exam_manager.export_to_xml(u'', exam.id)

        # Now rename the original exam, import the xml and export again, then
        # check to see if the XML matches.
        exam.name = 'renamed_exam'
        exam.save()
        new_exam = self.exam_manager.create_from_xml(u'', new_xml_data)
        new_xml_data2 = self.exam_manager.export_to_xml(u'', new_exam.id)
        self.assertEquals(new_xml_data, new_xml_data2)

        # Try one other exam with correct answers listed.
        xml_data = codecs.open('pr_services/test_data/instructor_exam.xml', 'r',
                               encoding='utf-8').read()
        exam = self.exam_manager.create_from_xml(u'', xml_data)
        new_xml_data = self.exam_manager.export_to_xml(u'', exam.id)

    def test_form_managers(self):
        exam = self._create_exam(name='seven', title='Do You Know Your Sevens?',
                                 passing_score=75)
        form_page = self.form_page_manager.create(self.admin_token, exam.id, 1)
        qp1 = self._create_question_pool(exam, title='Math')
        # Create a bool question with a correct answer.
        q1 = self._create_question(qp1, 'bool', label='3 + 4 = 7?')
        q1_a1 = self._create_answer(q1, correct=True, value=True)
        fw1 = self.form_widget_manager.create(self.admin_token, form_page.id, 24, 180, 17, 41, q1.id)


        q4 = self._create_question(qp1, 'choice', label='Which one is your ' + \
                                   'favorite dwarf?')
        q4_a1 = self._create_answer(q4, label='Dopey')
        q4_a2 = self._create_answer(q4, label='Grumpy')
        q4_a3 = self._create_answer(q4, label='Doc')
        q4_a4 = self._create_answer(q4, label='Happy')
        q4_a5 = self._create_answer(q4, label='Bashful')
        q4_a6 = self._create_answer(q4, label='Sneezy')
        q4_a7 = self._create_answer(q4, label='Sleepy')
        q4_a8 = self._create_answer(q4, label='None of the Above', text_response=False)
        fw4 = self.form_widget_manager.create(self.admin_token, form_page.id, 24, 24, 100, 16, q4.id, q4_a1.id)
        fw4 = self.form_widget_manager.create(self.admin_token, form_page.id, 24, 24, 100, 32, q4.id, q4_a2.id)
        fw4 = self.form_widget_manager.create(self.admin_token, form_page.id, 24, 24, 100, 48, q4.id, q4_a3.id)
        fw4 = self.form_widget_manager.create(self.admin_token, form_page.id, 24, 24, 100, 64, q4.id, q4_a4.id)

    def test_question_randomization(self):
        exam = self._create_exam(name='demo_exam', title='Demo Exam 1')
        qp1 = self._create_question_pool(exam, title='Math')
        q1 = self._create_question(qp1, 'bool', label='q1')
        q2 = self._create_question(qp1, 'bool', label='q2')
        q3 = self._create_question(qp1, 'bool', label='q3')
        q4 = self._create_question(qp1, 'bool', label='q4')

        student, student_at = self.create_student()
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)

        # make sure the order is correct
        exam_session = self.exam_session_manager.create(student_at, assignment.id,
                                                      fetch_all=False, resume=False)
        next_questions = exam_session.get_next_questions()
        default_order = ['q1', 'q2', 'q3', 'q4']
        self.assertEquals(default_order, [q.label for q in next_questions])

        # Now let's try to randomize the order
        qp1.randomize_questions = True
        qp1.save()

        # try this several times, in case the random order happens to be the
        # same as the default order
        reps = 10
        for x in xrange(reps):
            assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
            exam_session = self.exam_session_manager.create(student_at, assignment.id,
                                                            fetch_all=False, resume=False)
            next_questions = exam_session.get_next_questions()
            try:
                self.assertTrue(default_order != [q.label for q in next_questions])
                break
            except AssertionError:
                if x >= reps - 1:
                    raise

        # now let's try limiting the number of questions that get asked
        qp1.number_to_answer = 3
        qp1.save()
        
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        exam_session = self.exam_session_manager.create(self.admin_token, assignment.id,
                                                      fetch_all=False, resume=False)
        next_questions = exam_session.get_next_questions()
        self.assertEquals(len(next_questions), 3)

    def test_exam_session_manager(self):

        # First create the exam for this test case.
        exam = self._create_exam(name='seven', title='Do You Know Your Sevens?',
                                 passing_score=75)
        qp1 = self._create_question_pool(exam, title='Math')
        # Create a bool question with a correct answer.
        q1 = self._create_question(qp1, 'bool', label='3 + 4 = 7?')
        q1_a1 = self._create_answer(q1, correct=True, value=True)
        # Create a char question with a correct answer.
        q2 = self._create_question(qp1, 'char', label='Spell "7"')
        q2_a1 = self._create_answer(q2, correct=True, value='seven')
        qp2 = self._create_question_pool(exam, title='Dwarfs')
        # Create an int question with choices listed and a correct answer.
        q3 = self._create_question(qp2, 'int', label='Number of dwarfs?')
        q3_a1 = self._create_answer(q3, value=5, label='five')
        q3_a2 = self._create_answer(q3, value=7, correct=True, label='seven')
        q3_a3 = self._create_answer(q3, value=9, label='nine')
        q3_a4 = self._create_answer(q3, value=10, label='ten')
        # Create a question with choices not included in scoring.
        q4 = self._create_question(qp2, 'choice', label='Which one is your ' + \
                                   'favorite dwarf?')
        q4_a1 = self._create_answer(q4, label='Dopey')
        q4_a2 = self._create_answer(q4, label='Grumpy')
        q4_a3 = self._create_answer(q4, label='Doc')
        q4_a4 = self._create_answer(q4, label='Happy')
        q4_a5 = self._create_answer(q4, label='Bashful')
        q4_a6 = self._create_answer(q4, label='Sneezy')
        q4_a7 = self._create_answer(q4, label='Sleepy')
        q4_a8 = self._create_answer(q4, label='None of the Above',
                                    text_response=True)
        qp3 = self._create_question_pool(exam, title='Days')
        # Create a question
        q5 = self._create_question(qp3, 'int', label='How many days in a week?',
                                   help_text='Only count those days that ' + \
                                             'end with the word "day".')
        q5_a1 = self._create_answer(q5, value=7, correct=True)

        exam = self.exam_manager.get_filtered(self.admin_token, {'exact' : {'id' : exam.id}}, ['question_pools'])[0]
        self.assertEquals(len(exam['question_pools']), 3)

        student, student_at = self.create_student()
        assignment = self.assignment_manager.create(self.admin_token, exam['id'], student.id)

        # Take the exam with all answers correct.
        answer_key = {
            q1.id: {'value': True},
            q2.id: {'value': 'seven'},
            q3.id: {'value': 7},
            q4.id: {'value': lambda: random.choice(q4.answers.values_list( \
                                                   'id', flat=True)),
                    'correct': None},
            q5.id: {'value': 7}
        }
        # take the exam
        exam_session_id1 = self._take_exam(student_at, assignment, answer_key, 100, True)

        # Test that the default behavior of create is now to resume an existing
        # exam session instead of always creating a new one if there is a
        # pending one found for the same exam.
        assignment = self.assignment_manager.create(self.admin_token, exam['id'], student.id)
        exam_session_id1 = self.exam_session_manager.create(student_at,
                                                            assignment.id,
                                                            fetch_all=False).id
        exam_session_id2 = self.exam_session_manager.create(student_at,
                                                            assignment.id,
                                                            fetch_all=False).id
        self.assertEqual(exam_session_id1, exam_session_id2)

        # Test that create can still create a new session.
        exam_session_id1 = self.exam_session_manager.create(student_at,
                                                            assignment.id,
                                                            fetch_all=False,
                                                            resume=False).id
        exam_session_id2 = self.exam_session_manager.create(student_at,
                                                            assignment.id,
                                                            fetch_all=False,
                                                            resume=False).id
        self.assertNotEqual(exam_session_id1, exam_session_id2)

        # Now miss one question.
        assignment = self.assignment_manager.create(self.admin_token, exam['id'], student.id)
        answer_key[q1.id].update({'value': False, 'correct': False})
        self._take_exam(student_at, assignment, answer_key, 75, True)

        # Now miss two questions.
        assignment = self.assignment_manager.create(self.admin_token, exam['id'], student.id)
        answer_key[q2.id].update({'value': 'four', 'correct': False})
        self._take_exam(student_at, assignment, answer_key, 50, False)

        # Now miss three questions.
        assignment = self.assignment_manager.create(self.admin_token, exam['id'], student.id)
        answer_key[q3.id].update({'value': 4, 'correct': False})
        self._take_exam(student_at, assignment, answer_key, 25, False)

        # Now miss four questions.
        assignment = self.assignment_manager.create(self.admin_token, exam['id'], student.id)
        answer_key[q5.id].update({'value': 2, 'correct': False})
        exam_session_id = self._take_exam(student_at, assignment, answer_key, 0, False)

        # For an exam with possible correct answers, we cannot submit a response
        # or calculate the score after the exam is completed.
        self.assertRaises(exceptions.ExamSessionAlreadyFinishedException,
            self.exam_session_manager.add_response, student_at, exam_session_id, q5.id, {'value': 7})

    def test_exam_session_retry(self):
        """First create the exam for this test case.

        WARNING: This test fails when using a sqlite3 database.

        """
        exam = self._create_exam(name='seven', title='Do You Know Your Sevens?',
                                 passing_score=75)
        qp1 = self._create_question_pool(exam, title='Math')
        # Create a bool question with a correct answer.
        q1 = self._create_question(qp1, 'bool', label='3 + 4 = 7?')
        q1_a1 = self._create_answer(q1, correct=True, value=True)
        # Create a char question with a correct answer.
        q2 = self._create_question(qp1, 'char', label='Spell "7"')
        q2_a1 = self._create_answer(q2, correct=True, value='seven')
        
        student, student_at = self.create_student()
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)

        half_correct_answer_key = {
            q1.id: {'value': True},
            q2.id: {'value': 'sieben'},
        }
        # take the exam, getting half of the questions right
        exam_session_id_1 = self._take_exam(student_at, assignment, half_correct_answer_key, 50, False, True)
        exam_session_1 = self.exam_session_manager.get_filtered(student_at,
            {'exact': {'id': exam_session_id_1}}, ['score', 'date_completed', 'passed'])[0]
        self.assertEquals(Decimal(exam_session_1['score']), Decimal('50.00'))
        self.assertFalse(exam_session_1['passed'])
        self.assertNotEqual(exam_session_1['date_completed'], None)
        
        all_correct_answer_key = {
            q1.id: {'value': True},
            q2.id: {'value': 'seven'},
        }
        # take the exam again, getting all of the questions right
        exam_session_id_2 = self._take_exam(student_at, assignment, all_correct_answer_key, 100, True, True)
        exam_session_2 = self.exam_session_manager.get_filtered(student_at,
            {'exact': {'id': exam_session_id_2}}, ['score', 'date_completed', 'passed'])[0]
        self.assertEquals(Decimal(exam_session_2['score']), Decimal('100.00'))
        self.assertTrue(exam_session_2['passed'])
        self.assertNotEqual(exam_session_2['date_completed'], None)
        
        self.assertNotEqual(exam_session_id_1, exam_session_id_2)
        
    def test_exam_session_survey(self):
        #"""Test an exam session when used for a survey or application."""
        # (No answers are labelled as correct or incorrect.)

        # First create the exam for this test case.
        exam = self._create_exam(name='madeupwords',
                                 title='Random letters and numbers')
        qp1 = self._create_question_pool(exam, title='Numbers')
        # Create an int question.
        q1 = self._create_question(qp1, 'int',
                                   label='Enter any number you like.')
        # Create a bool question.
        q2 = self._create_question(qp1, 'bool',
                                   label='Select either true or false.')
        qp2 = self._create_question_pool(exam, title='Letters')
        # Create a question with choices not included in scoring.
        q3 = self._create_question(qp2, 'choice',
                                   label='Pick any of these.')
        q3_a1 = self._create_answer(q3, label='lkjfglkj')
        q3_a2 = self._create_answer(q3, label='iriririr')
        q3_a3 = self._create_answer(q3, label='kjdfkdjfkj')
        q3_a4 = self._create_answer(q3, label='mnbvmnbv')
        q4 = self._create_question(qp2, 'char',
                                   label='Enter any combination of letters.')

        # Take the exam with some answers.
        answer_key = {
            q1.id: {'value': 785, 'correct': None},
            q2.id: {'value': False, 'correct': None},
            q3.id: {'value': q3_a3.id, 'correct': None},
            q4.id: {'value': 'jkldfsjkldsfkjllkjdf', 'correct': None},
        }

        student, student_at = self.create_student()
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        es_id = self._take_exam(student_at, assignment, answer_key, None, None)

        # For an exam without possible correct answers, we can resume the exam
        # session and retake the exam.
        assignment = self.assignment_manager.create(self.admin_token, exam.id, student.id)
        es_id = self._take_exam(student_at, assignment, answer_key, None, None, resume=True)

        # And now just read the exam for review.
        ret = self.exam_session_manager.review(self.admin_token, es_id)
        for k in ('id', 'title', 'question_pools'):
            self.assertTrue(k in ret)
        for qp in ret['question_pools']:
            for k in ('id', 'title', 'questions'):
                self.assertTrue(k in qp)
            for q in qp['questions']:
                for k in ('id', 'question_type', 'widget'):
                    self.assertTrue(k in q)

class TestEvaluations(pr_tests.TestCase):
    def test_all(self):
        evaluation = facade.models.Exam.objects.create(name='eval',
            title='Eval')
        qp = facade.models.QuestionPool.objects.create(exam=evaluation,
            title='Evaluation')
        q1 = facade.models.Question.objects.create(question_pool=qp,
            question_type='char', label='How do you feel?')
        r1 = facade.models.Question.objects.create(question_pool=qp,
            question_type='rating', label='Pick a number', text_response=True,
            min_value=1, max_value=4)

        event1 = self.event_manager.create(self.admin_token, 'Event 1',
                                           'Event 1', 'Event 1',
                                           self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), self.organization1.id,
            self.product_line1.id, {'venue' : self.venue1.id})
        session1 = self.session_manager.create(self.admin_token,
                                               self.right_now.isoformat(),
            (self.right_now+self.one_day).isoformat(), 'active', True, 10000,
            event1.id)
        session1.evaluation = evaluation
        session1.save()

        # Take the evaluation
        student, student_at = self.create_student()
        assignment = self.assignment_manager.create(self.admin_token, evaluation.id, student.id)
        exam_session1 = self.exam_session_manager.create(student_at,
                                                         assignment.id, False)
        questions = self.exam_session_manager.finish(student_at,
                                                     exam_session1.id)
        self.exam_session_manager.add_response(student_at,
                                               exam_session1.id, q1.id,
                                               {'value': 'great'})
        self.exam_session_manager.add_response(student_at,
                                               exam_session1.id, r1.id,
                                               {'value': 4, 'text': 'four'})
        self.exam_session_manager.finish(student_at, exam_session1.id)

        ret = self.session_manager.get_evaluation_results(self.admin_token,
                                                          session1.id)

        self.assertEquals(len(ret), 1)
        response = ret[0]
        self.assertTrue('questions' in response)
        self.assertEquals(len(response['questions']), 2)
        self.assertEquals(response['questions'][0]['question']['label'], 'How do you feel?')
        self.assertEquals(response['questions'][0]['question']['id'], q1.id)
        self.assertEquals(response['questions'][0]['response']['value'], 'great')
        self.assertEquals(response['questions'][1]['response']['value'], 4)
        self.assertEquals(response['questions'][1]['response']['text'], 'four')
        self.assertEquals(response['questions'][1]['question']['label'], 'Pick a number')
        self.assertEquals(response['questions'][1]['question']['id'], r1.id)

# vim:tabstop=4 shiftwidth=4 expandtab
