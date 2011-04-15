"""ScoManager class"""

from __future__ import with_statement

__docformat__ = "restructuredtext en"

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
import facade
from pr_services.cookiecache import CookieCache
from pr_services.credential_system.task_manager import TaskManager
from pr_services import exceptions
from pr_services.rpc.service import service_method
from pr_services.utils import Utils
import os
from urlparse import urlparse
from xml.etree import cElementTree as ElementTree
import zipfile

class ScoManager(TaskManager):
    """Manage Scos in the Power Reg system."""

    def __init__(self):
        """ constructor """

        TaskManager.__init__(self)
        self.getters.update({
            'completion_requirement' : 'get_general',
            'course' : 'get_foreign_key',
            'data' : 'get_general',
            'url' : 'get_general',
        })
        self.setters.update({
            'completion_requirement' : 'set_general',
            'course' : 'set_foreign_key',
            'data' : 'set_general',
            'url' : 'set_general',
        })
        self.my_django_model = facade.models.Sco

    @service_method
    def create(self, auth_token):
        """This method is not permitted.

        Scos cannot be created using this method, but rather are created by
        using the upload target for SCORM courses.  This manager is used to
        then update the information pertaining to the sco.

        """
        raise exceptions.OperationNotPermittedException('Scos cannot be created using the sco manager.  Please use the SCORM upload target.')

    @service_method
    def get_filtered(self, auth_token, filters, field_names=None):
        """Get objects filtered by various limits

        :todo: explain why this needs to be overridden.

        """
        scos = super(ScoManager, self).get_filtered(auth_token, filters, field_names)
        # Whether or not we should give access to the SCORM player
        should_give_scorm_access = False
        mc = CookieCache(auth_token)
        for sco in scos:
            if 'url' in sco:
                the_sco = self.my_django_model.objects.get(id=sco['id'])
                relative_sco_url = urlparse(settings.SECURE_MEDIA_URL+settings.COURSE_PATH+str(the_sco.course.id)+'/')[2]
                mc.paths.append(relative_sco_url)
                sco['url'] = reverse('scorm_player', args=[auth_token.session_id, the_sco.id])
                should_give_scorm_access = True
        if should_give_scorm_access:
            scorm_player_path = urlparse(settings.SECURE_MEDIA_URL+'scorm_player/')[2]
            mc.paths.append(scorm_player_path)
        return scos

    def upload_course(self, request):
        """Handle SCORM course uploads

        This method will inspect the SCORM ZIP archive to make sure it meets various sanity
        checks, and if it does it will store the course data in the MEDIA directory and make
        database entries to suit.

        :param request: The Django HTTP request
        :type request:  HttpRequest
        :return:        An HttpResponse indicating whether the request was successful or not
        :rtype: HttpResponse

        """
        try:
            if request.method == 'POST' and len(request.FILES) == 1 and 'auth_token' in request.POST:
                # There is only one file, but this is an easy way to get its name
                for filename in request.FILES:
                    self._process_scorm_file(request.POST['auth_token'], request.FILES[filename])
                return HttpResponse('Success!')
            else:
                return HttpResponseNotFound('Your request must include exactly one file, and a variable named \'auth_token\'.')
        except exceptions.PrException, p:
            return HttpResponseForbidden(p.get_error_msg())
        except zipfile.error:
            return HttpResponseForbidden('Your request must include a valid zip archive')
        finally:
            if 'scorm_zip_file' in dir():
                scorm_zip_file.close()

    def _check_manifest(self, manifest, scorm_zip_file):
        """This method verifies that everything contained in a SCORM manifest is present in the zip
        archive, as well as that the scorm_version is supported.  Currently, only SCORM 1.2 is supported.

        :param manifest:        An ElementTree object that is initialized to read the SCORM manifest
        :type manifest:         xml.etree.cElementTree
        :param scorm_zip_file:  A ZipFile object representing an uploaded SCORM package
        :type scorm_zip_file:   ZipFile

        """
        # Ensure that this menifest is for a SCORM 1.2 course
        metadata_element = manifest.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}metadata')
        scorm_version = metadata_element.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}schemaversion').text
        if scorm_version != '1.2':
            raise exceptions.UnsupportedScormVersionException(scorm_version)
        # Ensure that all the contents of the manifest are present
        resources_element = manifest.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}resources')
        for resource in resources_element.findall('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}resource'):
            for file_element in resource.findall('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}file'):
                # Make sure that the file described by this element exists
                required_file = file_element.get('href')
                try:
                    # If the file doesn't exist in the archive, the following line will raise a
                    # KeyError
                    scorm_zip_file.getinfo(required_file)
                except KeyError:
                    raise exceptions.ArchiveMissingFileException(required_file)

    def _create_course(self, manifest, scorm_zip_file):
        """Uses the manifest information and the zip file to put the relevant files onto the file
        system, and makes the necessary database entries.

        :param manifest:        An ElementTree object that is initialized to read the SCORM
                                manifest
        :type manifest:         xml.etree.cElementTree
        :param scorm_zip_file:  A ZipFile object representing an uploaded SCORM package
        :type scorm_zip_file:   ZipFile

        """
        course_name = self._get_course_name(manifest)
        sco_name = self._get_sco_name(manifest)
        sco_title = self._get_sco_title(manifest)
        the_course = facade.models.Course(name=course_name)
        the_course.save()
        # Let's use the course's primary key as the url_prefix since that will be unique
        url_prefix = settings.COURSE_PATH+str(the_course.id)+'/'
        # We currently only support one SCO per course
        the_sco = facade.models.Sco(data='', url=url_prefix+self._get_sco_url(manifest),
            course=the_course, name=sco_name, title=sco_title)
        the_sco.save()
        # Write the files to the FS in the secure media root under a folder called
        # sco/id/url_prefix (the model type and primary key)
        self._extract_archive(scorm_zip_file, settings.SECURE_MEDIA_ROOT+'/'+url_prefix)

    def _extract_archive(self, scorm_zip_file, filesystem_prefix):
        """Extracts the zip archive to the proper place in the filesystem

        :param scorm_zip_file:      A ZipFile object representing an uploaded SCORM package
        :type scorm_zip_file:       ZipFile
        :param filesystem_prefix:   The location on the filesystem to which the zip archive should be extracted
        :type filesystem_prefix:    str

        """
        if not os.path.isdir(filesystem_prefix):
            os.makedirs(filesystem_prefix)
        for filename in scorm_zip_file.namelist():
            filename_path = filename.split('/')
            if len(filename_path) > 1: # We need to create the subdirectories to hold the package
                directory_to_create = filesystem_prefix
                for i in range(len(filename_path)-1):
                    directory_to_create += filename_path[i]
                if not os.path.isdir(directory_to_create):
                    os.makedirs(directory_to_create)
            if not os.path.isdir(filesystem_prefix+filename):
                if filename[len(filename)-1] == '/': # We have a directory and not a normal file
                    os.makedirs(filesystem_prefix+filename)
                else:
                    with open(filesystem_prefix+filename, 'wb') as the_file:
                        the_file.write(scorm_zip_file.read(filename))

    def _get_sco_title(self, manifest):
        """Parses the manifest for the name of the course."""

        organizations_element = manifest.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}organizations')
        organization_element = organizations_element.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}organization')
        item_element = organization_element.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}item')
        title_element = item_element.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}title')
        return title_element.text

    def _get_course_name(self, manifest):
        return manifest.attrib['identifier']

    def _get_sco_name(self, manifest):
        """Parses the manifest for the name of the sco."""

        organizations_element = manifest.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}organizations')
        organization_element = organizations_element.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}organization')
        item_element = organization_element.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}item')
        return item_element.attrib['identifier']

    def _get_sco_url(self, manifest):
        """Parses the manifest for the filename of the SCO, to be used as the
        entrypoint of the SCO.  This will often return index.html.

        """
        resources_element = manifest.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}resources')
        for resource in resources_element.findall('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}resource'):
            # This is the resource we are looking for
            if resource.attrib['{http://www.adlnet.org/xsd/adlcp_rootv1p2}scormtype'] == 'sco':
                return resource.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}file').attrib['href']

    @transaction.commit_on_success
    def _process_scorm_file(self, auth_token, scorm_file):
        # Make sure that the user is allowed to upload a scorm course
        if not isinstance(auth_token, facade.models.AuthToken):
            auth_token = Utils.get_auth_token_object(auth_token)
        facade.subsystems.Authorizer().check_arbitrary_permissions(auth_token, 'upload_scorm_course')
        scorm_zip_file = zipfile.ZipFile(scorm_file)
        manifest = scorm_zip_file.read('imsmanifest.xml')
        manifest = ElementTree.XML(manifest)
        self._check_manifest(manifest, scorm_zip_file)
        self._create_course(manifest, scorm_zip_file)

# vim:tabstop=4 shiftwidth=4 expandtab
