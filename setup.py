#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

long_desc = open('README.rst').read()

setup(
    name="python-aptly",
    version="0.3",
    description="Aptly REST API client and tooling",
    long_description=long_desc,
    author="Filip Pytloun",
    author_email="filip.pytloun@tcpcloud.eu",
    packages=['aptly', 'aptly.publisher'],
    install_requires=[
        'requests>=0.14',
    ],
    entry_points={
        'console_scripts': ['aptly-publisher = aptly.publisher.__main__:main']
    },
)
