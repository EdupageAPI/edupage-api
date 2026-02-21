"""Shared fixtures for edupage_api tests."""

import json
import pytest

from unittest.mock import MagicMock


def make_edupage_mock(data=None, subdomain="testschool", is_logged_in=True):
    """Create a mock EdupageModule with sensible defaults."""
    edupage = MagicMock()
    edupage.subdomain = subdomain
    edupage.is_logged_in = is_logged_in
    edupage.data = data if data is not None else {
        "dbi": {
            "teachers": {},
            "students": {},
            "parents": {},
            "classrooms": {},
            "classes": {},
            "subjects": {},
        },
        "items": [],
        "userProps": {},
    }
    return edupage


def make_timeline_item(
    timeline_id="100",
    typ="sprava",
    timestamp="2025-01-15 10:30:00",
    text="Test message",
    user_meno="*",
    vlastnik_meno="*",
    data_dict=None,
    pocet_reakcii=0,
    cas_pridania=None,
    removed=None,
):
    """Create a raw timeline item dict as returned by Edupage."""
    if data_dict is None:
        data_dict = {"messageContent": "Test message content"}

    item = {
        "timelineid": timeline_id,
        "typ": typ,
        "timestamp": timestamp,
        "text": text,
        "user_meno": user_meno,
        "vlastnik_meno": vlastnik_meno,
        "data": json.dumps(data_dict),
        "pocet_reakcii": pocet_reakcii,
    }
    if cas_pridania is not None:
        item["cas_pridania"] = cas_pridania
    if removed is not None:
        item["removed"] = removed
    return item


@pytest.fixture
def edupage_mock():
    """Provide a basic mock edupage object."""
    return make_edupage_mock()
