__author__ = 'krunic'

from setuptools import setup

setup(
    name = "webarchiver", # pip install pocket
    description = "Bulk WebArchive downloader wotking with the ",
    version = "0.1.0",
    author = 'Veljko Krunic',
    author_email = "krunic@ieee.org",

    url = 'http://github.com/krunic/webarchiver/',
    license = 'Apache',
    install_requires = ["pocket", ],

    py_modules = ["webarchiver"],

    zip_safe = True,
)

# TODO: Do all this and delete these lines
# register: Create an accnt on pypi, store your credentials in ~/.pypirc:
#
# [pypirc]
# servers =
#     pypi
#
# [server-login]
# username:<username>
# password:<pass>
#
# $ python setup.py register # one time only, will create pypi page for pocket
# $ python setup.py sdist --formats=gztar,zip upload # create a new release
#