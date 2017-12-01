#!/usr/bin/env python

from distutils.core import setup

VERSION = '0.2'

setup(name='bioRxivfeed',
      version=VERSION,
      description="BioRxiv RSS feed parser",
      author="Bill Flynn",
      author_email="wflynny@gmail.com",
      install_requires = ['pyyaml', 'feedparser'],
      packages=['biorxivfeed'],
      scripts=['biorxivfeed/biorxivfeed']
      )


