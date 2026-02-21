"""Tests for edupage_api.timeline — focusing on the new fields and userProps parsing."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from edupage_api.timeline import TimelineEvent, TimelineEvents, EventType
from tests.conftest import make_edupage_mock, make_timeline_item


# ---------------------------------------------------------------------------
# 1. TimelineEvent dataclass — new fields and defaults
# ---------------------------------------------------------------------------


class TestTimelineEventDataclass:
    """Test TimelineEvent dataclass field defaults and backward compatibility."""

    def test_new_fields_have_correct_defaults(self):
        """New optional fields should default to False/None/0."""
        event = TimelineEvent(
            event_id=1,
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            text="Hello",
            author="Author",
            recipient="Recipient",
            event_type=EventType.MESSAGE,
            additional_data={},
        )
        assert event.is_done is False
        assert event.done_at is None
        assert event.is_starred is False
        assert event.reaction_count == 0
        assert event.created_at is None
        assert event.is_removed is False

    def test_backward_compatibility_positional_args(self):
        """Constructing with only the original positional args should work."""
        event = TimelineEvent(
            42,
            datetime(2025, 6, 1),
            "text",
            "author",
            "recipient",
            EventType.HOMEWORK,
            {"key": "value"},
        )
        assert event.event_id == 42
        assert event.text == "text"
        assert event.is_done is False

    def test_all_new_fields_can_be_set(self):
        """All new fields can be explicitly set via keyword arguments."""
        done_ts = datetime(2025, 3, 1, 12, 0, 0)
        created_ts = datetime(2025, 2, 28, 8, 0, 0)
        event = TimelineEvent(
            event_id=99,
            timestamp=datetime(2025, 3, 1),
            text="Done item",
            author="teacher",
            recipient="student",
            event_type=EventType.GRADE,
            additional_data={},
            is_done=True,
            done_at=done_ts,
            is_starred=True,
            reaction_count=5,
            created_at=created_ts,
            is_removed=True,
        )
        assert event.is_done is True
        assert event.done_at == done_ts
        assert event.is_starred is True
        assert event.reaction_count == 5
        assert event.created_at == created_ts
        assert event.is_removed is True


# ---------------------------------------------------------------------------
# 2. __parse_items with userProps
# ---------------------------------------------------------------------------


class TestParseItemsUserProps:
    """Test that __parse_items correctly reads userProps for done/starred state."""

    def _parse(self, items, user_props=None, edupage=None):
        """Helper to call the private __parse_items via name mangling."""
        if edupage is None:
            edupage = make_edupage_mock()
        te = TimelineEvents(edupage)
        # Access through name mangling
        return te._TimelineEvents__parse_items(items, user_props)

    def test_item_with_done_max_cas_is_done(self):
        """An item whose userProps has doneMaxCas should be is_done=True with correct done_at."""
        item = make_timeline_item(timeline_id="200")
        user_props = {
            "200": {
                "doneMaxCas": "2025-03-10 14:30:00",
            }
        }
        results = self._parse([item], user_props)
        assert len(results) == 1
        event = results[0]
        assert event.is_done is True
        assert event.done_at == datetime(2025, 3, 10, 14, 30, 0)

    def test_item_with_starred_is_starred(self):
        """An item whose userProps has starred='1' should be is_starred=True."""
        item = make_timeline_item(timeline_id="300")
        user_props = {
            "300": {
                "starred": "1",
            }
        }
        results = self._parse([item], user_props)
        assert len(results) == 1
        assert results[0].is_starred is True

    def test_item_with_starred_zero_is_not_starred(self):
        """An item whose userProps has starred='0' should be is_starred=False."""
        item = make_timeline_item(timeline_id="301")
        user_props = {
            "301": {
                "starred": "0",
            }
        }
        results = self._parse([item], user_props)
        assert results[0].is_starred is False

    def test_item_with_empty_user_props_gets_defaults(self):
        """An item with empty userProps should get is_done=False, is_starred=False."""
        item = make_timeline_item(timeline_id="400")
        user_props = {}
        results = self._parse([item], user_props)
        assert len(results) == 1
        event = results[0]
        assert event.is_done is False
        assert event.done_at is None
        assert event.is_starred is False

    def test_item_with_missing_user_props_gets_defaults(self):
        """When user_props is None, defaults should be used."""
        item = make_timeline_item(timeline_id="401")
        results = self._parse([item], None)
        assert len(results) == 1
        event = results[0]
        assert event.is_done is False
        assert event.done_at is None
        assert event.is_starred is False

    def test_item_with_empty_string_done_max_cas(self):
        """An empty-string doneMaxCas should result in is_done=False (bool('') is False)."""
        item = make_timeline_item(timeline_id="500")
        user_props = {
            "500": {
                "doneMaxCas": "",
            }
        }
        results = self._parse([item], user_props)
        event = results[0]
        assert event.is_done is False
        assert event.done_at is None

    def test_item_with_invalid_done_max_cas_format(self):
        """An invalid doneMaxCas format should not crash; is_done derived from done_at."""
        item = make_timeline_item(timeline_id="600")
        user_props = {
            "600": {
                "doneMaxCas": "not-a-date",
            }
        }
        results = self._parse([item], user_props)
        event = results[0]
        # Parsing fails so done_at is None, and is_done is derived from done_at
        assert event.is_done is False
        assert event.done_at is None

    def test_user_props_with_non_dict_value(self):
        """If a userProps entry is not a dict (e.g., a string), it should be treated as empty."""
        item = make_timeline_item(timeline_id="700")
        user_props = {
            "700": "some-string-not-dict",
        }
        results = self._parse([item], user_props)
        event = results[0]
        assert event.is_done is False
        assert event.is_starred is False

    def test_both_done_and_starred(self):
        """An item can be both done and starred simultaneously."""
        item = make_timeline_item(timeline_id="800")
        user_props = {
            "800": {
                "doneMaxCas": "2025-06-01 09:00:00",
                "starred": "1",
            }
        }
        results = self._parse([item], user_props)
        event = results[0]
        assert event.is_done is True
        assert event.done_at == datetime(2025, 6, 1, 9, 0, 0)
        assert event.is_starred is True


# ---------------------------------------------------------------------------
# 3. Raw event fields — pocet_reakcii, cas_pridania, removed
# ---------------------------------------------------------------------------


class TestRawEventFields:
    """Test parsing of pocet_reakcii, cas_pridania, removed from raw events."""

    def _parse(self, items, user_props=None):
        edupage = make_edupage_mock()
        te = TimelineEvents(edupage)
        return te._TimelineEvents__parse_items(items, user_props)

    def test_reaction_count_parsed(self):
        """pocet_reakcii should be parsed into reaction_count."""
        item = make_timeline_item(timeline_id="901", pocet_reakcii=7)
        results = self._parse([item])
        assert results[0].reaction_count == 7

    def test_reaction_count_string_parsed(self):
        """pocet_reakcii as a string should be parsed to int."""
        item = make_timeline_item(timeline_id="902", pocet_reakcii="3")
        results = self._parse([item])
        assert results[0].reaction_count == 3

    def test_reaction_count_missing_defaults_to_zero(self):
        """Missing pocet_reakcii should default to 0."""
        item = make_timeline_item(timeline_id="903")
        # Remove the key entirely
        del item["pocet_reakcii"]
        results = self._parse([item])
        assert results[0].reaction_count == 0

    def test_reaction_count_invalid_defaults_to_zero(self):
        """Invalid (non-numeric) pocet_reakcii should default to 0."""
        item = make_timeline_item(timeline_id="904", pocet_reakcii="abc")
        results = self._parse([item])
        assert results[0].reaction_count == 0

    def test_created_at_parsed(self):
        """cas_pridania should be parsed into created_at datetime."""
        item = make_timeline_item(
            timeline_id="905", cas_pridania="2025-04-20 16:45:00"
        )
        results = self._parse([item])
        assert results[0].created_at == datetime(2025, 4, 20, 16, 45, 0)

    def test_created_at_missing_is_none(self):
        """Missing cas_pridania should result in created_at=None."""
        item = make_timeline_item(timeline_id="906")
        # cas_pridania not included by default
        results = self._parse([item])
        assert results[0].created_at is None

    def test_created_at_invalid_format_is_none(self):
        """Invalid cas_pridania format should result in created_at=None."""
        item = make_timeline_item(timeline_id="907", cas_pridania="invalid-date")
        results = self._parse([item])
        assert results[0].created_at is None

    def test_removed_true(self):
        """removed='1' should result in is_removed=True."""
        item = make_timeline_item(timeline_id="908", removed="1")
        results = self._parse([item])
        assert results[0].is_removed is True

    def test_removed_false(self):
        """removed='0' should result in is_removed=False."""
        item = make_timeline_item(timeline_id="909", removed="0")
        results = self._parse([item])
        assert results[0].is_removed is False

    def test_removed_missing(self):
        """Missing removed should result in is_removed=False."""
        item = make_timeline_item(timeline_id="910")
        results = self._parse([item])
        assert results[0].is_removed is False


# ---------------------------------------------------------------------------
# 4. get_notifications and get_notifications_history pass userProps
# ---------------------------------------------------------------------------


class TestGetNotificationsUserProps:
    """Test that public methods pass userProps correctly to __parse_items."""

    def test_get_notifications_passes_user_props(self):
        """get_notifications should read userProps from edupage.data and pass to __parse_items."""
        user_props = {
            "10": {"starred": "1", "doneMaxCas": "2025-05-01 12:00:00"}
        }
        timeline_item = make_timeline_item(timeline_id="10")

        edupage = make_edupage_mock(
            data={
                "dbi": {
                    "teachers": {},
                    "students": {},
                    "parents": {},
                    "classrooms": {},
                    "classes": {},
                    "subjects": {},
                },
                "items": [timeline_item],
                "userProps": user_props,
            }
        )

        te = TimelineEvents(edupage)
        results = te.get_notifications()

        assert len(results) == 1
        assert results[0].is_starred is True
        assert results[0].is_done is True
        assert results[0].done_at == datetime(2025, 5, 1, 12, 0, 0)

    def test_get_notifications_with_no_user_props(self):
        """get_notifications when userProps is missing from data should still work."""
        timeline_item = make_timeline_item(timeline_id="11")

        edupage = make_edupage_mock(
            data={
                "dbi": {
                    "teachers": {},
                    "students": {},
                    "parents": {},
                    "classrooms": {},
                    "classes": {},
                    "subjects": {},
                },
                "items": [timeline_item],
                # No userProps key
            }
        )

        te = TimelineEvents(edupage)
        results = te.get_notifications()

        assert len(results) == 1
        assert results[0].is_starred is False
        assert results[0].is_done is False

    def test_get_notifications_history_passes_timeline_user_props(self):
        """get_notifications_history should use timelineUserProps from response."""
        user_props = {
            "20": {"starred": "1"}
        }
        timeline_item = make_timeline_item(timeline_id="20")

        response_data = {
            "timelineItems": [timeline_item],
            "timelineUserProps": user_props,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        edupage = make_edupage_mock()
        edupage.session.post.return_value = mock_response

        te = TimelineEvents(edupage)
        results = te.get_notifications_history(datetime(2025, 1, 1).date())

        assert len(results) == 1
        assert results[0].is_starred is True

    def test_get_notifications_history_falls_back_to_cached_user_props(self):
        """When timelineUserProps is missing from response, fall back to edupage.data userProps."""
        cached_props = {
            "30": {"doneMaxCas": "2025-06-15 08:00:00"}
        }
        timeline_item = make_timeline_item(timeline_id="30")

        response_data = {
            "timelineItems": [timeline_item],
            # No timelineUserProps
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        edupage = make_edupage_mock(
            data={
                "dbi": {
                    "teachers": {},
                    "students": {},
                    "parents": {},
                    "classrooms": {},
                    "classes": {},
                    "subjects": {},
                },
                "items": [],
                "userProps": cached_props,
            }
        )
        edupage.session.post.return_value = mock_response

        te = TimelineEvents(edupage)
        results = te.get_notifications_history(datetime(2025, 1, 1).date())

        assert len(results) == 1
        assert results[0].is_done is True
        assert results[0].done_at == datetime(2025, 6, 15, 8, 0, 0)


# ---------------------------------------------------------------------------
# 5. Edge cases — items without timelineid, EventType parsing
# ---------------------------------------------------------------------------


class TestParseItemsEdgeCases:
    """Edge-case coverage for __parse_items."""

    def _parse(self, items, user_props=None):
        edupage = make_edupage_mock()
        te = TimelineEvents(edupage)
        return te._TimelineEvents__parse_items(items, user_props)

    def test_item_without_timelineid_is_skipped(self):
        """Items missing timelineid should be silently skipped."""
        item = make_timeline_item(timeline_id="50")
        item_no_id = make_timeline_item()
        item_no_id["timelineid"] = None

        results = self._parse([item_no_id, item])
        assert len(results) == 1
        assert results[0].event_id == 50

    def test_empty_items_list(self):
        """An empty items list should return an empty result."""
        results = self._parse([])
        assert results == []

    def test_event_type_parsed_correctly(self):
        """Event type string should be parsed into the EventType enum."""
        item = make_timeline_item(timeline_id="60", typ="homework")
        results = self._parse([item])
        assert results[0].event_type == EventType.HOMEWORK

    def test_multiple_items_parsed(self):
        """Multiple items should all be parsed."""
        item1 = make_timeline_item(timeline_id="70", text="First")
        item2 = make_timeline_item(timeline_id="71", text="Second")
        user_props = {
            "70": {"starred": "1"},
            "71": {"doneMaxCas": "2025-01-01 00:00:00"},
        }
        results = self._parse([item1, item2], user_props)
        assert len(results) == 2
        assert results[0].is_starred is True
        assert results[0].is_done is False
        assert results[1].is_starred is False
        assert results[1].is_done is True
