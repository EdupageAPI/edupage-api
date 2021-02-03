# edupage-api
This python library allows easy access to Edupage. This is not a sellenium web scraper. 
It makes requests directly to Edupage's endpoinds and parses the html data.

# Login
You can login easily, works with any school:
```python
from edupage import Edupage

edupage = Edupage("Username", "Password")
edupage.login()
```


# Get timetable for a given date
Check all avaiable timetables:
```python
from edupage import Edupage

edupage = Edupage("Username", "Password")
edupage.login()

# Get dates for all avaiable timetables
dates = edupage.get_avaiable_timetable_dates()

print(dates) # ['2021-02-03', '2021-02-04']
```

# Get the timetable for a date
```python
from edupage import Edupage

edupage = Edupage("Username", "Password")
edupage.login()

# Get today's date
today = EduDate.today() # '2021-02-03'

timetable = edupage.get_timetable(today) # returns a list of EduLesson

# The starting time of the first lesson
# Note: the start and end times from EduLesson.length are a string.
start_time = timetable[0].length.start
end_time = timetable[0].length.end

print(start_time)
print(end_time)
```
The EduLesson class provides some information about the lesson:

EduLesson:
	- name: The subject of this lesson
	- teacher: The teacher that will teach this lesson
	- classroom: The classroom number where the lesson will be
	- length: EduLength -> The length (start and end times) of the lesson
	- online_lesson_link: A string with link to the online lesson. If this lesson is not online, online_lesson_link is None.

