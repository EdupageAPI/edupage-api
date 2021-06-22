
# Disclaimer
I do not have the energy to update this project. I can make bug-fixes or some small feature updates from time to time, but I am fed up with python's weak typing. 

# edupage-api
[![CodeFactor](https://www.codefactor.io/repository/github/ivanhrabcak/edupage-api/badge)](https://www.codefactor.io/repository/github/ivanhrabcak/edupage-api) 


This python library allows easy access to Edupage. This is not a Selenium web scraper. 
It makes requests directly to Edupage's endpoints and parses the HTML document.

If you find any issue with this code, it doesn't work, or you have a suggestion please let me know by opening an [issue](https://github.com/ivanhrabcak/edupage-api/issues/new/choose)! If you, even better have fixed the issue, added a new feature or made something work better please open a [pull request](https://github.com/ivanhrabcak/edupage-api/compare)!

# Installing
You can install this library with pip:
```
pip install edupage-api
```
# Usage
## Login
You can log in easily, works with any school:
```python
from edupage_api import Edupage, BadCredentialsException, LoginDataParsingException


edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")

try:
    edupage.login()
except BadCredentialsException:
    print("Wrong username or password!")
except LoginDataParsingException:
    print("Try again or open an issue!")
```

## Get timetable for a given date
Check all available timetables:
```python
from edupage_api import Edupage

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Get dates for all available timetables
dates = edupage.get_available_timetable_dates()

print(dates) # ['2021-02-03', '2021-02-04']
```

## Get the timetable for a date
```python
from edupage_api import Edupage, EduDate

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Get today's date
today = EduDate.today() # '2021-02-03'

timetable = edupage.get_timetable(today) # returns EduTimetable

# Get first lesson
first_lesson = timetable.get_first_lesson()

# The starting and ending time of the first lesson
start_time = first_lesson.length.start
end_time = first_lesson.length.end

print(start_time)
print(end_time)

# Get yesterday date
yesterday = EduDate.yesterday_this_time() # '2021-02-04'
print(yesterday)

# This will return None, because the timetable from yesterday is not available
timetable_for_yesterday = edupage.get_timetable(yesterday)
print(timetable_for_yesterday)
```

## Get lesson for a given time
```python
from edupage_api import Edupage, EduDate, EduTime

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
from edupage_api import Edupage, EduDate, EduTime

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Timetable for today
timetable = edupage.get_timetable(EduDate.today())

# Get current time
current_time = EduTime.now()

next_lesson = timetable.get_next_lesson_at_time(current_time)

print(next_lesson)
```

The `EduLesson` class provides some information about the lesson:

#### `EduLesson`: 
- `period`: The order of period in timetable (e.g. 1).
- `name`: The subject of this lesson.
- `teacher`: The teacher that will teach this lesson
- `classroom`: The classroom number where the lesson will be.
- `length`: `EduLength` –> The length (start and end times) of the lesson.
- `online_lesson_link`: A string with link to the online lesson. If this lesson is not online, `online_lesson_link` is `None`.


## Tell edupage that you are on an online lesson
Useful for automating your presence, because you don't actually have to be on the lesson.
You can tell edupage that you are on the current lesson like this:
```python
from edupage_api import Edupage, LessonUtil

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

timetable = edupage.get_timetable(EduDate.today())
next_lesson = timetable.get_next_lesson_at_time(EduTime.now())

if LessonUtil.is_online_lesson(next_lesson):
    next_lesson.sign_into_lesson(edupage)
    print("You are now 'present' on the next lesson!")
else:
    print("The next lesson is not an online lesson!")
```

## Get news from the webpage
Thanks to how Edupage's message system works, you can get recent news from the webpage like this:
```python
from edupage_api import Edupage

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Note: if you are not logged in or there was an error, get_news returns None
news = edupage.get_news() # returns a list of EduNews

for message in news:
    print(str(message))
```

## Get a list of students
This is an edupage-curated list of students. When students enter the school, they get assigned a number. If anybody changes school, leaves or anything happens with any student, the numbers don't change. It just skips the number.
```python
from edupage_api import Edupage, EduStudent

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Note: This list doesn't have to be sorted!
students = edupage.get_students()

# Sort the list by student numbers
students.sort(key = EduStudent.__sort__)

for student in students:
    print(f"{student.number_in_class}: {student.fullname}")

```

## Get a list of teachers
This list is not sorted in any way and this library doesn't provide a way to sort it.
```python
from edupage_api import Edupage

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

# Note: This list is not sorted and you cannot sort it with EduStudent.__sort__!
teachers = edupage.get_teachers()

for teacher in teachers:
    print(str(teacher))

```

## Get homework
```python
from edupage_api import Edupage

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")  
edupage.login()

homework = edupage.get_homework()

for hw in homework:
    print(hw.due_date)
```

Homework, other than its title and description, provides some more information:
#### `EduHomework`
- `due_date`: `EduDate` –> When the homework is due
- `subject`: The subject which this homework is from
- `groups`: If this subject is divided into groups, the target should be here. __Needs testing__
- `title`: The title of the homework message. This is usually what you in a notification in the Edupage app.
- `description`: A detailed description of the homework. (Usually is blank)
- `event_id`: A internal Edupage ID, which can be used to find the event corresponding to this homework. Useless for now.
- `datetime_added`: `EduDateTime` –> A date and time when this homework was assigned.


## Sending messages
You can send a message to one or multiple people when you have an object that extends `EduPerson`
```python
from edupage_api import Edupage, EduStudent

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

for student in students:
    if student.fullname == "John Smith":
        # Ignore the attachments parameter, for some reason attachments do not work
        edupage.send_message(student, "Hello John!")
```

## Upload a file to Edupage's cloud
The file will be hosted forever (and for free) on Edupage's servers. The file is tied to your user account, but anybody with a link can view it.

Anyway, Edupage limits file size to 50 MB and the file can have only some extensions. All supported file extensions could be found on this [Edupage help site](https://help.edupage.org/?p=u1/u113/u132/u362/u467).
```python
from edupage_api import Edupage, EduStudent
from edupage_api.cloud import EduCloud

edupage = Edupage("Subdomain (Name) of your school", "Username or E-Mail", "Password")
edupage.login()

f = open("image.png", "rb")

uploaded_file = EduCloud.upload_file(edupage, f)
link = uploaded_file.get_url(edupage)

print(link)

```

# Upcoming features
- [x] Lunches
- [x] Grades
- [x] Reading your own notifications
- [x] Connecting to the online lessons (with your presence being acknowledged by Edupage)
- [x] Uploading (and hosting) files on the Edupage cloud (if possible)
- [x] Writing messages to other students/teachers
- [x] Make this library available through PyPi

Feel free to suggest any other features! Just open an [issue with the *Feature Request* tag](https://github.com/ivanhrabcak/edupage-api/issues/new?labels=feature+request&template=feature_request.md&title=%5BFeature+request%5D+).
