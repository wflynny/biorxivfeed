import os
import feedparser

from .conf import ConfigParser
from .pubslist import Entry, PubsList

from .utils import validate_doi

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
        pubslist.export(new_pubs, download=kwargs.get('download', False))

def remove(**kwargs) -> None:
    dois = kwargs.get('dois')
    for doi in dois:
        if not validate_doi(doi):
            raise Exception("doi %s not a valid bioRxiv doi", doi)

    configs, pubslist = preload(kwargs.get('conf')) 

    for doi in dois:
        pubslist.blacklist_doi(doi)

def list_pubs(**kwargs) -> None:
    configs, pubslist = preload(kwargs.get('conf')) 

    pubslist.list_pubs()
