from __future__ import with_statement

from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.template.loader import render_to_string

from optparse import make_option
import os
import re

import facade

BASE_DIR = 'model'

class Command(BaseCommand):
    args = '<base path for flex package>'
    help = 'Generates flex code'

    option_list = BaseCommand.option_list + (
        make_option('-o', '--output-path', type='string', dest='output_path', help='directory in which to create output', default='.'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('must provide base path for flex package as an argument')

        flex_package_path = '%s.%s' % (args[0], BASE_DIR)

        # make sure we can do what we need at the output path
        output_path = options.get('output_path')
        if output_path is not None:
            if not os.access(output_path, os.W_OK):
                raise CommandError('cannot write to output path')
            os.chdir(output_path)
            if os.access(BASE_DIR, os.F_OK):
                raise CommandError('folder %s already exists. exiting!' % (BASE_DIR))

        os.mkdir(BASE_DIR)
        os.chdir(BASE_DIR)

        for attr in dir(facade.models):
            model = getattr(facade.models, attr)
            if isinstance(model, models.base.ModelBase):
                created_dir = False
                for field in model._meta.fields:
                    if isinstance(field, models.EmailField):
                        created_dir = self._confirm_or_create_directory(model._meta.object_name, created_dir)
                        self._create_class_file('flex/EmailFieldInput.as', field, flex_package_path, model._meta.object_name)
                    elif isinstance(field, models.CharField):
                        created_dir = self._confirm_or_create_directory(model._meta.object_name, created_dir)
                        self._create_class_file('flex/CharFieldInput.as', field, flex_package_path, model._meta.object_name)
                if created_dir:
                    os.chdir('../')

    def _confirm_or_create_directory(self, name, created_dir):
        """
        if the directory hasn't been created, create it and move there
        """
        if not created_dir:
            os.mkdir(name)
            os.chdir(name)
        return True

    def _create_class_file(self, template, field, flex_package_path, model_name):
        """
        create a new flex class

        note that we can get the model name from field.model._meta.object_name,
        but that will sometimes return a parent class instead of the model
        we are actually interested in.

        :param template:            name of a django template
        :type template:             string
        :param field:               django model field
        :type field:                django.db.models.Field
        :param flex_package_path:   base path of the flex package
        :type flex_package_path:    string
        :param model_name:          name of the model
        :type model_name:           string
        """
        name = self._convert_to_camel_case(field.name)
        with open('%sInput.as' % (name), 'w') as newfile:
            newfile.write(render_to_string(template, {'field':field, 'package_path':flex_package_path, 'class_name':name, 'model_name':model_name}))
            newfile.close()

    def _convert_to_camel_case(self, text):
        """
        convert a lowercase string with underscores to camel case

        example: 'session_user_role_requirement' becomes 'SessionUserRoleRequirement'
        """
        text = re.sub(r'(_)([a-z])', lambda x: x.group(2).upper(), text)
        text = re.sub(r'(\A[a-z])', lambda x: x.group(1).upper(), text)
        return text
