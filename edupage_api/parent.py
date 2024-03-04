from typing import Union

from edupage_api.exceptions import InvalidChildException, UnknownServerError
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount


class Parent(Module):
    @ModuleHelper.logged_in
    @ModuleHelper.is_parent
    def switch_to_child(self, child: Union[EduAccount, int]):
        params = {"studentid": child.person_id if type(child) == EduAccount else child}

        url = f"https://{self.edupage.subdomain}.edupage.org/login/switchchild"
        response = self.edupage.session.get(url, params=params)

        if response.text != "OK":
            raise InvalidChildException(
                f"{response.text}: Invalid child selected! (not your child?)"
            )

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
