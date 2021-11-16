#!/usr/bin/env python

import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/canvas-analytics>`_.
"""

version_path = 'data_aggregator/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='canvas-analytics',
    version=VERSION,
    packages=['data_aggregator'],
    include_package_data=True,
    install_requires = [
        'Django~=3.2',
        'UW-RestClients-SWS==2.3.14',
        'UW-RestClients-PWS~=2.1',
        'UW-RestClients-Canvas~=1.2.4',
        'UW-Django-SAML2~=1.5',
        'django-webpack-loader~=0.7',
        'djangorestframework~=3.12',
        'psycopg2~=2.8',
        'uw-gcs-clients~=1.0',
        'boto3~=1.17',
        'google-cloud-storage~=1.37',
        'google-api-core~=1.26',
        'pandas~=1.1',
        'urllib3~=1.25',
        'pymssql==2.2.2',
    ],
    license='Apache License, Version 2.0',
    description='Collects data about UW Canvas usage',
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
        'Programming Language :: Python :: 3.6',
    ],
)
