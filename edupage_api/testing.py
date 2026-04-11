"""Testing utilities for edupage-api.

This module provides three components that together allow writing offline,
reproducible tests against the edupage-api library without a real Edupage
account or live network access:

* :class:`EduRecorder` — context manager that intercepts a live session and
  writes every HTTP exchange (plus the parsed ``edupage.data`` blob) to a JSON
  fixture file.

* :class:`MockSession` — a :class:`requests.Session` replacement that replays
  responses from a previously recorded fixture file instead of making real
  network requests.

* :class:`EdupageTestCase` — a :class:`unittest.TestCase` base class that
  exposes :meth:`~EdupageTestCase.get_edupage`, a factory that loads a fixture,
  wires up a :class:`MockSession`, and returns a fully-initialised
  :class:`~edupage_api.Edupage` instance ready for testing — without any login
  flow.

Typical workflow
----------------

1. **Record** a real session once (requires a real account)::

       from edupage_api import Edupage
       from edupage_api.testing import EduRecorder

       edupage = Edupage()
       with EduRecorder(edupage, "tests/fixtures/grades.json"):
           edupage.login("user", "pass", "myschool")
           edupage.get_grades()
       # fixture file written on context-manager exit

2. *Optionally* anonymise the fixture by hand or via the ``anonymiser``
   callback.

3. **Replay** in tests (no credentials, no network)::

       from edupage_api.testing import EdupageTestCase

       class GradesTest(EdupageTestCase):
           def test_grade_count(self):
               edupage = self.get_edupage("tests/fixtures/grades.json")
               grades = edupage.get_grades()
               self.assertEqual(len(grades), 5)

Fixture format
--------------

::

    {
        "meta": {
            "subdomain": "myschool",
            "username":  "student123",
            "gsec_hash": "abc123"
        },
        "data": { /* full edupage.data dict (userhome payload) */ },
        "requests": [
            {
                "method": "GET",
                "url": "https://myschool.edupage.org/znamky/",
                "response": {
                    "status_code": 200,
                    "text": "... page body ..."
                }
            }
        ]
    }

Multiple fixtures can be kept for the same feature to cover different server
response variants (e.g. ``grades_school_a.json`` vs ``grades_school_b.json``).
"""

import json
import unittest
from typing import Callable, Optional

from requests import Response, Session
from requests.structures import CaseInsensitiveDict


class UnexpectedRequestError(Exception):
    """Raised by :class:`MockSession` when a request has no matching fixture entry.

    This keeps tests deterministic: a missing fixture entry is a hard error
    rather than a silent network call.
    """


def _make_response(status_code: int, text: str, url: str) -> Response:
    """Build a minimal :class:`requests.Response` from raw fixture data."""
    response = Response()
    response.status_code = status_code
    response._content = text.encode("utf-8")
    response.encoding = "utf-8"
    response.url = url
    response.headers = CaseInsensitiveDict(
        {"Content-Type": "text/html; charset=utf-8"}
    )
    return response


class MockSession(Session):
    """A :class:`requests.Session` that serves pre-recorded responses.

    Responses are looked up by ``(HTTP method, URL)`` key.  If the same
    ``(method, URL)`` pair appears more than once in the fixture, responses are
    served in the order they were recorded; the last recorded response is
    repeated once exhausted.

    Args:
        requests_data: The ``"requests"`` list from a loaded fixture dict.

    Raises:
        UnexpectedRequestError: When a ``(method, URL)`` pair is received that
            has no entry in the fixture.
    """

    def __init__(self, requests_data: list):
        super().__init__()
        # (method, url) -> ordered list of response dicts
        self._mock_responses: dict[tuple[str, str], list[dict]] = {}
        for entry in requests_data:
            key = (entry["method"].upper(), entry["url"])
            self._mock_responses.setdefault(key, []).append(entry["response"])

    def send(self, request, **kwargs):
        key = (request.method.upper(), request.url)
        responses = self._mock_responses.get(key)
        if not responses:
            raise UnexpectedRequestError(
                f"No mock response for {request.method} {request.url}. "
                "Add this request/response pair to your fixture file."
            )
        # Consume the first entry; keep the last one so it can be reused.
        response_data = responses.pop(0) if len(responses) > 1 else responses[0]
        return _make_response(
            response_data["status_code"], response_data["text"], request.url
        )


