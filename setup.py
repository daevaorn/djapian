#!/usr/bin/env python

from distutils.core import setup

setup(name="Djapian", version="1.7",
      author='Rafael "SDM" Sierra',
      author_email="rafaeljsg14@gmail.com",
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
