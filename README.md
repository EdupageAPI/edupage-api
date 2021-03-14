# edupage-api
This python library allows easy access to Edupage. This is not a sellenium web scraper. 
It makes requests directly to Edupage's endpoinds and parses the html document.

If you find any issue with this code, it doesn't work or you have a suggestion please let me know and open a Issue! If you, even better have fixed the issue, added a new feature or made something work better please open a pull request!

# Installing
You can install this library with pip:
```
pip install edupage-api
```
# Usage
## Login
You can login easily, works with any school:
```python
from edupage_api import Edupage, BadCredentialsException, LoginDataParsingException

try:
    edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
except BadCredentialsException:
    print("Wrong username or password!")
except LoginDataParsingException:
    print("Try again or open an issue!")

edupage.login()
```

## Get timetable for a given date
Check all avaiable timetables:
```python
from edupage_api import Edupage, BadCredentialsException, LoginDataParsingException

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Get dates for all avaiable timetables
dates = edupage.get_avaiable_timetable_dates()

print(dates) # ['2021-02-03', '2021-02-04']
```

## Get the timetable for a date
```python
from edupage_api import Edupage, EduDate, BadCredentialsException, LoginDataParsingException

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Get today's date
today = EduDate.today() # '2021-02-03'

timetable = edupage.get_timetable(today) # returns EduTimetable

# The starting time of the first lesson
first_lesson = timetable.get_first_lesson()

start_time = first_lesson.start
end_time = first_lesson.end

print(start_time)
print(end_time)

# Get tommorow date
tommorrow = EduDate.yesterday() # '2021-02-04'

# This will return None, because the timetable from yesterday is not avaiable
timetable_for_tommorrow = edupage.get_timetable(tommorrow)
```

## Get lesson for a given time
```python
from edupage_api import Edupage, EduDate, EduTime, BadCredentialsException, LoginDataParsingException

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Timetable for today
timetable = edupage.get_timetable(EduDate.today())

# Get current time
current_time = EduTime.now()

current_lesson = timetable.get_lesson_at_time(current_time)

print(current_lesson)

```

## Get next lesson for a given time
```python
from edupage_api import Edupage, EduDate, EduTime, BadCredentialsException, LoginDataParsingException

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Timetable for today
timetable = edupage.get_timetable(EduDate.today())

# Get current time
current_time = EduTime.now()

next_lesson = timetable.get_next_lesson_at_time(current_time)

print(next_lesson)
```

The EduLesson class provides some information about the lesson:

#### EduLesson: 
- name: The subject of this lesson
- teacher: The teacher that will teach this lesson
- classroom: The classroom number where the lesson will be
- length: EduLength -> The length (start and end times) of the lesson
- online_lesson_link: A string with link to the online lesson. If this lesson is not online, online_lesson_link is None.


## Get news from the webpage
Thanks to how Edupage's message system works, you can get recent news from the webpage like this:
```python
from edupage_api import Edupage, BadCredentialsException, LoginDataParsingException

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Note: if you are not logged in or there was an error, get_news returns None
news = edupage.get_news() # returns a list of EduNews

for message in news:
    print(str(news))
```

## Get the list of students
This is an edupage-curated list of students. When students enter the school, they get assigned a number. If anybody changes school, leaves or anything happens with any student, the numbers don't change. It just skips the number.
```python
from edupage_api import Edupage, EduStudent, BadCredentialsException, LoginDataParsingException

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Note: This list doesn't have to be sorted!
students = edupage.get_students()

# Sort the list by student numbers
students.sort(key = EduStudent.__sort__)

for student in students:
    print(f"{student.number_in_class}: {student.fullname}")

```

## Get homework
```python
from edupage_api import Edupage, BadCredentialsException, LoginDataParsingException

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")  
edupage.login()

homework = edupage.get_homework()

for hw in homework:
    print(hw.due_date)
```
Homework, other than its title and description, provides some more information:
#### EduHomework
- due_date: EduDate -> When the homework is due
- subject: The subject which this homework is from
- groups: If this subject is devided into groups, the target should be here. __Needs testing__
- title: The title of the homework message. This is usually what you in a notification in the Edupage app.
- description: A detailed description of the homework.
- event_id: A internal Edupage id, which can be used to find the event coresponding to this homework. Useless for now.
- datetime_added: EduDateTime -> A date and time when this homework was assigned.

# Upcoming features
- [ ] Correct test answers (see [EduPageTestHack](https://github.com/markotomcik/EduPageTestHack))
- [ ] Lunches
- [ ] Grades
- [ ] All message types
- [ ] Writing messages to other students/teachers
- [x] Make this library avaiable through PyPi

Feel free to suggest any other features! Just open an issue with the *Feature Request* tag.