class EduRecorder:
    """Context manager that records all HTTP exchanges to a JSON fixture file.

    Wrap any block of :class:`~edupage_api.Edupage` calls with this context
    manager.  On exit the recorded request/response pairs *and* the current
    ``edupage.data`` blob are written to *fixture_path* as a single JSON file.

    Args:
        edupage: The :class:`~edupage_api.Edupage` instance whose session will
            be instrumented.
        fixture_path: Path where the fixture JSON file will be written.
        anonymiser: Optional callable ``(fixture: dict) -> dict`` applied to
            the fixture before writing.  Use it to scrub personal data (real
            names, grades, …) before committing the file to version control.

    Example::

        from edupage_api import Edupage
        from edupage_api.testing import EduRecorder

        def scrub(fixture):
            fixture["meta"]["username"] = "anonymised"
            return fixture

        edupage = Edupage()
        with EduRecorder(edupage, "tests/fixtures/grades.json", anonymiser=scrub):
            edupage.login("real_user", "real_pass", "myschool")
            edupage.get_grades()
    """

    def __init__(
        self,
        edupage,
        fixture_path: str,
        anonymiser: Optional[Callable[[dict], dict]] = None,
    ):
        self.edupage = edupage
        self.fixture_path = fixture_path
        self.anonymiser = anonymiser
        self._captured: list = []
        self._original_send = None

    def __enter__(self):
        self._original_send = self.edupage.session.send

        def _recording_send(request, **kwargs):
            response = self._original_send(request, **kwargs)
            self._captured.append(
                {
                    "method": request.method,
                    "url": request.url,
                    "response": {
                        "status_code": response.status_code,
                        "text": response.text,
                    },
                }
            )
            return response

        self.edupage.session.send = _recording_send
        return self

    def __exit__(self, *args):
        self.edupage.session.send = self._original_send

        fixture = {
            "meta": {
                "subdomain": self.edupage.subdomain,
                "username": self.edupage.username,
                "gsec_hash": self.edupage.gsec_hash,
            },
            "data": self.edupage.data,
            "requests": self._captured,
        }

        if self.anonymiser is not None:
            fixture = self.anonymiser(fixture)

        with open(self.fixture_path, "w", encoding="utf-8") as f:
            json.dump(fixture, f, indent=2, ensure_ascii=False)


class EdupageTestCase(unittest.TestCase):
    """Base :class:`unittest.TestCase` with helpers for fixture-based testing.

    Subclass this instead of :class:`unittest.TestCase` to get access to
    :meth:`get_edupage`.

    Example::

        import os
        from edupage_api.testing import EdupageTestCase

        FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

        class MyTest(EdupageTestCase):
            def test_something(self):
                edupage = self.get_edupage(os.path.join(FIXTURES, "my_feature.json"))
                result = edupage.some_method()
                self.assertEqual(result, expected)
    """

    def get_edupage(self, fixture_path: str):
        """Load a fixture and return a ready-to-use :class:`~edupage_api.Edupage` instance.

        The returned instance has:

        * ``data`` populated from the fixture's ``"data"`` field.
        * ``subdomain``, ``username``, ``gsec_hash`` set from ``"meta"``.
        * ``is_logged_in`` set to ``True`` (bypasses the ``@logged_in`` guard).
        * ``session`` replaced with a :class:`MockSession` backed by the
          fixture's ``"requests"`` list — no real network access occurs.

        Args:
            fixture_path: Path to a JSON fixture file produced by
                :class:`EduRecorder` (or hand-crafted).

        Returns:
            A configured :class:`~edupage_api.Edupage` instance.

        Note:
            Any ``"meta"`` fields or the ``"data"`` key that are absent from the
            fixture will result in the corresponding ``Edupage`` attribute being
            ``None``.  Hand-crafted fixtures must include at minimum a
            ``"data"`` key; missing ``"meta"`` values will cause
            ``AttributeError`` or ``MissingDataException`` in methods that rely
            on ``subdomain``, ``username``, or ``gsec_hash``.
        """
        # Import here to avoid a circular import at module level
        # (testing.py lives inside the edupage_api package).
        from edupage_api import Edupage

        with open(fixture_path, encoding="utf-8") as f:
            fixture = json.load(f)

        edupage = Edupage()

        meta = fixture.get("meta", {})
        edupage.subdomain = meta.get("subdomain")
        edupage.username = meta.get("username")
        edupage.gsec_hash = meta.get("gsec_hash")
        edupage.data = fixture.get("data")
        edupage.is_logged_in = True

        edupage.session = MockSession(fixture.get("requests", []))

        return edupage
