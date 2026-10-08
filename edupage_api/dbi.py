from typing import Optional

from edupage_api.module import Module, ModuleHelper


class DbiHelper(Module):
    def __get_dbi(self) -> dict:
        return self.edupage.data.get("dbi")

    def __get_item_group(self, item_group_name: str) -> dict | None:
        dbi = self.__get_dbi()
        if dbi is None:
            return None

        item_group = dbi.get(item_group_name)

        if isinstance(item_group, list) and not item_group:
            # An item group with no entries is serialised by EduPage as an empty
            # JSON array instead of an empty object. Callers rely on mapping
            # access (see __get_item_with_id), so read an empty array as an empty
            # mapping.
            #
            # Only empty arrays are handled. A populated array has not been
            # observed, and mapping it onto positional keys would fabricate ids
            # that can never match a real reference, so it is left alone and
            # keeps failing loudly instead of silently losing data.
            return {}

        return item_group

    def __get_item_with_id(self, item_group_name: str, item_id: str) -> dict | None:
        items_in_group = self.__get_item_group(item_group_name)
        if items_in_group is None:
            return None

        return items_in_group.get(str(item_id))

    def __get_full_name(self, person_item: dict) -> str:
        first_name = person_item.get("firstname")
        last_name = person_item.get("lastname")

        return f"{first_name} {last_name}"

    def fetch_subject_name(self, subject_id: int) -> str | None:
        subject_item = self.__get_item_with_id("subjects", subject_id)
        if subject_item is not None:
            return subject_item.get("short")

    def fetch_classroom_number(self, classroom_id: str) -> str | None:
        classroom_item = self.__get_item_with_id("classrooms", classroom_id)
        if classroom_item is not None:
            return classroom_item.get("short")

    def fetch_class_name(self, class_id: int) -> str | None:
        class_item = self.__get_item_with_id("classes", class_id)
        if class_item is not None:
            return class_item.get("short")

    def fetch_teacher_name(self, teacher_id: int) -> str | None:
        teacher_item = self.__get_item_with_id("teachers", teacher_id)
        if teacher_item is not None:
            return self.__get_full_name(teacher_item)

    def fetch_student_name(self, student_id: int) -> str | None:
        student_item = self.__get_item_with_id("students", student_id)
        if student_item is not None:
            return self.__get_full_name(student_item)

    def fetch_student_list(self) -> list | None:
        return self.__get_item_group("students")

    def fetch_teacher_list(self) -> list | None:
        return self.__get_item_group("teachers")

    def fetch_subject_list(self) -> list | None:
        return self.__get_item_group("subjects")

    def fetch_classroom_list(self) -> list | None:
        return self.__get_item_group("classrooms")

    def fetch_class_list(self) -> list | None:
        return self.__get_item_group("classes")

    def fetch_teacher_data(self, teacher_id: int) -> dict | None:
        return self.__get_item_with_id("teachers", teacher_id)

    def fetch_student_data(self, student_id: int) -> dict | None:
        return self.__get_item_with_id("students", student_id)

    def fetch_student_data_by_name(self, student_name: str) -> dict | None:
        item_group = self.__get_item_group("students")

        for student_id in item_group:
            student_data = item_group.get(student_id)
            if self.__get_full_name(student_data) in student_name:
                student_data["id"] = student_id
                return student_data

    def fetch_teacher_data_by_name(self, teacher_name: str) -> dict | None:
        item_group = self.__get_item_group("teachers")

        for teacher_id in item_group:
            teacher_data = item_group.get(teacher_id)
            if self.__get_full_name(teacher_data) in teacher_name:
                teacher_data["id"] = teacher_id
                return teacher_data

    def fetch_parent_data_by_name(self, parent_name: str) -> dict | None:
        item_group = self.__get_item_group("parents")

        for parent_id in item_group:
            parent_data = item_group.get(parent_id)
            if self.__get_full_name(parent_data) in parent_name:
                parent_data["id"] = parent_id
                return parent_data

    def fetch_person_data_by_name(self, name: str) -> dict | None:
        teacher_data = self.fetch_teacher_data_by_name(name)
        student_data = self.fetch_student_data_by_name(name)
        parent_data = self.fetch_parent_data_by_name(name)

        return ModuleHelper.return_first_not_null(
            teacher_data, student_data, parent_data
        )
