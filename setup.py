#!/usr/bin/env python
from setuptools import setup

setup(
    name='ddebounce',
    version='0.1.0-rc0',
    author='Student.com',
    url='http://github.com/iky/ddebounce',
    package_dir={'': 'src'},
    packages=[''],
    install_requires=[
        "redis>=2.10.5",
        'wrapt>=1.10.8',
    ],
    extras_require={
        'dev': [
            "coverage==4.5.2",
            "eventlet==0.21.0",
            "flake8==3.6.0",
            "mock==2.0.0",
            "pylint==2.2.2",
            "pytest==4.1.1",
        ],
    },
    dependency_links=[],
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
