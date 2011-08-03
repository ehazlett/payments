#!/usr/bin/env python

from distutils.core import setup
import sys

REQUIRES = []

setup(name='payments',
    version = '0.02',
    author = 'Evan Hazlett',
    author_email = 'ejhazlett@gmail.com',
    packages = ['payments'],
    description = 'Library for handling online payments',
    url = 'http://github.com/ehazlett/payments',
    license = 'License :: OSI Approved :: Apache Software License',
    long_description = """
    This is a wrapper library that helps in working with online payment systems
    like PayPal and Amazon FPS.
    """,
    download_url = 'https://github.com/ehazlett/payments/tarball/master',
    install_requires = REQUIRES,
    platforms = [
        "All",
        ],
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        ]
    )

