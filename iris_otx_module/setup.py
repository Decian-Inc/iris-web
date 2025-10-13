#!/usr/bin/env python3
#  IRIS AlienVault OTX Module Source Code
#  Copyright (C) 2025 - Decian
#  contact@decian.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from setuptools import setup, find_packages

setup(
    name='iris_otx_module',
    version='1.0.0',
    packages=['iris_otx_module', 'iris_otx_module.otx_handler'],
    package_dir={'iris_otx_module': '.'},
    url='https://github.com/decian-eu/iris-otx-module',
    license='LGPL v3',
    author='Decian',
    author_email='contact@decian.org',
    description='AlienVault OTX module for IRIS',
    long_description='Provides AlienVault OTX enrichment for IRIS IOCs with automatic report generation',
    install_requires=[
        'requests>=2.25.0',
        'iris_interface'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)