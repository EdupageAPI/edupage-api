from typing import Union
from edupage_api.module import Module

class DbiHelper(Module):
    def __get_dbi(self) -> dict:
        return self.edupage.data.get("dbi")
        
    def __get_item_group(self, item_group_name: str) -> Union[dict, None]:
        dbi = self.__get_dbi()
        if dbi is None:
            return None
        
        return dbi.get(item_group_name)

    def __get_item_with_id(self, item_group_name: str, item_id: int) -> Union[dict, None]:
        items_in_group = self.__get_item_group(item_group_name)
        if items_in_group is None:
            return None
        
        return items_in_group.get(str(item_id))

    def __get_full_name(self, person_item: dict) -> str:
        first_name = person_item.get("firstname")
        last_name = person_item.get("lastname")

        return f"{first_name} {last_name}"

    def fetch_subject_name(self, subject_id: int) -> Union[str, None]:
        subject_item = self.__get_item_with_id("subjects", subject_id)
        if subject_item is not None:
            return subject_item.get("short")
    
    def fetch_classroom_number(self, classroom_id: int) -> Union[str, None]:
        classroom_item = self.__get_item_with_id("classrooms", classroom_id)
        if classroom_item is not None:
            return classroom_item.get("short")
    
    def fetch_class_name(self, class_id: int) -> Union[str, None]:
        class_item = self.__get_item_with_id("classes", class_id)
        if class_item is not None:
            return class_item.get("short")

    def fetch_teacher_name(self, teacher_id: int) -> Union[str, None]:
        teacher_item = self.__get_item_with_id("teachers", teacher_id)
        if teacher_item is not None:
            return self.__get_full_name(teacher_item)
    
    def fetch_student_name(self, student_id: int) -> Union[str, None]:
        student_item = self.__get_item_with_id("students", student_id)
        if student_item is not None:
            return self.__get_full_name(student_item)
        
    def fetch_student_list(self) -> Union[list, None]:
        return self.__get_item_group("students")
    
    def fetch_teacher_list(self) -> Union[list, None]:
        return self.__get_item_group("teachers")
    
    def fetch_teacher_data(self, teacher_id: int) -> Union[dict, None]:
        return self.__get_item_with_id("teachers", teacher_id)
    
    def fetch_student_data(self, student_id: int) -> Union[dict, None]:
        return self.__get_item_with_id("students", student_id)
