# `edupage-api`
[![CodeFactor](https://www.codefactor.io/repository/github/ivanhrabcak/edupage-api/badge)](https://www.codefactor.io/repository/github/ivanhrabcak/edupage-api) 

This python library allows easy access to EduPage. This is not a Selenium web scraper. 
It makes requests directly to EduPage's endpoints and parses the HTML document.

If you find any issue with this code, it doesn't work, or you have a suggestion, please, let me know by opening an [issue](https://github.com/ivanhrabcak/edupage-api/issues/new/choose)!

If you, even better, have fixed the issue, added a new feature, or made something work better, please, open a [pull request](https://github.com/ivanhrabcak/edupage-api/compare)!

# Installing
You can install this library with pip:

```
pip install edupage-api
```

# Usage
## Login
You can log in easily, works with any school:

```python
from edupage_api import Edupage

edupage = Edupage()

try:
    edupage.login("Username", "Password", "Your school's subdomain")
except BadCredentialsException:
    print("Wrong username or password!")
except LoginDataParsingException:
    print("Try again or open an issue!")
```

# Documentation

## Hosted
The docs are available on [yesdaddyfuck.me/edupage-api](https://yesdaddyfuck.me/edupage-api/)

## Host it yourself locally
To learn display the documentation for this library, you can run: `python -m http.server --directory docs`. 

Then a local webpage will be served on http://127.0.0.1:8000.



# I have a problem or an idea!
Feel free to suggest any other features! Just open an [issue with the *Feature Request* tag](https://github.com/ivanhrabcak/edupage-api/issues/new?labels=feature+request&template=feature_request.md&title=%5BFeature+request%5D+).
