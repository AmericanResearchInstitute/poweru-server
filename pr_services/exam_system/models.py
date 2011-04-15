"""
Data model for Power Reg exam system.

:author: Chris Church <cchurch@americanri.com>
:copyright: Copyright 2010 American Research Institute, Inc.
"""

__docformat__ = "restructuredtext en"

# Python
import datetime
from decimal import Decimal, ROUND_UP
import itertools
import re

# Django
from django.conf import settings
from django.db import models

# PowerReg
from pr_services import pr_models
import exceptions
from pr_services import storage

__all__ = ['Exam', 'QuestionPool', 'Question', 'Answer', 'ExamSession',
           'Response', 'FormPage', 'FormWidget']

def _update_order_field(instance, query_set, field_name='order'):
    """Updates the order field when creating/modifying ordered items."""
    # If the instance exists, exclude it from the query set results.
    if instance.pk is not None:
        query_set = query_set.exclude(pk=instance.pk)
    # If current/set value is None, append to the list.
    if getattr(instance, field_name) is None:
        if not query_set.count():
            setattr(instance, field_name, 0)
        else:
            setattr(instance, field_name,
                    query_set.aggregate(n=models.Max(field_name))['n'] + 1)
    # Otherwise insert the item at the given position and shift remaining items
    # as necessary.
    else:
        order_value = getattr(instance, field_name)
        # Only do the update if there is an item already with the same order.
        if query_set.filter(**{field_name: order_value}).count():
            qs = query_set.filter(**{'%s__gte' % field_name: order_value})
            qs.update(**{field_name: models.F(field_name) + 1})

def _name_is_unique(instance, query_set, other_query_sets=[], field_name='name'):
    if instance.pk is not None:
        query_set = query_set.exclude(pk=instance.pk)
    name_value = getattr(instance, field_name)
    if name_value is not None:
        for qs in [query_set] + other_query_sets:
            if qs is not None and qs.filter(**{field_name: name_value}).count():
                return False
    return True

class Exam(pr_models.Task):
    """An exam containing one or more question pools."""

    class Meta:
        app_label = 'pr_services'

    #: Minimum score required to pass the exam (0 to 100 inclusive).
    passing_score = models.PositiveIntegerField(default=0)

    # Other fields we may need, TBD.
    #: When True, the exam is finished as soon as a passing score is achieved.
    # finish_on_pass = PRBooleanField(default=False)
    #: When True, the exam is finished as soon as it is no longer possible for
    #: a user to achieve a passing score.
    # finish_on_fail = PRBooleanField(default=False)

    # question_pools = one-to-many relationship with QuestionPool
    # exam_sessions = one-to-many relationship with ExamSession

    def validate(self, validation_errors=None, related=False):
        validation_errors = super(Exam, self).validate(validation_errors) or {}
        # Verify that the passing score is from 0 to 100.
        if self.passing_score not in xrange(0, 101):
            pr_models.add_validation_error(validation_errors, 'passing_score', \
                'passing score must be from 0 to 100 inclusive')
        # Verify that the name field is set and unique among Exams.
        if not self.name:
            pr_models.add_validation_error(validation_errors, 'name',
                                           'exam must be given a name')
        possible_duplicates = Exam.objects.filter(name=self.name)
        if self.pk:
            possible_duplicates = possible_duplicates.exclude(pk=self.pk)
        for possible_duplicate in possible_duplicates:
            if self.version_id == possible_duplicate.version_id:
                pr_models.add_validation_error(validation_errors, 'name',
                    'exam with same name and version id exists')
        # make sure that the exam's name is not the name of any of its elements
        if not _name_is_unique(self,
            QuestionPool.objects.filter(exam=self) if self.pk else None,
            [Question.objects.filter(question_pool__exam=self),
            Answer.objects.filter(question__question_pool__exam=self),
            ] if self.pk is not None else []):
            pr_models.add_validation_error(validation_errors, 'name', \
                'exam name must not match the name of any of its elements')
        # When the related flag is set, validate all question pools that are
        # part of this exam.
        if related:
            for qp in self.question_pools.all():
                validation_errors = qp.validate(validation_errors, True)
        return validation_errors

    def __unicode__(self):
        return u'%s' % self.title

