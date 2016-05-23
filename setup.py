#!/usr/bin/env python

PROJECT = 'jenkins-slave-builder'

VERSION = '0.1.0'

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

config = {
    'name': 'jenkins-slave-builder',
    'version': '0.1.0',

    'description': 'Build jenkins slaves in YAML',

    'author': 'ikasam_a',
    'author_email': 'masaki.nakagawa@gmail.com',

    'url': 'https://github.com/masaki/jenkins-slave-builder',

    'classifiers': [],

    'platforms': ['Any'],

    'scripts': [],

    'provides': [],

    'install_requires': [
        'cliff',
        'PyYAML',
        'argparse',
        'requests'
    ],

    'packages': find_packages(),
    'include_package_data': True,

    'entry_points': {
        'console_scripts': [
            'jenkins-slave-builder = builder.main:main',
        ],
        'builder.commands': [
            'update = builder.commands.update:Update',
        ],
    },


    'zip_safe': False,
}

setup(**config)
