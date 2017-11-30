# bioRxivfeed

This package is a simple parser that I use to lazily browse bioRxiv's new
articles.  I felt like my search queries and general browsing would lead to
false negatives or completely missing new articles until I'd get a Google
Scholar alert a few weeks/months later.

This simple script is intended to be run regularly (e.g. via `cron`).  It reads
a list of keywords and authors that you are interested in (specified in YAML)
and will update a YAML list of bioRxiv publications of the following format:

    ---
    authors:
    - last1, F
    - last2, F
    date: '2017-11-30'
    doi: 10.1101/DOI
    keywords:
    - matched-keyword1
    - matched-keyword2
    pdflink: https://www.biorxiv.org/content/biorxiv/early/YEAR/MONTH/DAY/DOI.full.pdf
    people:
    - matched-author1
    - matched-author2
    title: Title of paper

You can optionally specify for it to automatically download the pdfs of the
articles it finds for you.

## Installation

Download and unpack or clone the repo, then

    cd biorxivfeed
    python setup.py install

or via `pip`

    pip install git+https://github.com/wflynny/biorxivfeed.git
    # or
    pip install git+git://github.com/wflynny/biorxivfeed.git

This exposes the script

    $ biorxivfeed --help
    usage: biorxivfeed [-h] [-c CONF] [-d]

    optional arguments:
      -h, --help            show this help message and exit
      -c CONF, --conf CONF  path to configuration YAML file
      -d, --download        download pdfs if possible