class QuestionPool(pr_models.OwnedPRModel):
    """A pool of related questions that make up an exam."""

    class Meta:
        app_label = 'pr_services'
        #order_with_respect_to = 'exam'
        ordering = ['order']

    #: unique identifier for this question pool within the exam (meant to be
    #: quasi-human friendly and available independently of primary keys in the
    #: database)
    name = models.CharField(max_length=255, blank=True, null=True)
    #: Reference to the exam containing this question pool.
    exam = pr_models.PRForeignKey('Exam', related_name='question_pools')
    #: Title of this section of the exam.
    title = models.CharField(max_length=255, null=True, blank=True)
    #: Order of this question pool within the exam.
    order = models.PositiveIntegerField(default=None)
    #: When set, determines the next question pool to follow this one instead of
    #: the default, which is the next one in order.  Can only skip ahead; not
    #: allowed to jump back to a previous one.
    next_question_pool = pr_models.PRForeignKey('QuestionPool', null=True,
                                           default=None)

    # Other fields we may need, TBD.
    #: Pick questions in random order, ignoring the question's order attribute.
    randomize_questions = pr_models.PRBooleanField(default=False)
    #: Display only this number of questions from the pool, instead of all.
    # minimum_questions = models.PostitiveIntegerField(default=None, null=True)

    # questions = one-to-many relationship with Question

    number_to_answer = models.PositiveIntegerField(default=0)

    def validate(self, validation_errors=None, related=False):
        validation_errors = super(QuestionPool, self).validate(validation_errors)
        validation_errors = validation_errors or {}
        if not _name_is_unique(self, QuestionPool.objects.filter(exam=self.exam),
                               [Exam.objects.filter(pk=self.exam.pk),
                                Question.objects.filter(question_pool__exam=self.exam),
                                Answer.objects.filter(question__question_pool__exam=self.exam),
                                ]):
            pr_models.add_validation_error(validation_errors,
                'name', 'value is not unique among the names in the current Exam')
        # Make sure the next_question_pool, if set, is part of the same exam.
        if self.next_question_pool and self.next_question_pool.exam != self.exam:
                pr_models.add_validation_error(validation_errors, \
                    'next_question_pool', \
                    'next question pool must be part of the same exam')
        # Make sure the next_question_pool does not put us in a loop.
        if self.next_question_pool and self.next_question_pool.order <= self.order:
                pr_models.add_validation_error(validation_errors, \
                    'next_question_pool', 'next question pool must come ' + \
                    'after the current question pool')
        # When the related flag is set, validate all questions that are part of
        # this question pool.
        if related:
            for q in self.questions.all():
                validation_errors = q.validate(validation_errors, True)
        return validation_errors

    def save(self, *args, **kwargs):
        # Modify order field to keep in sequence within the exam.
        qs = QuestionPool.objects.filter(exam=self.exam)
        _update_order_field(self, qs)
        return super(QuestionPool, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.title

class Question(pr_models.OwnedPRModel):
    """A question belonging to a question pool."""

    # The question model provides the information to display a question and
    # determine whether the response is valid, regardless of whether or not it
    # is considered a correct answer.

    #: Dictionary mapping question types to widgets; first widget in the list is
    #: used as the default.
    QUESTION_WIDGETS = {
        #'question_type': ['default_widget', 'other_widget', ...],
        'bool': ['CheckboxInput', 'RadioSelect', 'Select'],
        'char': ['TextInput', 'Textarea'],
        'choice': ['Select', 'SelectMultiple', 'RadioSelect',
                   'CheckboxSelectMultiple'],
        'date': ['DateInput', 'TextInput'],
        'datetime': ['DateTimeInput', 'TextInput'],
        'decimal': ['TextInput', 'Select'],
        'float': ['TextInput', 'Select'],
        'int': ['TextInput', 'Select'],
        'rating': ['RadioSelect', 'Select'],
        'text': ['Textarea', 'TextInput'],
        'time': ['TimeInput', 'TextInput'],
    }

    class Meta:
        app_label = 'pr_services'
        ordering = ['order']

    ## Fields applicable to all question types.

    #: a unique identifier for this question (unique within its exam)
    name = models.CharField(max_length=255, blank=True, null=True)
    #: Reference to the question pool containing this question.
    question_pool = pr_models.PRForeignKey('QuestionPool', related_name='questions')
    #: Order of this question within the question pool.
    order = models.PositiveIntegerField(default=None)
    #: Is the user required to answer this question?
    required = pr_models.PRBooleanField(default=True)
    #: Text of the question (e.g. "What's your favorite color?")
    label = models.TextField()
    #: Help text for this question.
    help_text = models.TextField(default=None, null=True)
    #: Text to display when someone gets this question wrong.
    rejoinder = models.TextField(default=None, null=True)

    #: Possible types of questions.
    QUESTION_TYPE_CHOICES = ((x,x) for x in QUESTION_WIDGETS.keys())
    #: Type of question.
    question_type = models.CharField(max_length=31,
                                     choices=QUESTION_TYPE_CHOICES)
    #: Possible types of widgets used to display questions.
    WIDGET_CHOICES = ((x,x) for x in itertools.chain(*QUESTION_WIDGETS.values()))
    #: Widget used to display this question.
    widget = models.CharField(max_length=31, choices=WIDGET_CHOICES,
                              default=None)

    ## Fields applicable based on the selected question type.

    #: Minimum number of answers that must be selected (for choice questions).
    min_answers = models.PositiveIntegerField(default=1)
    #: Maximum number of answers that may be selected (for choice questions).
    max_answers = models.PositiveIntegerField(default=1, null=True)

    #: Do we allow an (additional) free-form, text response regardless of the
    #: answer?  Note: this field is FALSE for questions already accepting a text
    #: input.
    text_response = pr_models.PRBooleanField(default=False)
    #: Additional label to be displayed for free-text response.
    text_response_label = models.TextField(default=None, null=True)
    #: Minimum length of text entry required.
    min_length = models.PositiveIntegerField(default=0)
    #: Maximum length of text entry allowed.
    max_length = models.PositiveIntegerField(default=None, null=True)
    #: Regular expression used to validate text entry.
    text_regex = models.CharField(max_length=255, default=None, null=True)

    #: Minimum valid value for any numeric question type.
    min_value = models.DecimalField(max_digits=24, decimal_places=10,
                                    default=None, null=True)
    #: Maximum valid value for any numeric question type.
    max_value = models.DecimalField(max_digits=24, decimal_places=10,
                                    default=None, null=True)

    # answers = one-to-many relationship with Answer
    # responses = many-to-many relationship with Response

    # Other fields possibly needed, TBD.
    #: Randomize the order of the answers.
    #randomize_answers = PRBooleanField(default=False)
    #: When True and this question has no explicit answers specified, any valid
    #: response will be considered a correct one.
    #correct_if_valid = models.NullBooleanField(default=None)
    #: An image file to be displayed with this question.
    #image = models.ImageField(default=None, null=True)

    @classmethod
    def _update_question_widgets(cls, question_widgets={}, replace=False):
        """Method for use by subclasses to update question and widget types."""
        if replace:
            cls.QUESTION_WIDGETS = {}
        cls.QUESTION_WIDGETS.update(question_widgets)
        cls.QUESTION_TYPE_CHOICES = ((x,x) for x in cls.QUESTION_WIDGETS.keys())
        pr_models.change_charfield_choices(cls, 'question_type',
                                           cls.QUESTION_TYPE_CHOICES)
        cls.WIDGET_CHOICES = ((x,x) for x in \
            itertools.chain(*QUESTION_WIDGETS.values()))
        pr_models.change_charfield_choices(cls, 'widget', cls.WIDGET_CHOICES)

    def _get_default_widget(self):
        """Return the default widget to be used for the question type."""
        return self.QUESTION_WIDGETS.get(self.question_type, [None])[0]
    default_widget = property(_get_default_widget)

    def _get_valid_widgets(self):
        """Return a set of all valid widget types for the question type."""
        return set(self.QUESTION_WIDGETS.get(self.question_type, []))
    valid_widgets = property(_get_valid_widgets)

    def validate(self, validation_errors=None, related=False):
        validation_errors = super(Question, self).validate(validation_errors)
        validation_errors = validation_errors or {}
        
        # make sure that the name of this question is unique among all of the
        # name attributes for the question's Exam, and QuestionPools,
        # Questions, and Answers also belonging to the question's exam
        exam = self.question_pool.exam
        if not _name_is_unique(self, Question.objects.filter(question_pool__exam=exam),
                               [Exam.objects.filter(pk=exam.pk),
                                QuestionPool.objects.filter(exam=exam),
                                Answer.objects.filter(question__question_pool__exam=exam),
                                ]):
            pr_models.add_validation_error(validation_errors,
                'name', 'value is not unique among the names in the current Exam')

        # Verify range of values for numeric questions:
        if self.question_type in ('decimal', 'float', 'int', 'rating'):
            type_func = {'float': float, 'int': int, 'rating': int}.get( \
                self.question_type, lambda x: x)
            if self.min_value is not None and self.max_value is not None:
                if not type_func(self.max_value) >= type_func(self.min_value):
                    pr_models.add_validation_error(validation_errors, \
                        'max_value', \
                        'max_value must be greater than min_value')
        # Check minimum value for rating questions.
        if self.question_type == 'rating':
            if self.min_value is not None:
                if not int(self.min_value) >= 0:
                    pr_models.add_validation_error(validation_errors, \
                        'min_value', 'min_value must be zero or positive')
        # Check question attributes for a choice question.
        if self.question_type == 'choice':
            if self.max_answers is not None:
                if not self.max_answers >= self.min_answers:
                    pr_models.add_validation_error(validation_errors, \
                        'max_answers', \
                        'max_answers must be greater than min_answers')
                if not self.max_answers > 0:
                    pr_models.add_validation_error(validation_errors, \
                        'max_answers', 'max_answers must be greater than zero')
        # Verify text response length attributes.
        if self.max_length is not None:
            if not self.max_length >= self.min_length:
                pr_models.add_validation_error(validation_errors, 'max_length',\
                    'max_length must be greater than min_length')
        # Verify the text response regular expression.
        if self.text_regex is not None:
            try:
                re.compile(self.text_regex)
            except re.error:
                pr_models.add_validation_error(validation_errors, 'text_regex',\
                    'invalid text regular expression')
        # Use default widget for question type if not explicitly specified.
        if self.widget not in self.valid_widgets:
            pr_models.add_validation_error(validation_errors, 'widget', \
                'invalid widget %s for question type %s' % \
                (self.widget, self.question_type))
        # When the related flag is set, validate all answers that are part of
        # this question.
        if related:
            for a in self.answers.all():
                validation_errors = a.validate(validation_errors)
        return validation_errors

    def save(self, *args, **kwargs):
        # Modify order field to keep in sequence within the question pool.
        qs = Question.objects.filter(question_pool=self.question_pool)
        _update_order_field(self, qs)
        # Use default widget for question type if not explicitly specified.
        if self.widget is None:
            self.widget = self.default_widget
        # Set text_response = False for any char question types.
        if self.question_type in ('char', 'password', 'text'):
            self.text_response = False
        return super(Question, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % (self.label)

class Answer(pr_models.OwnedPRModel):
    """Possible answers for multiple-choice questions or correct answers for
    other question types."""

    # The answer model provides possible choices for multiple choice questions,
    # as well as logic used to determine whether the answer is correct for any
    # question type.

    class Meta:
        app_label = 'pr_services'
        #order_with_respect_to = 'question'
        ordering = ['order']

    #: a unique identifier for this answer (unique within its exam)
    name = models.CharField(max_length=255, blank=True, null=True)
    #: Question to which this answer applies.
    question = pr_models.PRForeignKey('Question', related_name='answers')
    #: Order of this answer within the list of possible choices.
    order = models.PositiveIntegerField(default=None)
    #: The text presented to the user for this answer.  Answers with no label
    #: are never sent to the user, only used to determine whether a response is
    #: correct.
    label = models.CharField(max_length=255, default=None, null=True)
    #: When True and this answer is selected, allow an additional text response.
    text_response = pr_models.PRBooleanField(default=False)
    #: The actual value or expression represented by this answer.  Used to
    #: determine whether the answer is correct when not a choice question.
    value = models.CharField(max_length=255, default=None, null=True)
    #: True if this answer is a correct one, False if it is incorrect.
    #: None if it is neither correct nor incorrect.
    correct = models.NullBooleanField(default=None)

    #: When set, determines the next question pool when this answer is selected,
    #: regardless of whether the answer is correct or not.
    next_question_pool = pr_models.PRForeignKey('QuestionPool', null=True,
                                           default=None)
    #: When True and this answer is selected, immediately end the question pool.
    end_question_pool = pr_models.PRBooleanField(default=False)
    #: When True and this answer is selected, end the exam after this question
    #: pool.
    end_exam = pr_models.PRBooleanField(default=False)

    # responses = many-to-many relationship with Response.

    # Other fields that may be needed, TBD.
    #: An image file to be displayed with this answer.
    #image = models.ImageField(default=None, null=True)

    def validate(self, validation_errors=None):
        validation_errors = super(Answer, self).validate(validation_errors)
        validation_errors = validation_errors or {}
        exam = self.question.question_pool.exam
        if not _name_is_unique(self, Answer.objects.filter(question__question_pool__exam=exam),
                               [Exam.objects.filter(pk=exam.pk),
                                QuestionPool.objects.filter(exam=exam),
                                Question.objects.filter(question_pool__exam=exam),
                                ]):
            pr_models.add_validation_error(validation_errors,
                'name', 'value is not unique among the names in the current Exam')
        # Make sure the next_question_pool, if set, is part of the same exam.
        if self.next_question_pool and \
            self.next_question_pool.exam != self.question.question_pool.exam:
                pr_models.add_validation_error(validation_errors, \
                    'next_question_pool', \
                    'next question pool must be part of the same exam')
        # Make sure the next_question_pool does not put us in a loop.
        if self.next_question_pool and \
            self.next_question_pool.order <= self.question.question_pool.order:
                pr_models.add_validation_error(validation_errors, \
                    'next_question_pool', 'next question pool must come ' + \
                    'after the current question pool')
        return validation_errors

    def save(self, *args, **kwargs):
        """Check or update the answer attributes before saving."""
        # Modify order field to keep in sequence within the question pool.
        qs = Answer.objects.filter(question=self.question)
        _update_order_field(self, qs)
        self.value = str(self.value) if self.value is not None else None
        super(Answer, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % (self.label)

class ExamSession(pr_models.AssignmentAttempt):
    """An instance of a user taking an exam."""

    class Meta:
        app_label = 'pr_services'

    #: Many-to-many relationship to questions and responses for this session.
    response_questions = models.ManyToManyField('Question', through='Response')

    #: We store these two values instead of calculating them on the fly in case
    #: the exam changes over time.
    
    #: Percentage of questions for which there is a correct answer which were
    #: answered correctly, to 2 decimal places.
    score = models.DecimalField(max_digits=5, decimal_places=2, default=None,
                                null=True)
    #: number of questions that were answered correctly
    number_correct = models.PositiveIntegerField(default=None, null=True)
    #: Whether the user passed the exam, None if the exam is not complete.
    passed = models.NullBooleanField()

    # responses = many-to-one relationship with Response

    def save(self, *args, **kwargs):
        """Check or update the exam session attributes before saving."""

        # if completed and passed, mark the assignment completed
        if self.date_completed is not None and self.passed:
            self.date_completed = datetime.datetime.utcnow()
            self.assignment.mark_completed()
        super(ExamSession, self).save(*args, **kwargs)

    @property
    def passing_score(self):
        return self.exam.passing_score

    @property
    def exam(self):
        exam = self.assignment.task.downcast_completely()
        if isinstance(exam, Exam):
            return exam
        else:
            raise TypeError('Assigned Task is not an Exam')

    def iter_questions(self):
        """Iterate over all questions for this exam session, including branching
        based on answers submitted so far."""
        next_qp = None
        end_exam = False
        end_qp = False
        for qp in self.exam.question_pools.all():
            # If flagged to end the exam, skip remaining questions.
            if end_exam:
                continue
            # If next question pool has been set, skip this pool if it is not
            # the next one.  Once we reach the next question pool, reset the
            # next_qp variable to None.
            if next_qp is not None:
                if next_qp != qp:
                    continue
                else:
                    next_qp = None
            if qp.next_question_pool:
                next_qp = qp.next_question_pool

            existing_responses = self.responses.filter(question__question_pool=qp)
            # If no questions have been previously assigned, decide which ones
            # will be assigned
            if existing_responses.count() == 0:
                questions = qp.questions.all()
                if qp.randomize_questions:
                    questions = questions.order_by('?')
                    if qp.number_to_answer > 0:
                        questions = questions[:qp.number_to_answer]
            else:
                questions = [response.question for response in existing_responses]

            for q in questions:
                # If flagged to end the pool, skip remaining questions.
                if end_qp:
                    continue
                # If a response has been given, use the answer to determine
                # whether to end the exam, question pool, or jump to a new
                # question pool after this one.
                if self.responses.filter(question=q).count():
                    r = self.responses.get(question=q)
                    # Check answers to all questions with answers submitted.
                    if r.valid is not None:
                        for a in r.answers.all():
                            if a.next_question_pool:
                                next_qp = a.next_question_pool
                            if a.end_question_pool:
                                end_qp = True
                            if a.end_exam:
                                end_exam = True
                yield q

    def get_next_questions(self, include_answered=False):
        """Return the next set of questions to be answered."""
        # If the exam has been completed, no questions are available.
        if self.assignment.status not in  ('pending', 'assigned', 'late'):
            return []
        q_list = []     # Unanswered questions
        aq_list = []    # Answered questions
        this_qp = None
        for q in self.iter_questions():
            # Stop at a new question pool when we have unanswered questions to
            # return.
            if this_qp is None or not q_list:
                this_qp = q.question_pool
            elif this_qp != q.question_pool:
                break
            # Create a new empty response when we send out a new question.
            r, created = self.responses.get_or_create(question=q)
            # If a new response was created, add this question to the list.
            if created or (r.valid is None and q.required):
                q_list.append(q)
            # Otherwise, the question may already have a response. Add it to the
            # list only if we are including already answered questions.
            elif include_answered:
                aq_list.append(q)
        return aq_list + q_list

    def submit_response(self, question, value=None, text=None):
        """Submit a response value and optional text for the given question."""
        # If the exam has been completed, no further response can be accepted.
        if self.date_completed != None:
            raise exceptions.ExamSessionAlreadyFinishedException()
        try:
            r = self.responses.get(question=question)
        except Response.DoesNotExist:
            # Cannot accept a response for a question that has not been sent to
            # the user.
            raise exceptions.InvalidResponseException()
        r.value = value
        r.text = text
        r.save(check_correct=True)
        if self.assignment.status == 'assigned':
            self.assignment.status = 'pending'
            self.assignment.save()
        return r

    def calculate_score(self, save_score=True, save_passed=True):
        """Calculate the score and update the pass/fail flag."""

        # Iterate through all the questions and tally the total number of
        # questions with potential correct answers, as well as the total number
        # answered correctly.
        q_count = 0
        q_correct = 0
        for q in self.iter_questions():
            # First check to see if this question has any answers which are
            # explicitly set as correct or incorrect.
            if q.answers.filter(correct__isnull=False).count():
                q_count += 1
                # Now check to see if it has a response, and is correct.
                try:
                    if self.responses.get(question=q).correct:
                        q_correct += 1
                except Response.DoesNotExist:
                    pass

        # Compute the score and save it.
        if q_count:
            score = 100 * Decimal(q_correct) / Decimal(q_count)
            score = score.quantize(Decimal('0.01'), rounding=ROUND_UP)
        else:
            score = None
        if save_score:
            self.score = score
            self.number_correct = q_correct

        # Update the pass/fail flag.
        if score is not None and self.exam.passing_score is not None:
            passed = score >= self.exam.passing_score
        else:
            passed = None
        if save_passed:
            self.passed = passed

        # Save this instance and return the score.
        if save_score or save_passed:
            self.save()
        return score

class Response(pr_models.OwnedPRModel):
    """Through table for a response to a Question for a given ExamSession."""

    # The response model stores a response to a question, or a potential
    # response to a question sent to the user but not yet answered.  A valid
    # response is any response that passes all of the validation rules defined
    # for the question itself, while a correct response is one that matches one
    # or more of the correct answers associated with the question.

    # Possible combinations of valid and correct fields (* means any of True,
    # False or None):
    # valid=None    correct=*       unanswered: question has been sent to the
    #                               user, but the user has not responded.
    # valid=False   correct=*       invalid: question has received a response,
    #                               but the response did not validate.
    # valid=True    correct=None    answered: question has received a valid
    #                               response, but it is not possible to
    #                               determine whether the response is correct.
    # valid=True    correct=False   incorrect: question has received a valid
    #                               response, but the response is incorrect.
    # valid=True    correct=True    correct: question has received a valid and
    #                               correct response.

    class Meta:
        app_label = 'pr_services'
        #order_with_respect_to = 'exam_session'
        ordering = ['order']
        unique_together = ('exam_session', 'question')

    #: The following two foreign keys are for each end of the many-to-many
    #: relationship for which this is a through table (association class).
    #: The exam session associated with this response.
    exam_session = pr_models.PRForeignKey('ExamSession', related_name='responses')
    #: The question associated with this response.
    question = pr_models.PRForeignKey('Question', related_name='responses')
    #: The order that this question was sent to the user.
    order = models.PositiveIntegerField(default=0)
    #: Whether this response is valid, None if we haven't checked yet.
    valid = models.NullBooleanField(default=None)
    #: Whether this response is correct, None if we havent' checked yet.
    correct = models.NullBooleanField(default=None)

    #: Which answer(s) the user chose for multiple choice questions.  Or in the
    #: case of other questions, which answer(s) matched the user's response.
    answers = models.ManyToManyField('Answer', related_name='responses')
    #: Response value used for boolean questions.
    bool_value = models.NullBooleanField(default=None)
    #: Response value used for char questions.
    char_value = models.CharField(max_length=255, default=None, null=True)
    #: Response value used for date questions.
    date_value = models.DateField(default=None, null=True)
    #: Response value used for datetime questions.
    datetime_value = models.DateTimeField(default=None, null=True)
    #: Response value used for decimal questions.
    decimal_value = models.DecimalField(max_digits=24, decimal_places=10,
                                        default=None, null=True)
    #: Response value used for float questions.
    float_value = models.FloatField(default=None, null=True)
    #: Response value used for int questions.
    int_value = models.IntegerField(default=None, null=True)
    #: Response value used for password questions.
    password_value = models.CharField(max_length=255, default=None, null=True)
    #: Response value used for rating questions.
    rating_value = models.PositiveSmallIntegerField(default=None, null=True)
    #: Response value used for text questions or prose responses to other
    #: question types.
    text_value = models.TextField(default=None, null=True)
    #: Response value used for time questions.
    time_value = models.TimeField(default=None, null=True)

    def _to_python(self, value, value_type=None):
        """Converts the given value to python for the question type."""
        value_type = value_type or self.question.question_type
        # First look for a method named _TYPE_to_python, if not found, look for
        # a field named TYPE_value and use its to_python method.
        f = getattr(self, '_%s_to_python' % value_type, None)
        if not f:
            f = [x.to_python for x in self._meta.fields \
                 if x.name == '%s_value' % value_type][0]
        return f(value)

    def _bool_to_python(self, value):
        """Convert the given value to a Python boolean or None."""
        value = str(value).lower()
        if value in ('1', 't', 'true', 'y', 'yes'):
            return True
        elif str(value).lower() in ('0', 'f', 'false', 'n', 'no'):
            return False
        elif str(value).lower() in ('', 'none', 'null', 'nil'):
            return None
        else:
            return bool(value)

    def _set_text_value(self, value, check_valid=False, value_type=None):
        """Validate and store the response value for any text question."""
        value_type = value_type or self.question.question_type
        value = self._to_python(value, value_type)
        setattr(self, '%s_value' % value_type, value)
        value = value or ''
        if check_valid:
            if len(value) < self.question.min_length:
                raise ValueError, 'response too short'
            if self.question.max_length is not None:
                if len(value) > self.question.max_length:
                    raise ValueError, 'response too long'
            if self.question.text_regex is not None:
                if re.match(self.question.text_regex, value) is None:
                    raise ValueError, 'response does not match regex'

    _set_char_value = _set_text_value
    _set_password_value = _set_text_value

    def _check_text_answer(self, answer):
        """Return True if the answer matches the current response."""
        return self._to_python(answer.value) == self.value

    _check_char_answer = _check_text_answer
    _check_password_answer = _check_text_answer

    def _choice_to_python(self, value):
        """Convert a choice value to python."""
        # Value can be None, an Answer instance, an Anwser primary key, or a
        # sequence containing Answers instances or primary keys.
        if value is None:
            value = []
        elif isinstance(value, (Answer, int, long)):
            value = [value]
        return set(value)

    def _get_choice_value(self):
        """Return a set of all answer id's associated with this reponse."""
        return set(x.id for x in self.answers.all())

    def _set_choice_value(self, value, check_valid=False, value_type=None):
        """Update the answers selected for this response."""
        self.answers = self._to_python(value)
        # Check that the number of answers selected is within the given range,
        # and that the answers are actually related to the same question.
        if check_valid:
            if self.answers.exclude(question=self.question).count() > 0:
                raise ValueError, 'one or more answers are not related to ' + \
                                  'the same question'
            if self.answers.count() < self.question.min_answers:
                raise ValueError, 'at least %s answers must be selected' % \
                                  self.question.min_answers
            elif self.question.max_answers != None and self.answers.count() > self.question.max_answers:
                raise ValueError, (u'question (id: %d, name: %s): no more than %s answers may be selected' % 
                    (self.question.id, unicode(self.question.name), self.question.max_answers))

    def _check_choice_answer(self, answer):
        """Return True if the answer matches the current response."""
        return answer.id in self.value

    def _set_numeric_value(self, value, check_valid=False, value_type=None):
        """Generic setter for any numeric question type."""
        value_type = value_type or self.question.question_type
        value = self._to_python(value, value_type)
        setattr(self, '%s_value' % value_type, value)
        if check_valid:
            if self.question.min_value is not None:
                min_value = self._to_python(self.question.min_value)
                if value < min_value:
                    raise ValueError, 'value cannot be less than %s' % \
                                      str(min_value)
            if self.question.max_value is not None:
                max_value = self._to_python(self.question.max_value)
                if value > max_value:
                    raise ValueError, 'value cannot be greater than %s' % \
                                      str(max_value)

    _set_decimal_value = _set_numeric_value
    _set_float_value = _set_numeric_value
    _set_int_value = _set_numeric_value
    _set_rating_value = _set_numeric_value

    def _get_value(self, value_type=None):
        """Return the value of this response, depending on the question type."""
        value_type = value_type or self.question.question_type
        # Look for a getter method for this question type.
        f = getattr(self, '_get_%s_value' % value_type, None)
        # If no getter method is defined, attempt to get an attribute of the
        # instance based on the question type.
        if not f:
            f = lambda: getattr(self, '%s_value' % value_type)
        return f()

    def _set_value(self, value=None, check_valid=False, value_type=None):
        """Update the value of this response, depending on the question type."""
        value_type = value_type or self.question.question_type
        # Anytime the value is set, reset the valid and correct flags.
        self.valid = None
        self.correct = None
        # Look for a setter method for this question type.
        f = getattr(self, '_set_%s_value' % value_type, None)
        # If no setter function is defined, attempt to set an attribute of the
        # instance based on the question type.
        if not f:
            f = lambda x,y,z: setattr(self, '%s_value' % z, x)
        # Handle the case where answer primary keys are submitted as the value
        # when the question is not a choice question type.
        if value_type != 'choice' and isinstance(value, (tuple, list)) and \
            value_type == self.question.question_type:
            for a in self.question.answers.filter(label__isnull=False, id__in=value):
                value = a.value
                break
            if isinstance(value, (tuple, list)):
                raise ValueError, 'invalid answer primary keys'
        # Set the value and optionally check whether a response is required.
        # The value should always be set, and a ValueError raised for an invalid
        # value only when check_valid is True.
        if check_valid and value is None and self.question.required and \
            value_type == self.question.question_type:
            f(self._to_python(value, value_type), False, value_type)
            raise ValueError, 'a response is required'
        else:
            f(self._to_python(value, value_type), check_valid, value_type)

    value = property(_get_value, _set_value)

    def _get_text(self):
        """Getter for free text response field."""
        if self.question.question_type in ('char', 'password', 'text'):
            return None
        return self._get_value('text')

    def _set_text(self, value, check_valid=False):
        """Setter for free text response field."""
        if self.question.question_type not in ('char', 'password', 'text'):
            if self.question.text_response or \
                    self.answers.filter(text_response=True).count():
                self._set_value(value, check_valid, 'text')
            elif value is not None:
                raise ValueError, 'text response not allowed'
        elif value:
            raise ValueError, \
                'char questions do not allow an additional text response'

    text = property(_get_text, _set_text)

    def save(self, *args, **kwargs):
        """Optionally check this response to see if it is valid and correct."""
        if kwargs.pop('check_valid', False):
            self.check_valid()
        if kwargs.pop('check_correct', False):
            self.check_correct()
        return super(Response, self).save(*args, **kwargs)

    def check_valid(self, store_valid=True):
        """Check this response to see if it is valid."""
        # FIXME: Store validation errors for the user.
        # Use the value setter to validate this response value.
        try:
            self._set_value(self.value, True)
            self._set_text(self.text, True)
        except ValueError, value_error:
            valid = False
        else:
            valid = True
            value_error = ''
        if store_valid:
            self.valid = valid
        return valid, str(value_error) or None

    def check_correct(self, store_correct=True):
        """Check this response to see if it is correct."""
        # First check that the response is valid.
        if not self.valid:
            if self.valid == False or not self.check_valid(store_correct)[0]:
                if store_correct:
                    self.correct = None
                return None
        # Look for a custom check function, otherwise just compare the answer
        # label to the value to find a match.
        f = getattr(self, '_check_%s_answer' % self.question.question_type, None)
        if not f:
            f = lambda x: self.value == self._to_python(x.value)
        correct = []
        answers = []
        # Check to see if any answers match this response, but only if there is
        # at least one correct answer specified.
        if self.question.answers.filter(correct__isnull=False).count():
            for answer in self.question.answers.all():
                if f(answer):
                    correct.append(bool(answer.correct))
                    answers.append(answer)
                # Only for choice, append a None if a correct answer has not
                # been selected, otherwise, append False.
                elif answer.correct:
                    if self.question.question_type == 'choice':
                        correct.append(None)
                    else:
                        correct.append(False)
                        answers.append(answer)
        # For answers that do not determine correctness, simply associate any
        # answers with matchings values to the response.
        else:
            for answer in self.question.answers.all():
                if f(answer):
                    answers.append(answer)
        # For multiple choice questions, the response should be correct as long
        # as the minimum number of correct answers are selected, even if there
        # are other correct answers that were not selected.  Remove the None's
        # from the list in this case.
        if self.question.question_type == 'choice' and False not in correct:
            if len([x for x in correct if x]) >= self.question.min_answers:
                correct = [x for x in correct if x is not None]
        # If no right or wrong answers are explicitly specified, we cannot
        # determine whether this response is correct or not, so just store None.
        correct = None if not correct else all(correct)
        # Now store the correct flag and answers.
        if store_correct:
            self.correct = correct
            # For choice questions, the value IS the answers, so don't mess with
            # the answers already given.
            if self.question.question_type != 'choice':
                self.answers = answers
        return correct

class FormPage(models.Model):
    exam = pr_models.PRForeignKey(Exam, related_name='form_pages')
    number = models.PositiveIntegerField()
    photo = models.ImageField(storage=storage.FormPagePhotoStorage, null=True, upload_to=settings.FORM_PAGE_PHOTO_PATH)

    class Meta:
        app_label = 'pr_services'
        unique_together = (('exam', 'number'),)

class FormWidget(pr_models.OwnedPRModel):
    form_page = pr_models.PRForeignKey(FormPage, related_name='form_widgets')
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    question = pr_models.PRForeignKey(Question, related_name='form_widgets')
    answer = pr_models.PRForeignKey(Answer, null=True, related_name='form_widgets')

    class Meta:
        app_label = 'pr_services'

# vim:tabstop=4 shiftwidth=4 expandtab
