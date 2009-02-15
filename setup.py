#!/usr/bin/env python

from distutils.core import setup

setup(
    name="Djapian",
    version="2.0",

    author='Alex Koshelev',
    author_email="daevaorn@gmail.com",
    maintainer='Rafael "SDM" Sierra',
    maintainer_email="rafaeljsg14@gmail.com",

    url="http://code.google.com/p/djapian/",

    packages=[
        "djapian",
        "djapian.utils",
        "djapian.tests",
        "djapian.management",
        "djapian.management.commands"
    ],
    package_dir={
        "djapian": "src/djapian"
    },
)
