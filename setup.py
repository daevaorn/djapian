#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup


setup(name="Djapian", version="1.1",
      author='Rafael "SDM" Sierra',
      author_email="rafaeljsg14@gmail.com",
      packages=["djapian", "djapian.backend", "djapian.management"],
      package_dir={"djapian": "src/djapian"},
)
