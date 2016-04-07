"""Acceptance tests for LMS-hosted Programs pages"""
from bok_choy.web_app_test import WebAppTest
from nose.plugins.attrib import attr

from ...fixtures import PROGRAMS_STUB_URL
from ...fixtures.config import ConfigModelFixture
from ...fixtures.programs import ProgramsFixture
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.programs import ProgramListingPage


class BaseProgramListingPageTest(WebAppTest):
    """Base class used for program listing page tests."""
    def setUp(self):
        pass


class ProgramListingPageTest(WebAppTest):
    """Verify user-facing behavior of the program listing page."""
    def setUp(self):
        super(ProgramListingPageTest, self).setUp()

        self.auth_page = AutoAuthPage(self.browser)
        self.listing_page = ProgramListingPage(self.browser)

        self.auth_page.visit()

    # TODO: Mixin?
    def set_programs_api_configuration(self, is_enabled=False, api_version=1, api_url=PROGRAMS_STUB_URL,
                                       js_path='/js', css_path='/css'):
        """Dynamically adjusts the Programs config model during tests."""
        ConfigModelFixture('/config/programs', {
            'enabled': is_enabled,
            'enable_studio_tab': is_enabled,
            'enable_student_dashboard': is_enabled,
            'api_version_number': api_version,
            'internal_service_url': api_url,
            'public_service_url': api_url,
            'authoring_app_js_path': js_path,
            'authoring_app_css_path': css_path,
            'cache_ttl': 0
        }).install()

    def test_no_enrollments(self):
        """Verify that no cards appear when the user has no enrollments."""
        ProgramsFixture().install_programs([
            ('Foo Bar', 'Baz'),
        ])
        self.set_programs_api_configuration(is_enabled=True)

        self.listing_page.visit()

        # TODO: Verify empty state messaging.
        self.assertFalse(self.listing_page.are_cards_present)

    def test_no_programs(self):
        """
        Verify that no cards appear when the user has enrollments
        but none are included in an active program.
        """
        pass

    def test_enrollments_and_programs(self):
        """
        Verify that cards appear when the user has enrollments
        which are included in at least one active program.
        """
        pass


@attr('a11y')
class ProgramListingPageA11yTest(WebAppTest):
    """Test program listing page accessibility."""

    def test_empty_a11y(self):
        """Test a11y of the page's empty state."""
        pass

        # self.assertEqual(len(self.listing_page.cards), 0)
        # self.listing_page.a11y_audit.check_for_accessibility_errors()

    def test_single_card_a11y(self):
        """Test a11y when one card is present."""
        pass

        # self.assertEqual(len(self.listing_page.cards), 1)
        # self.listing_page.a11y_audit.check_for_accessibility_errors()

    def test_cards_a11y(self):
        """Test a11y when multiple cards are present."""
        pass

        # self.assertGreaterEqual(len(self.listing_page.cards), 1)
        # self.listing_page.a11y_audit.check_for_accessibility_errors()
