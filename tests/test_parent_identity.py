"""Server-issued parent identities and stale session state."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from edupage_api.login_session import LoginSession
from edupage_api.parent import Parent
from edupage_api.exceptions import BadCredentialsException, UnknownServerError


class ParentIdentityTests(unittest.TestCase):
    def client(self, rows):
        client = SimpleNamespace(is_logged_in=True, username="alias@example.test", subdomain="school",
                                 _account_rows=rows, _selected_child_id=1, session=Mock(),
                                 get_user_id=lambda: "Rodic1")
        client.session.get.return_value.url = "https://school.edupage.org/user/"
        return client

    def test_exact_server_row_and_alias_identity(self):
        for username in ("alias@example.test", "canonical@example.test"):
            with self.subTest(username=username):
                row = f"edupage;school;{username};rodic"
                client = self.client([row, "edupage;other;someone;rodic"])
                Parent(client).switch_to_parent()
                self.assertEqual(client.session.get.call_args.kwargs["params"], {"rid": row})
                self.assertIsNone(client._selected_child_id)

    def test_ambiguous_parent_rows_fail_without_request(self):
        client = self.client(["edupage;school;one;rodic", "edupage;school;two;rodic"])
        with self.assertRaises(UnknownServerError):
            Parent(client).switch_to_parent()
        client.session.get.assert_not_called()

    def test_old_pages_keep_legacy_identifier(self):
        client = self.client([])
        Parent(client).switch_to_parent()
        self.assertEqual(client.session.get.call_args.kwargs["params"], {"rid": "edupage;school;alias@example.test"})

    def test_login_parses_account_rows_without_javascript(self):
        client = self.client([])
        LoginSession(client).parse_login_data(
            '<a class="edubarProfileUserBtn edubarChangeEdurowBtn Rodic" '
            'data-rowid="edupage;school;parent&amp;alias;rodic"></a>'
            'userhome({"userid":"Rodic1"});'
        )
        self.assertEqual(client._account_rows, ["edupage;school;parent&alias;rodic"])

    def test_expired_reload_invalidates_previous_login_state(self):
        client = self.client(["old row"])
        client.data = {"userid": "Rodic1"}
        client.session.get.return_value.content = b'<form id="login"></form>'
        with self.assertRaises(BadCredentialsException):
            LoginSession(client).reload_data("school", "expired", "parent")
        self.assertFalse(client.is_logged_in)
        self.assertIsNone(client.data)
        self.assertEqual(client._account_rows, [])

    def test_login_redirect_does_not_claim_parent_restored(self):
        client = self.client(["edupage;school;parent;rodic"])
        client.session.get.return_value.url = "https://school.edupage.org/login/"
        with self.assertRaises(UnknownServerError):
            Parent(client).switch_to_parent()
        self.assertEqual(client._selected_child_id, 1)
