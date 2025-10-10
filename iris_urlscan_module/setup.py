#!/usr/bin/env python3

#  IRIS URLScan.io Module Source Code
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
    name='iris_urlscan_module',
    version='1.0.0',
    packages=['iris_urlscan_module', 'iris_urlscan_module.urlscan_handler'],
    package_dir={'iris_urlscan_module': '.'},
    install_requires=[
        'requests>=2.25.0',
        'iris_interface'
    ],
    author="Decian",
    author_email="contact@decian.org",
    description="IRIS URLScan.io integration module for URL threat intelligence with screenshot capture",
    long_description="Provides comprehensive URL analysis using URLScan.io for domains and URLs with automatic screenshot capture, verdict analysis, geolocation data, and report generation in IRIS Notes section.",
    long_description_content_type="text/plain",
    url="https://github.com/decian/iris-urlscan-module",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: System :: Monitoring"
    ],
    python_requires='>=3.8',
    keywords='iris, threat intelligence, url analysis, urlscan, cybersecurity, incident response, screenshot'
)