import argparse
from datetime import date, datetime
import sys
from typing import Optional, Union
from dataclasses import asdict
import json
import csv
import io

from edupage_api import Edupage
from edupage_api.exceptions import BadCredentialsException
from edupage_api.people import EduTeacher
from edupage_api.substitution import TimetableChange

parser = argparse.ArgumentParser(description="Get substitution information from edupage.")
parser.add_argument("--output", metavar="file", type=str, default="stdout")
parser.add_argument("--format", metavar="format", choices=["json", "text", "csv"], default="text")
parser.add_argument("--date", metavar="date", type=lambda d: datetime.strptime(d, "%Y-%m-%d").date(), default=date.today())
parser.add_argument("username", type=str)
parser.add_argument("password", type=str)
parser.add_argument("subdomain", type=str)

args = parser.parse_args()

edupage = Edupage()

try:
    edupage.login(args.username, args.password, args.subdomain)
except BadCredentialsException:
    print("Invalid username, password or subdomain!")
    sys.exit(1)

missing_teachers = edupage.get_missing_teachers(args.date)
timetable_changes = edupage.get_timetable_changes(args.date)

def output(file: str, s: str):
    if file == "stdout":
        print(s)
        return
    
    f = open(file, "w+")
    f.write(s)
    f.close()

def get_lesson_number_pretty(n: Union[int, tuple[int, int]]) -> str:
        if type(n) == int:
            return str(n) + ":"
        elif n is None:
            return ""
        else:
            return f"{n[0]}-{n[1]}:"

def get_text(missing_teachers: Optional[list[EduTeacher]], timetable_changes: Optional[list[TimetableChange]]):
    s = ""

    if missing_teachers:
        s += "Missing teachers: "
        s += ", ".join(list(map(lambda t: t.name, missing_teachers))) + "\n\n"
    
    if timetable_changes:
        s += "Timetable changes:\n"

        # group by classes
        classes = {}
        for change in timetable_changes:
            if classes.get(change.change_class) == None:
                classes[change.change_class] = [change]
            else:
                classes[change.change_class].append(change)
        
        for clazz in classes:
            s += f"    {clazz}:\n"
            for change in classes[clazz]:
                s += f"        {get_lesson_number_pretty(change.lesson_n)} {change.title}\n"
    
    return s

if args.format == "text":
    output(args.output, get_text(missing_teachers, timetable_changes))
else:
    data = {}
    
    if missing_teachers:
        data["missingTeachers"] = list(map(lambda t: t.name, missing_teachers))
    
    if timetable_changes:
        data["timetableChanges"] = list(map(lambda c: asdict(c), timetable_changes))
        
    if args.format == "json":
        output(args.output, json.dumps(data, indent=4))
    else:
        stream = io.StringIO()
        
        if missing_teachers:
            missing_teachers_writer = csv.DictWriter(stream, fieldnames=["name"])

            missing_teachers_writer.writeheader()
            missing_teachers_dict = [{"name": t} for t in data["missingTeachers"]]
            print(missing_teachers_dict)
            missing_teachers_writer.writerows(missing_teachers_dict)

            stream.write("\n\n")
        
        if timetable_changes:

            timetable_changes_writer = csv.DictWriter(stream, fieldnames=["change_class", "lesson_n", "title", "action"])
            timetable_changes_writer.writeheader()
            
            for change in data["timetableChanges"]:
                change["lesson_n"] = get_lesson_number_pretty(change["lesson_n"])
            
            timetable_changes_writer.writerows(data["timetableChanges"])

        output(args.output, stream.getvalue())
