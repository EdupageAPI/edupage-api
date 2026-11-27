import logging

from typing import Union
from urllib.parse import urlsplit

from edupage_api.exceptions import InvalidChildException, UnknownServerError
from edupage_api.module import Module, ModuleHelper
from edupage_api.people import EduAccount
from edupage_api._http_diagnostics import context, response_shape

_LOGGER = logging.getLogger(__name__)


class Parent(Module):
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
        candidates = []
        for row in getattr(self.edupage, "_account_rows", []):
            parts = row.split(";")
            if (len(parts) == 4 and parts[0] == "edupage"
                    and parts[1] == self.edupage.subdomain and parts[3] == "rodic"):
                candidates.append(row)
        exact = [row for row in candidates if row.split(";")[2] == self.edupage.username]
        source = "legacy"
        if len(set(exact)) == 1:
            rid = exact[0]
            source = "exact_server_row"
        elif len(set(candidates)) == 1:
            # Login aliases need not equal the canonical account identifier.
            rid = candidates[0]
            source = "unique_server_row"
        elif candidates:
            _LOGGER.debug("parent_switch ambiguous identity context=%s parent_candidates=%d exact_candidates=%d",
                          context(self.edupage), len(candidates), len(exact))
            raise UnknownServerError("Ambiguous parent account identity")

        params = {"rid": rid}

        url = f"https://{self.edupage.subdomain}.edupage.org/login/edupageChange"
        _LOGGER.debug(
            "parent_switch request context=%s method=GET endpoint=/login/edupageChange "
            "parameter_names=rid identity_source=%s identity_parts=%d parent_candidates=%d exact_candidates=%d",
            context(self.edupage), source, len(rid.split(";")), len(candidates), len(exact),
        )
        response = self.edupage.session.get(url, params=params)
        _LOGGER.debug("parent_switch response context=%s metadata=%s",
                      context(self.edupage), response_shape(response, self.edupage.subdomain))

        response.raise_for_status()
        if ("EdupageLoginFailed" in response.url
                or urlsplit(response.url).path.rstrip("/") in ("/login", "/login/index.php")):
            raise UnknownServerError("Parent switch redirected to login")

        self.edupage._selected_child_id = None
        _LOGGER.debug("parent_switch completed context=%s", context(self.edupage))

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
