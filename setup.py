from distutils.core import setup

setup(
    name = "edupage_api",
    packages = ["edupage_api"],
    version = "0.1",
    license = "GNU GPLv3",
    description = "A python library for accessing your Edupage account",
    author = "ivanhrabcak",
    author_email = "ivan@hrabcak.eu",
    url = "https://github.com/ivanhrabcak/edupage-api",
    download_url = "https://github.com/ivanhrabcak/edupage-api/archive/0.1.tar.gz",
    keywords = ["edupage", "edupage api", "library"],
    install_requires = ["requests", "datetime", "json", "pprint"],
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