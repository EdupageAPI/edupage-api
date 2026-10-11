from datetime import date

from edupage_api import Edupage

# A parent account can have children in several schools.
with Edupage() as edupage:
    edupage.login(
        "Username (or e-mail)",
        "Password",
        "Subdomain of your school (SUBDOMAIN.edupage.org)",
    )

    school_accounts = edupage.get_school_accounts()

    for school in school_accounts:
        children = ", ".join(child.name for child in school.children) or "-"
        current = " (current)" if school.is_current else ""
        print(f"{school.subdomain}{current}: {children}")

    print()

    for school in school_accounts:
        # You can also pass just the subdomain: edupage.switch_to_school("subdomain")
        edupage.switch_to_school(school)

        # get_children() only lists the children of the current school and
        # switching to a school forgets the currently selected child
        for child in edupage.get_children():
            edupage.switch_to_child(child)

            print(f"{child.name} ({school.subdomain}), timetable for today:")

            for lesson in edupage.get_my_timetable(date.today()):
                teacher_name = lesson.teachers[0].name if lesson.teachers else "?"
                print(f"    [{lesson.period}] {lesson.subject.name} ({teacher_name})")
