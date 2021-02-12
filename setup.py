from distutils.core import setup
from os import path

# https://packaging.python.org/guides/making-a-pypi-friendly-readme/
this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, "README.md"), encoding="utf8") as f:
    long_description = f.read()

setup(
    name = "edupage_api",
    packages = ["edupage_api"],
    version = "0.3",
    license = "GNU GPLv3",
    description = "A python library for accessing your Edupage account",
    long_description= long_description,
    author = "ivanhrabcak",
    author_email = "ivan@hrabcak.eu",
    url = "https://github.com/ivanhrabcak/edupage-api",
    download_url = "https://github.com/ivanhrabcak/edupage-api/archive/0.3.tar.gz",
    keywords = ["edupage", "edupage api", "library"],
    install_requires = ["requests"],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ]
)