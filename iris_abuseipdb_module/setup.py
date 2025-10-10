#!/usr/bin/env python3

from setuptools import setup

setup(
    name='iris_abuseipdb_module',
    version='1.0.0',
    packages=['iris_abuseipdb_module', 'iris_abuseipdb_module.abuseipdb_handler'],
    package_dir={'iris_abuseipdb_module': '.'},
    license='LGPL-3.0',
    description='IRIS AbuseIPDB integration module',
    author='Decian',
    author_email='contact@decian.org',
    keywords=['iris', 'abuseipdb', 'threat intelligence', 'security'],
    install_requires=[
        'requests>=2.25.0',
        'iris_interface'
    ],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)