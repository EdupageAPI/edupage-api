import os
import unittest
from datetime import datetime

from edupage_api.testing import EdupageTestCase, MockSession, UnexpectedRequestError
from edupage_api.timeline import EventType

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
NOTIFICATIONS_FIXTURE = os.path.join(FIXTURES_DIR, "notifications.json")


class NotificationsTest(EdupageTestCase):
    """Tests for get_notifications() using a pre-recorded fixture.

    These tests cover notification parsing without any live network access.
    The fixture contains two synthetic timeline items: one school-wide message
    and one homework notification.
    """

    def _get_notifications(self):
        edupage = self.get_edupage(NOTIFICATIONS_FIXTURE)
        return edupage.get_notifications()

    # ------------------------------------------------------------------
    # Basic count / structure
    # ------------------------------------------------------------------

    def test_returns_two_notifications(self):
        notifications = self._get_notifications()
        self.assertEqual(len(notifications), 2)

    # ------------------------------------------------------------------
    # First notification — school-wide message
    # ------------------------------------------------------------------

    def test_first_notification_event_type(self):
        notifications = self._get_notifications()
        self.assertEqual(notifications[0].event_type, EventType.MESSAGE)

    def test_first_notification_text(self):
        notifications = self._get_notifications()
        self.assertEqual(notifications[0].text, "Hello from school")

    def test_first_notification_timestamp(self):
        notifications = self._get_notifications()
        self.assertEqual(
            notifications[0].timestamp,
            datetime(2024, 1, 15, 10, 30, 0),
        )

    def test_first_notification_reaction_count(self):
        notifications = self._get_notifications()
        self.assertEqual(notifications[0].reaction_count, 3)

    def test_first_notification_not_starred(self):
        notifications = self._get_notifications()
        self.assertFalse(notifications[0].is_starred)

    def test_first_notification_not_done(self):
        notifications = self._get_notifications()
        self.assertFalse(notifications[0].is_done)

    def test_first_notification_not_removed(self):
        notifications = self._get_notifications()
        self.assertFalse(notifications[0].is_removed)

    def test_first_notification_created_at(self):
        notifications = self._get_notifications()
        self.assertEqual(
            notifications[0].created_at,
            datetime(2024, 1, 15, 10, 28, 0),
        )

    # ------------------------------------------------------------------
    # Second notification — homework (done and starred)
    # ------------------------------------------------------------------

    def test_second_notification_event_type(self):
        notifications = self._get_notifications()
        self.assertEqual(notifications[1].event_type, EventType.HOMEWORK)

    def test_second_notification_is_starred(self):
        notifications = self._get_notifications()
        self.assertTrue(notifications[1].is_starred)

    def test_second_notification_is_done(self):
        notifications = self._get_notifications()
        self.assertTrue(notifications[1].is_done)

    def test_second_notification_done_at(self):
        notifications = self._get_notifications()
        self.assertEqual(
            notifications[1].done_at,
            datetime(2024, 2, 20, 9, 15, 0),
        )

    # ------------------------------------------------------------------
    # MockSession behaviour
    # ------------------------------------------------------------------

    def test_get_edupage_sets_is_logged_in(self):
        edupage = self.get_edupage(NOTIFICATIONS_FIXTURE)
        self.assertTrue(edupage.is_logged_in)

    def test_get_edupage_sets_subdomain(self):
        edupage = self.get_edupage(NOTIFICATIONS_FIXTURE)
        self.assertEqual(edupage.subdomain, "testschool")

    def test_get_edupage_sets_username(self):
        edupage = self.get_edupage(NOTIFICATIONS_FIXTURE)
        self.assertEqual(edupage.username, "test.student")

    def test_get_edupage_sets_gsec_hash(self):
        edupage = self.get_edupage(NOTIFICATIONS_FIXTURE)
        self.assertEqual(edupage.gsec_hash, "testhash123")

    def test_get_edupage_installs_mock_session(self):
        edupage = self.get_edupage(NOTIFICATIONS_FIXTURE)
        self.assertIsInstance(edupage.session, MockSession)

    def test_unexpected_request_raises_error(self):
        """MockSession must raise UnexpectedRequestError for unmapped URLs."""
        edupage = self.get_edupage(NOTIFICATIONS_FIXTURE)
        # The fixture has an empty requests list, so any HTTP call should fail.
        with self.assertRaises(UnexpectedRequestError):
            edupage.session.get("https://testschool.edupage.org/unexpected/")


if __name__ == "__main__":
    unittest.main()
