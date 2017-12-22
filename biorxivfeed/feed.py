import os
import sys
import feedparser

from .conf import ConfigParser
from .pubslist import Entry, PubsList

from .utils import *

DEFAULT_CONF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'conf.example.yml')

FEED_URL = 'https://connect.biorxiv.org/biorxiv_xml.php?subject=all'

def preload(conf_file):
    configs = ConfigParser(conf_file)
    pubslist = PubsList(configs.pubs_file, configs.download_dir,
                        configs.blacklist_file)

    return configs, pubslist

def scrape(**kwargs) -> None:
    configs, pubslist = preload(kwargs.get('conf')) 
    feed = feedparser.parse(FEED_URL)

    keywords, authors = configs.keywords, configs.authors

    new_pubs = []
    for item in feed['entries']:
        entry = Entry(item)
        entry.search_for_keywords(keywords)
        entry.search_for_authors(authors)

        if entry.found_keywords or entry.found_authors:
            new_pubs.append(entry.export())

    if new_pubs:
        pubslist.export(new_pubs, download=kwargs.get('download', False),
                        update=kwargs.get('update', False))

def remove(**kwargs) -> None:
    dois = kwargs.get('dois')

    accepted_dois, rejected_dois = standardize_doi_list(dois)
    if rejected_dois:
        for reject in rejected_dois:
            print("doi %s not a valid bioRxiv doi"%rejected, file=sys.stderr)
        if not accepted_dois:
            sys.exit("No valid dois to process!")

    configs, pubslist = preload(kwargs.get('conf')) 

    for doi in accepted_dois:
        pubslist.blacklist_doi(doi)

def list_pubs(**kwargs) -> None:
    configs, pubslist = preload(kwargs.get('conf')) 
    fancy = kwargs.get('fancy', False)

    sortway = None
    if kwargs.get('date_sort'): sortway = 'date'
    elif kwargs.get('doi_sort'): sortway = 'doi'
    elif kwargs.get('author_sort'): sortway = 'auth'

    if fancy:
        pubslist.list_pubs_fancy(sortway)
    else:
        pubslist.list_pubs(sortway)

def add_to_pubs(**kwargs) -> None:
    configs, pubslist = preload(kwargs.get('conf'))

    doi = kwargs.get('doi')
    doi = standardize_doi(doi)
    if not doi:
        print(f"doi {doi} isn't valid!", file=sys.stderr)
        sys.exit(2)

    prefix = configs.pubs_cmd_prefix
    tags = kwargs.get('tags', None)
    move = kwargs.get('move', False)
    pubslist.call_pubs_add(prefix, doi, tags, move=move)
