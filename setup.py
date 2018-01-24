#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

long_desc = open('README.rst').read()

setup(
    name="aptly-gui",
    version="0.1.0",
    description="Aptly GUI based on python-aptly",
    long_description=long_desc,
    author="Cedric Hnyda",
    author_email="ced.hnyda@gmail.com",
    url='https://github.com/chnyda/python-aptly-gui',
    license='GPLv2',
    packages=['aptlygui', 'aptlygui.model', 'aptlygui.views', 'aptlygui.workers'],
    install_requires=[
        'requests>=0.14',
        'pyqt5',
        'python-aptly',
    ],
    entry_points={
        'console_scripts': ['aptly-gui = aptlygui.__main__:main']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    keywords='aptly debian repository gui',
)

