#!/usr/bin/env python
from setuptools import setup

setup(
    name='ddebounce',
    version='0.0.1',
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
            "coverage==4.3.4",
            "eventlet==0.21.0",
            "flake8==3.3.0",
            "mock==2.0.0",
            "pylint==1.7.1",
            "pytest==3.0.6",
            "requests-mock==1.3.0",
        ],
    },
    dependency_links=[],
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
