from datetime import datetime

from edupage_api import Edupage
from edupage_api.timeline import EventType

edupage = Edupage()
edupage.login(
    "Username (or e-mail)",
    "Password",
    "Subdomain of your school (SUBDOMAIN.edupage.org)",
)

notifications = edupage.get_notifications()

homework_not_due = 0

homework = list(filter(lambda x: x.event_type == EventType.HOMEWORK, notifications))
for hw in homework:
    additional_data = hw.additional_data

    old_vals = additional_data.get("oldVals")

    due_date = None
    hw_title = None

    if old_vals:
        try:
            due_date = old_vals.get("date")
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        except TypeError:
            pass

        hw_title = old_vals.get("title")

    text = f"Homework from {hw.timestamp}\n"

    hw_text = hw_title or hw.text.replace("\n", " ")
    text += f"{hw_text}"

    if due_date:
        now = datetime.now()
        text += f"\nDue to: {due_date} -> "

        if due_date > now:
            text += "DUE"
        else:
            homework_not_due += 1
            text += "UNFINISHED"

    print(text)
    print("—")

print(f"You have {homework_not_due} unfinished homework assignments.")
