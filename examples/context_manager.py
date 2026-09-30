from edupage_api import Edupage

# Using Edupage as a context manager logs out automatically when the block
# ends, even if an exception is raised inside it.
with Edupage() as edupage:
    edupage.login(
        "Username (or e-mail)",
        "Password",
        "Subdomain of your school (SUBDOMAIN.edupage.org)",
    )

    teachers = edupage.get_teachers()

    for i, teacher in enumerate(teachers):
        print(f"{i + 1}. {teacher.name}")
