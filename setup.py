import setuptools
import sys

if sys.version_info < (3, 9):
    raise RuntimeError("This package requres Python 3.9+")

setuptools.setup()
