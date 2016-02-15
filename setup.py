#!/usr/bin/env python

from distutils.core import setup

setup(name='Distutils',
      version='1.0',
      description='Nginx conf compiler for Marathon apps',
      author='Burak Bostancioglu',
      author_email='bostancioglub@gmail.com',
      url='https://github.com/burakbostancioglu/marangx',
      packages=['distutils', 'distutils.command'])