#!/usr/bin/env python

import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='canvas-analytics',
    version='1.0',
    packages=['analytics'],
    include_package_data=True,
    install_requires = [
        'Django==1.11.10',
        'UW-RestClients-SWS>=1.5.1,<2.0',
        'UW-RestClients-Canvas>=0.7.1,<1.0',
        'UW-Django-SAML2>=0.4.5',
    ],
    license='Apache License, Version 2.0',
    description='Builds reports about UW Canvas usage',
    long_description=README,
    url='https://github.com/uw-it-aca/canvas-analytics',
    author = "UW-IT AXDD",
    author_email = "aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
)
