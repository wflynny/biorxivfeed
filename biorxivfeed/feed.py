import os
import re
import feedparser

from .conf import adjust_auth, ConfigParser, PubsList

DEFAULT_CONF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'conf.example.yml')

FEED_URL = 'https://connect.biorxiv.org/biorxiv_xml.php?subject=all'
PDF_URL_FMT = ('https://www.biorxiv.org/content/biorxiv/early/'
               '{date[0]}/{date[1]}/{date[2]}/{doi}.full.pdf')
SANITIZERS = [
                (re.compile(r'{.*?}'), ''),
            ]

class Entry(object):

    def __init__(self, feed_item):
        self.raw = feed_item
        self._construct()

    def __repr__(self):
        return '\n'.join((self.title, self.authors[0], self.date,
                          self.doi, self.pdflink))

    def _construct(self) -> None:
        self.date = self.raw.get('date', '')

        self.title = self.raw.get('title', '')
        self.title_searchable = self._sanitize(self.title)
        self.abstract = self.raw.get('summary', '')
        self.abstract_searchable = self._sanitize(self.abstract)

        doi = self.raw.get('dc_identifier', '')
        if doi:
            doi = doi.split(':', 1)[1]
        self.doi = doi
        self.link = self.raw.get('link', '')

        authors = [d['name'].replace('.', '') for d in self.raw.get('authors')]
        self.authors = list(map(adjust_auth, authors))

        self.pdflink = PDF_URL_FMT.format(date=self.date.split('-'),
                                          doi=self.doi.split('/',1)[1])
        found_keywords = []
        found_authors = []

    def _sanitize(self, s:str) -> str:
        s = s.lower()
        for pattern, sub in SANITIZERS:
            s = re.sub(pattern, sub, s)
        return s

    def export(self) -> dict:
        return dict(title=self.title, authors=self.authors, date=self.date, 
                    doi=self.doi, pdflink=self.pdflink,
                    keywords=self.found_keywords,
                    people=self.found_authors)

    def search_for_keywords(self, keywords:list):
        found_keywords = set()
        for kw in keywords:
            if kw.lower() in self.title_searchable:
                found_keywords.add(kw)
            if self.abstract_searchable and \
                kw.lower() in self.abstract_searchable:
                found_keywords.add(kw)
        self.found_keywords = list(found_keywords)

    def search_for_authors(self, authors:list):
        found_authors = []
        for author in authors:
            if author in self.authors:
                found_authors.append(author)
        self.found_authors = found_authors

def main(**kwargs) -> None:
    configs = ConfigParser(kwargs.get('conf'))
    pubslist = PubsList(configs.pubs_file, configs.download_dir)
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
