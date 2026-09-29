from typing import Union

from edupage_api.exceptions import InvalidChildException, UnknownServerError
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount


class Parent(Module):
    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def switch_to_child(self, child: Union[EduAccount, int]):
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
