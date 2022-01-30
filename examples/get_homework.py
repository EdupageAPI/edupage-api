from datetime import datetime
from edupage_api import Edupage
from edupage_api.timeline import EventType

import json

edupage = Edupage()
edupage.login("Username (or e-mail)", "Password", "Subdomain of your school (SUBDOMAIN.edupage.org)")

notifications = edupage.get_notifications()

homework_not_due = 0

homework = list(filter(lambda x: x.event_type == EventType.HOMEWORK, notifications))
for hw in homework:
    additional_data = hw.additional_data

    old_vals = additional_data.get("oldVals")
    
    due_date = None
    hw_title = None
    
    if old_vals:
        due_date = old_vals.get("date")
        due_date = datetime.strptime(due_date, "%Y-%m-%d")

        hw_title = old_vals.get("title")

    text = f"Homework from {hw.timestamp}:\n"

    hw_text = hw_title if hw_title else hw.text.replace("\n", " ")
    text += (f"{hw_text}")

    if due_date:
        now = datetime.now()
        if due_date > now:
            text += "\n - DUE -"
        else:
            homework_not_due += 1
            text += "\n- UNFINISHED -"

    print(text)
    print("-------------------------------------")

print(f"You have {homework_not_due} homework that is not finished.")

    