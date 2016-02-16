#!/usr/bin/env python

from setuptools import setup

setup(name='marangx',
      version='1.0a',
      description='Nginx conf compiler for Marathon apps',
      author='Burak Bostancioglu',
      author_email='bostancioglub@gmail.com',
      url='https://github.com/burakbostancioglu/marangx',
      packages=['marangx'],
      install_requires=[
            'ipdb==0.8.1',
            'marathon',
            'json-cfg==0.3.4'
      ],
      dependency_links=[
          "git+ssh://git@github.com/burakbostancioglu/marathon-python.git#egg=marathon"
      ])