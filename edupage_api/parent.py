from dataclasses import dataclass
from html import unescape
from typing import Union
from urllib.parse import urlparse

from edupage_api.dbi import DbiHelper
from edupage_api.exceptions import (
    InvalidChildException,
    InvalidSchoolException,
    MissingDataException,
    UnknownServerError,
)
from edupage_api.login_session import LoginSession
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount, EduStudent


@dataclass
class SchoolChild:
    person_id: int
    name: str


@dataclass
class SchoolAccount:
    subdomain: str
    is_current: bool
    children: list[SchoolChild]


class Parent(Module):
    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def get_children(self) -> list[EduStudent]:
        child_ids = self.edupage.data.get("parentStudentids") or []

        dbi = DbiHelper(self.edupage)

        children = []
        for child_id in child_ids:
            child_data = dbi.fetch_student_data(child_id)
            if child_data is None:
                continue

            child = EduAccount.parse(child_data, int(child_id), self.edupage)
            if child is not None:
                children.append(child)

        return children

    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def switch_to_child(self, child: EduAccount | int):
        child_id = child.person_id if isinstance(child, EduAccount) else child
        params = {"studentid": child_id}

        url = f"https://{self.edupage.subdomain}.edupage.org/login/switchchild"
        response = self.edupage.session.get(url, params=params)

        if response.text != "OK":
            raise InvalidChildException(
                f"{response.text}: Invalid child selected! (not your child?)"
            )

        self.edupage._selected_child_id = int(child_id)

    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def switch_to_parent(self):
        # variable name is from edupage's code :/
        rid = f"edupage;{self.edupage.subdomain};{self.edupage.username}"

        params = {"rid": rid}

        url = f"https://{self.edupage.subdomain}.edupage.org/login/edupageChange"
        response = self.edupage.session.get(url, params=params)

        if "EdupageLoginFailed" in response.url:
            raise UnknownServerError()

        self.edupage._selected_child_id = None

    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def switch_to_school(self, school: SchoolAccount | str):
        subdomain = school.subdomain if isinstance(school, SchoolAccount) else school

        rid = f"edupage;{subdomain};{self.edupage.username};rodic"

        params = {"rid": rid}

        url = f"https://{self.edupage.subdomain}.edupage.org/login/edupageChange"
        response = self.edupage.session.get(url, params=params)

        if (
            "EdupageLoginFailed" in response.url
            or urlparse(response.url).hostname != f"{subdomain.lower()}.edupage.org"
        ):
            raise InvalidSchoolException(
                f"Can't switch to {subdomain}: this account has no access to that school."
            )

        LoginSession(self.edupage).parse_login_data(response.text)

        self.edupage.subdomain = subdomain
        self.edupage._selected_child_id = None

    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def get_subdomains(self) -> list[str]:
        url = f"https://{self.edupage.subdomain}.edupage.org/user"
        response = self.edupage.session.get(url)
        html = response.text

        # Each school-switcher entry in the top bar's profile menu looks like:
        # <a class="edubarProfileUserBtn edubarChangeEdurowBtn Rodic selected" data-rowid="edupage;subdomain;user@example.com;rodic">
        subdomains = []

        for entry in html.split('<a class="')[1:]:
            class_attr = entry.split('"', 1)[0]

            if "edubarChangeEdurowBtn" not in class_attr:
                continue

            try:
                row_id = entry.split('data-rowid="', 1)[1].split('"', 1)[0]
            except IndexError:
                continue

            edupage, subdomain, _username, role = (row_id.split(";") + [""] * 4)[:4]
            if edupage != "edupage" or role != "rodic":
                continue

            subdomains.append(subdomain)

        if not subdomains:
            return [self.edupage.subdomain]

        return subdomains

    @staticmethod
    def _parse_school_accounts(html: str) -> list[SchoolAccount]:
        # The "My profile" page looks like this:
        # <div class="account-box [selected] box-ok"> ... Deti: <ul class="circles">
        #   <li> <CHILD_NAME> · <a class="account-childPasswordBtn" data-uid="<CHILD_ID>" ...>...</a></li>
        # </ul> ... <a class="removeEdupageBtn" data-edupage="subdomain" ...>
        # I hope that explains why this method is so ugly.
        accounts = []

        for box in html.split('<div class="account-box ')[1:]:
            class_attr = box.split('"', 1)[0]

            try:
                subdomain = box.split('data-edupage="', 1)[1].split('"', 1)[0]
            except IndexError:
                continue

            children = []

            if '<ul class="circles">' in box:
                children_html = box.split('<ul class="circles">', 1)[1].split(
                    "</ul>", 1
                )[0]

                for item in children_html.split("<li>")[1:]:
                    try:
                        person_id = int(item.split('data-uid="', 1)[1].split('"', 1)[0])
                    except (IndexError, ValueError):
                        continue

                    name = unescape(item.split("<a", 1)[0]).strip().rstrip("·").strip()
                    children.append(SchoolChild(person_id, name))

            accounts.append(
                SchoolAccount(subdomain, "selected" in class_attr.split(), children)
            )

        return accounts

    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def get_school_accounts(self) -> list[SchoolAccount]:
        url = f"https://{self.edupage.subdomain}.edupage.org/portal/"
        params = {
            "cmd": "MyAccount",
            "barNoSkin": 1,
            "ebuid": self.edupage.get_user_id(),
        }
        response = self.edupage.session.get(url, params=params)

        accounts = Parent._parse_school_accounts(response.text)
        if not accounts:
            raise MissingDataException("EduPage didn't return any school accounts.")

        return accounts
