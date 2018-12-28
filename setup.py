#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @todo: https://github.com/stefankoegl/python-json-patch/blob/master/setup.py
"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGES.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.0', 'guillotina>=4.3.5', 'fhirclient', 'jsonpatch']

setup_requirements = ['pytest-runner', ]

test_requirements = [
    'coverage',
    'docker',
    'pytest',
    'pytest-asyncio',
    'pytest-cov',
    'pytest-isort',
    'pytest-docker-fixtures',
    'tox-pipenv'
]

setup(
    author="Md Nazrul Islam",
    author_email='email2nazrul@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="FHIR field for guillotina.",
    entry_points={
        'console_scripts': [
            'guillotina_fhirfield=guillotina_fhirfield.cli:main',
        ],
    },
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='guillotina_fhirfield',
    name='guillotina_fhirfield',
    packages=find_packages('src', include=['guillotina_fhirfield']),
    package_dir={'': 'src'},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    extras_require={
          'test': test_requirements + setup_requirements
    },
    url='https://github.com/nazrulworld/guillotina_fhirfield',
    version='0.1.0a2.dev0',
    zip_safe=False,
)
