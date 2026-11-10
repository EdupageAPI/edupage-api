import unittest
from unittest.mock import Mock

from edupage_api import Edupage
from edupage_api.exceptions import (
    InvalidSchoolException,
    MissingDataException,
    NotParentException,
)
from edupage_api.parent import SchoolAccount, SchoolChild


def school_box(subdomain, children, selected=False):
    items = "".join(
        "<li>\t\t\t\t\t\t\t\t\t\r\n"
        f"\t\t\t\t\t\t\t\t\t\t{name} · "
        f'<a class="account-childPasswordBtn" data-uid="{uid}" '
        f'data-rowid="edupage;{subdomain};parent@example.com;Rodic">Reset</a>\r\n'
        "\t\t\t\t\t\t\t\t\t</li>\r\n"
        for uid, name in children
    )
    children_html = (
        '<div style="margin-top:8px">\r\n\t\t\t\tKids:\r\n'
        f'\t\t\t\t<ul class="circles">\t\t\t{items}\t\t\t</ul>\r\n'
        "\t\t\t</div>"
        if children
        else ""
    )

    return (
        f'<div class="account-box {"selected" if selected else " "} box-ok">\r\n'
        '\t\t<div><img src="/app/pics/icons/sidemenu/parent.svg" alt=""></div>\r\n'
        "\t\t<div><b>parent@example.com</b></div>\r\n"
        '\t\t<div style="flex: auto 1 1;">\r\n'
        f"\t\t\tParent\t\t\t·\r\n\t\t\t{subdomain}.edupage.org\r\n"
        f"\t\t\t{children_html}\r\n"
        "\t\t</div>\r\n"
        '\t\t<div class="account-box-msg ok">\r\n'
        '\t\t\t<div class="account-box-msg0">Ok</div>\r\n'
        '\t\t\t<div class="account-ralign">\r\n'
        '\t\t\t\t<a class="removeEdupageBtn account-link-button" '
        f'data-rowid="edupage;{subdomain};parent@example.com;Rodic" '
        f'data-edupage="{subdomain}" data-edumeno="parent@example.com">Remove</a>\r\n'
        "\t\t\t</div>\r\n"
        "\t\t</div>\r\n"
        "\t</div>\r\n"
    )


ADD_ACCOUNT_BUTTON = (
    '<a class="account-box nobg newBtn addEdupageBtn">'
    '<i class="fa fa-fw fa-plus"></i><div>Add<br /> account</div></a>'
)


def my_account_page(*boxes):
    return (
        '<div class="myprofile-section"><h3>School accounts</h3>\r\n'
        '<div class="account-boxes clearfix">\t\r\n'
        + "".join(boxes)
        + ADD_ACCOUNT_BUTTON
        + "\r\n</div></div>"
    )


class SchoolAccountsTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.subdomain = "school-b"
        self.api.data = {"userid": "Rodic-1"}
        self.api.session = Mock()

    def get_school_accounts(self, page):
        self.api.session.get.return_value.text = page
        return self.api.get_school_accounts()

    def test_schools_and_children_are_parsed(self):
        accounts = self.get_school_accounts(
            my_account_page(
                school_box("school-a", [(1001, "Anna Testová")]),
                school_box(
                    "school-b",
                    [(2001, "Boris Test"), (2002, "Anna Testová")],
                    selected=True,
                ),
            )
        )

        self.assertEqual(
            accounts,
            [
                SchoolAccount("school-a", False, [SchoolChild(1001, "Anna Testová")]),
                SchoolAccount(
                    "school-b",
                    True,
                    [SchoolChild(2001, "Boris Test"), SchoolChild(2002, "Anna Testová")],
                ),
            ],
        )

    def test_school_without_children(self):
        accounts = self.get_school_accounts(
            my_account_page(school_box("school-a", [], selected=True))
        )

        self.assertEqual(accounts, [SchoolAccount("school-a", True, [])])

    def test_add_account_button_is_not_a_school(self):
        accounts = self.get_school_accounts(
            my_account_page(school_box("school-a", [(1001, "Anna Testová")]))
        )

        self.assertEqual([a.subdomain for a in accounts], ["school-a"])

    def test_names_are_unescaped(self):
        accounts = self.get_school_accounts(
            my_account_page(school_box("school-a", [(1001, "Anna &amp; Boris")]))
        )

        self.assertEqual(accounts[0].children[0].name, "Anna & Boris")

    def test_child_without_a_valid_id_is_skipped(self):
        page = my_account_page(
            school_box("school-a", [(1001, "Anna Testová"), (1002, "Boris Test")])
        ).replace('data-uid="1002"', 'data-uid="oops"')

        accounts = self.get_school_accounts(page)

        self.assertEqual(accounts[0].children, [SchoolChild(1001, "Anna Testová")])

    def test_request_goes_to_my_account_with_the_user_id(self):
        self.get_school_accounts(my_account_page(school_box("school-a", [])))

        args, kwargs = self.api.session.get.call_args
        self.assertEqual(args[0], "https://school-b.edupage.org/portal/")
        self.assertEqual(kwargs["params"]["cmd"], "MyAccount")
        self.assertEqual(kwargs["params"]["ebuid"], "Rodic-1")

    def test_page_without_schools_raises(self):
        with self.assertRaises(MissingDataException):
            self.get_school_accounts("<html>Please log in</html>")

    def test_not_a_parent_raises(self):
        self.api.data = {"userid": "Student-1"}

        with self.assertRaises(NotParentException):
            self.api.get_school_accounts()


