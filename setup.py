#!/usr/bin/env python

from distutils.core import setup

setup(
    name="Djapian",
    version="2.0",

    license="New BSD License",

    author='Alex Koshelev',
    author_email="daevaorn@gmail.com",

    #maintainer='Rafael "SDM" Sierra',
    #maintainer_email="rafaeljsg14@gmail.com",

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

    description="High-level Xapian full-text indexer integration for Django",

    classifiers=[
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
        "Topic :: Text Processing :: Indexing"
    ]
)
