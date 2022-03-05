from edupage_api import Edupage

edupage = Edupage()
edupage.login_auto("Username (or e-mail)", "Password")

grades = edupage.get_grades()

grades_by_subject = {}

for grade in grades:
    if grades_by_subject.get(grade.subject_name):
        grades_by_subject[grade.subject_name] += [grade]
    else:
        grades_by_subject[grade.subject_name] = [grade]

for subject in grades_by_subject:
    print(f"{subject}:")
    for grade in grades_by_subject[subject]:
        
        print(f"    {grade.title} -> ", end="")

        if grade.max_points != 100:
            print(f"{grade.grade_n}/{grade.max_points}")
        else:
            print(f"{grade.percent}%")
    print("----------------")