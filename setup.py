__author__ = 'Amry Fitra'

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="cls_python",
    version="0.1.dev1",
    description="Cattle Livestock Device Controller",
    long_description=long_description,
    url="",
    author="Amry Amanah",
    author_email="amryfitra@gmail.com",
    license="MIT",
    packages=find_packages(),
    package_data={
        "": ['*.txt', '*.rst', '*.dll']
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities"
    ],
    entry_points={
        'console_scripts': [
            'cls_python = cls_python:main_loop',
            'cls_image_checker = cls_python:image_checker'
        ]
    }
)
