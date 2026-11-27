"""HTTP diagnostic summaries never contain authentication material or bodies."""
import unittest
from types import SimpleNamespace
from requests.structures import CaseInsensitiveDict

from edupage_api._http_diagnostics import response_shape


class HttpDiagnosticTests(unittest.TestCase):
    def test_sensitive_response_is_reduced_to_structural_fields(self):
        response = SimpleNamespace(
            url="https://school.edupage.org/login/?rid=PRIVATE_RID&PHPSESSID=PRIVATE_SESSION",
            text="PRIVATE_BODY userhome( ASC.gsechash=PRIVATE_HASH", content=b"PRIVATE_BODY",
            status_code=200,
            headers=CaseInsensitiveDict({"Content-Type": "text/html; charset=utf-8", "Set-Cookie": "PRIVATE_COOKIE"}),
            history=[SimpleNamespace(status_code=302)],
        )
        summary = response_shape(response, "school")
        self.assertEqual(summary["endpoint"], "login")
        self.assertEqual(summary["content_type"], "text/html")
        self.assertEqual(summary["redirect_statuses"], [302])
        self.assertTrue(summary["same_school_host"])
        self.assertTrue(summary["has_userhome"])
        self.assertTrue(summary["has_gsec_hash"])
        self.assertNotIn("PRIVATE", repr(summary))
        self.assertNotIn("rid", summary)

    def test_unknown_final_path_and_mime_are_not_echoed(self):
        response = SimpleNamespace(url="https://other.test/PRIVATE_USER", status_code=503,
                                   headers={"Content-Type": "PRIVATE_TYPE"}, text="", content=b"", history=[])
        summary = response_shape(response, "school")
        self.assertEqual(summary["endpoint"], "other")
        self.assertEqual(summary["content_type"], "other")
        self.assertFalse(summary["same_school_host"])
        self.assertNotIn("PRIVATE", repr(summary))
