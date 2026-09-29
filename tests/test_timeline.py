import json
import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch

from edupage_api import Edupage
from edupage_api.timeline import EventType


class TimelineParsingTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.subdomain = "example"
        self.api.data = {"items": [], "userProps": {}}
        self.api.session = Mock()
        person_lookup = patch(
            "edupage_api.timeline.DbiHelper.fetch_person_data_by_name",
            return_value=None,
        )
        person_lookup.start()
        self.addCleanup(person_lookup.stop)

    @staticmethod
    def message(text="Original message", data=None, event_type="sprava"):
        return {
            "timelineid": "123",
            "timestamp": "2026-09-01 08:00:00",
            "text": text,
            "typ": event_type,
            "data": json.dumps(data if data is not None else {}),
            "user_meno": "Example recipient",
            "vlastnik_meno": "Example author",
        }

    def parse(self, event, history=False, props=None):
        if history:
            self.api.session.post.return_value.status_code = 200
            self.api.session.post.return_value.json.return_value = {
                "timelineItems": [event],
                "timelineUserProps": props,
            }
            events = self.api.get_notification_history(date(2026, 9, 1))
        else:
            self.api.data["items"] = [event]
            self.api.data["userProps"] = props
            events = self.api.get_notifications()
        self.assertEqual(len(events), 1)
        return events[0]

    def test_message_body_is_independent_of_placeholder_language(self):
        body = "<p>Full message body with diacritics: příští týden.</p>"
        for history in (False, True):
            for placeholder in (
                "Důležitá zpráva: otevřete aplikaci",
                "Dôležitá správa: otvorte aplikáciu",
                "Important message: open the application",
            ):
                with self.subTest(history=history, placeholder=placeholder):
                    event = self.parse(
                        self.message(placeholder, {"messageContent": body}),
                        history=history,
                    )
                    self.assertEqual(event.text, body)
                    self.assertEqual(event.additional_data["messageContent"], body)
                    self.assertEqual(event.event_type, EventType.MESSAGE)
                    self.assertEqual(event.event_id, 123)

    def test_missing_or_invalid_body_preserves_original_message(self):
        for data in (
            {},
            {"messageContent": None},
            {"messageContent": ""},
            {"messageContent": "  "},
            {"messageContent": []},
            {"messageContent": 1},
        ):
            with self.subTest(data=data):
                text = "Dôležitá správa: original text"
                self.assertEqual(self.parse(self.message(text, data)).text, text)

    def test_other_event_types_do_not_use_message_content(self):
        event = self.parse(
            self.message(
                "Grade notification", {"messageContent": "Other data"}, "znamka"
            )
        )
        self.assertEqual(event.text, "Grade notification")

    def test_array_or_null_event_data_preserves_original_text(self):
        for event_type in ("sprava", "znamka", "h_clearcache"):
            for raw_data in ("[]", "null"):
                with self.subTest(event_type=event_type, data=raw_data):
                    raw = self.message("Original text", event_type=event_type)
                    raw["data"] = raw_data
                    self.assertEqual(self.parse(raw).text, "Original text")

    def test_empty_history_user_properties_accept_list_dict_or_none(self):
        for props in ([], {}, None):
            with self.subTest(props=props):
                event = self.parse(self.message(), history=True, props=props)
                self.assertEqual(event.text, "Original message")
                self.assertFalse(event.is_starred)
                self.assertFalse(event.is_done)
                self.assertIsNone(event.done_at)

    def test_history_preserves_nonempty_user_properties(self):
        props = {"123": {"starred": "1", "doneMaxCas": "2026-09-02 09:00:00"}}
        event = self.parse(self.message(), history=True, props=props)
        self.assertTrue(event.is_starred)
        self.assertTrue(event.is_done)
        self.assertEqual(event.done_at, datetime(2026, 9, 2, 9))

    def test_missing_history_properties_fall_back_to_cached_properties(self):
        self.api.data["userProps"] = {"123": {"starred": "1"}}
        self.assertTrue(self.parse(self.message(), history=True).is_starred)


if __name__ == "__main__":
    unittest.main()
