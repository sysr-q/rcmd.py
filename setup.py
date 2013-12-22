# -*- coding: utf-8 -*-
from distutils.core import setup


def long_desc():
    with open('README.md', 'rb') as f:
        return f.read()

kw = {
    "name": "rcmd",
    "version": "1.0.2",
    "description": "Like Python's cmd module, but uses regex based handlers instead!",
    "long_description": "Does things!",  # long_desc() is pain in Py3k.
    "url": "https://github.com/plausibility/rcmd.py",
    "author": "plausibility",
    "author_email": "chris@gibsonsec.org",
    "license": "MIT",
    "packages": [
        "rcmd"
    ],
    "zip_safe": False,
    "keywords": "cmd command line loop",
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ]
}

if __name__ == "__main__":
    setup(**kw)