class SwitchToSchoolTests(unittest.TestCase):
    def setUp(self):
        self.api = Edupage()
        self.api.is_logged_in = True
        self.api.subdomain = "school-b"
        self.api.username = "parent@example.com"
        self.api.data = {"userid": "Rodic-1", "parentStudentids": [2001, 2002]}
        self.api._selected_child_id = 2001
        self.api.session = Mock()

    def respond(self, url, text=""):
        response = self.api.session.get.return_value
        response.url = url
        response.text = text

    def landing_page(self, user_id="Rodic-2", child_ids=(1001,)):
        return (
            "<script>\r\n\t\t$j(document).ready(function() {\r\n"
            f'\t\t\t$j("#x").userhome({{"userid": "{user_id}", '
            f'"parentStudentids": {list(child_ids)}}});\r\n'
            "\t\t});\r\n\t\t</script>"
        )

    def test_switches_and_loads_the_new_schools_data(self):
        self.respond("https://school-a.edupage.org/user/", self.landing_page())

        self.api.switch_to_school("school-a")

        self.assertEqual(self.api.subdomain, "school-a")
        self.assertEqual(self.api.data["parentStudentids"], [1001])
        self.assertIsNone(self.api._selected_child_id)
        self.assertEqual(self.api.username, "parent@example.com")

    def test_request_is_sent_to_the_current_school_with_the_target_row_id(self):
        self.respond("https://school-a.edupage.org/user/", self.landing_page())

        self.api.switch_to_school("school-a")

        args, kwargs = self.api.session.get.call_args
        self.assertEqual(args[0], "https://school-b.edupage.org/login/edupageChange")
        self.assertEqual(
            kwargs["params"], {"rid": "edupage;school-a;parent@example.com;rodic"}
        )

    def test_accepts_a_school_account(self):
        self.respond("https://school-a.edupage.org/user/", self.landing_page())

        self.api.switch_to_school(SchoolAccount("school-a", False, []))

        self.assertEqual(self.api.subdomain, "school-a")

    def test_unknown_school_raises_and_changes_nothing(self):
        # EduPage sends a school the account doesn't have back to the current school
        self.respond("https://school-b.edupage.org/portal/?cmd=MyAccount", "<html>")

        with self.assertRaises(InvalidSchoolException):
            self.api.switch_to_school("nonexistent")

        self.assertEqual(self.api.subdomain, "school-b")
        self.assertEqual(self.api.data["userid"], "Rodic-1")
        self.assertEqual(self.api._selected_child_id, 2001)

    def test_failed_login_raises_and_changes_nothing(self):
        self.respond("https://school-b.edupage.org/?EdupageLoginFailed=1")

        with self.assertRaises(InvalidSchoolException):
            self.api.switch_to_school("nonexistent")

        self.assertEqual(self.api.subdomain, "school-b")
        self.assertEqual(self.api._selected_child_id, 2001)

    def test_not_a_parent_raises(self):
        self.api.data = {"userid": "Student-1"}

        with self.assertRaises(NotParentException):
            self.api.switch_to_school("school-a")


if __name__ == "__main__":
    unittest.main()
