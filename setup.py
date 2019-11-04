#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import sys
from setuptools import setup


if sys.version_info < (3,):
    versioned_requirements = ["wait-for<1.1.0"]
else:
    versioned_requirements = ["wait-for"]

requirements = ["requests", "iso8601", "simplejson", "six"]
requirements.extend(versioned_requirements)

setup(
    name="manageiq-client",
    use_scm_version=True,
    author="Milan Falesnik",
    author_email="mfalesni@redhat.com",
    description="Python client for the ManageIQ REST-API",
    license="GPLv2",
    keywords=['api', 'rest', 'client', 'manageiq'],
    url="https://github.com/ManageIQ/manageiq-api-client-python",
    packages=["manageiq_client"],
    package_dir={'': 'src'},
    install_requires=requirements,
    setup_requires=[
        'setuptools_scm',
    ],
    classifiers=[
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
    ]
)
