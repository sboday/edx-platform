"""
Test for LMS courseware app.
"""
from textwrap import dedent
from unittest import TestCase

from django.core.urlresolvers import reverse
import mock
from nose.plugins.attrib import attr
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_XML_MODULESTORE as XML_MODULESTORE
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_TOY_MODULESTORE as TOY_MODULESTORE
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@attr('shard_1')
class ActivateLoginTest(LoginEnrollmentTestCase):
    """
    Test logging in and logging out.
    """
    def setUp(self):
        super(ActivateLoginTest, self).setUp()
        self.setup_user()

    def test_activate_login(self):
        """
        Test login -- the setup function does all the work.
        """
        pass

    def test_logout(self):
        """
        Test logout -- setup function does login.
        """
        self.logout()


class PageLoaderTestCase(LoginEnrollmentTestCase):
    """
    Base class that adds a function to load all pages in a modulestore.
    """

    def check_all_pages_load(self, course_key):
        """
        Assert that all pages in the course load correctly.
        `course_id` is the ID of the course to check.
        """

        store = modulestore()

        # Enroll in the course before trying to access pages
        course = store.get_course(course_key)
        self.enroll(course, True)

        # Search for items in the course
        items = store.get_items(course_key)

        if len(items) < 1:
            self.fail('Could not retrieve any items from course')

        # Try to load each item in the course
        for descriptor in items:

            if descriptor.location.category == 'about':
                self._assert_loads('about_course',
                                   {'course_id': course_key.to_deprecated_string()},
                                   descriptor)

            elif descriptor.location.category == 'static_tab':
                kwargs = {'course_id': course_key.to_deprecated_string(),
                          'tab_slug': descriptor.location.name}
                self._assert_loads('static_tab', kwargs, descriptor)

            elif descriptor.location.category == 'course_info':
                self._assert_loads('info', {'course_id': course_key.to_deprecated_string()},
                                   descriptor)

            else:

                kwargs = {'course_id': course_key.to_deprecated_string(),
                          'location': descriptor.location.to_deprecated_string()}

                self._assert_loads('jump_to', kwargs, descriptor,
                                   expect_redirect=True,
                                   check_content=True)

    def _assert_loads(self, django_url, kwargs, descriptor,
                      expect_redirect=False,
                      check_content=False):
        """
        Assert that the url loads correctly.
        If expect_redirect, then also check that we were redirected.
        If check_content, then check that we don't get
        an error message about unavailable modules.
        """

        url = reverse(django_url, kwargs=kwargs)
        response = self.client.get(url, follow=True)

        if response.status_code != 200:
            self.fail('Status %d for page %s' %
                      (response.status_code, descriptor.location))

        if expect_redirect:
            self.assertEqual(response.redirect_chain[0][1], 302)

        if check_content:
            self.assertNotContains(response, "this module is temporarily unavailable")


@attr('shard_1')
class TestXmlCoursesLoad(ModuleStoreTestCase, PageLoaderTestCase):
    """
    Check that all pages in test courses load properly from XML.
    """
    MODULESTORE = XML_MODULESTORE

    def setUp(self):
        super(TestXmlCoursesLoad, self).setUp()
        self.setup_user()

    def test_toy_course_loads(self):
        # Load one of the XML based courses
        # Our test mapping rules allow the MixedModuleStore
        # to load this course from XML, not Mongo.
        self.check_all_pages_load(SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'))


@attr('shard_1')
class TestMongoCoursesLoad(ModuleStoreTestCase, PageLoaderTestCase):
    """
    Check that all pages in test courses load properly from Mongo.
    """
    MODULESTORE = TOY_MODULESTORE

    def setUp(self):
        super(TestMongoCoursesLoad, self).setUp()
        self.setup_user()

    @mock.patch('xmodule.course_module.requests.get')
    def test_toy_textbooks_loads(self, mock_get):
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()

        location = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall').make_usage_key('course', '2012_Fall')
        course = self.store.get_item(location)
        self.assertGreater(len(course.textbooks), 0)


@attr('shard_1')
class TestDraftModuleStore(ModuleStoreTestCase):
    def test_get_items_with_course_items(self):
        store = modulestore()

        # fix was to allow get_items() to take the course_id parameter
        store.get_items(SlashSeparatedCourseKey('abc', 'def', 'ghi'), qualifiers={'category': 'vertical'})

        # test success is just getting through the above statement.
        # The bug was that 'course_id' argument was
        # not allowed to be passed in (i.e. was throwing exception)


@attr('shard_1')
class TestLmsFieldData(TestCase):
    """
    Tests of the LmsFieldData class
    """
    def test_lms_field_data_wont_nest(self):
        # Verify that if an LmsFieldData is passed into LmsFieldData as the
        # authored_data, that it doesn't produced a nested field data.
        #
        # This fixes a bug where re-use of the same descriptor for many modules
        # would cause more and more nesting, until the recursion depth would be
        # reached on any attribute access

        # pylint: disable=protected-access
        base_authored = mock.Mock()
        base_student = mock.Mock()
        first_level = LmsFieldData(base_authored, base_student)
        second_level = LmsFieldData(first_level, base_student)
        self.assertEquals(second_level._authored_data, first_level._authored_data)
        self.assertNotIsInstance(second_level._authored_data, LmsFieldData)
