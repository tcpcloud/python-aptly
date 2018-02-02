#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

long_desc = open('README.rst').read()

setup(
    name="python-aptly",
    version="0.12.11",
    description="Aptly REST API client, GUI and tooling",
    long_description=long_desc,
    author="Filip Pytloun, Cedric Hnyda",
    author_email="filip.pytloun@tcpcloud.eu, ced.hnyda@gmail.com",
    url='https://github.com/tcpcloud/python-aptly',
    license='GPLv2',
    packages=['aptly', 'aptly.publisher', 'aptlygui', 'aptlygui.model', 'aptlygui.views', 'aptlygui.workers', 'aptlygui.widgets'],
    install_requires=[
        'requests>=0.14',
        'PyYaml',
        'python-apt',
        'pyqt5',
    ],
    entry_points={
        'console_scripts': ['aptly-publisher = aptly.publisher.__main__:main'],
        'gui_scripts': ['aptly-gui = aptlygui.__main__:main']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    keywords='aptly debian repository',
)
