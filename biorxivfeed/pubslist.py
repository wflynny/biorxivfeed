import re
import os
import sys
import yaml
import subprocess

from .utils import adjust_auth, partition, date_fudge
from .color import dye_out

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
        return ' | '.join((self.doi, self.date, self.authors[0], self.title))

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


class PubsList(object):
    def __init__(self, pubs_file, download_dir=None, blacklist_file=None):
        self.pubs_file = pubs_file
        self.download_dir = os.path.dirname(os.path.abspath(pubs_file))
        self.blacklist_file = os.path.join(self.download_dir, 'blacklist.yml')

        if download_dir:
            self.download_dir = download_dir
        if blacklist_file:
            self.blacklist_file = blacklist_file

        self.parse_blacklist()

    def parse_blacklist(self) -> list:
        with open(self.blacklist_file, 'r') as fin:
            contents = fin.read()
            if contents:
                self.blacklist = set(yaml.load(contents))
            else:
                self.blacklist = set()

    def write_blacklist(self) -> None:
        with open(self.blacklist_file, 'w+') as fout:
            yaml.dump(self.blacklist, fout, default_flow_style=False)

    def blacklist_doi(self, doi:str) -> None:
        if doi in self.blacklist:
            print(f"doi {doi} already blacklisted", file=sys.stderr)
            return
        self.blacklist.add(doi)
        self.export([])
        print(f"Successfully added {doi} to blacklist")

    def get_pdf_path(self, doi:str) -> None:
        pdfname = doi.split('/', 1)[1] + '.full.pdf'
        return os.path.join(self.download_dir, pdfname)

    def remove_pdf(self, pub_dict:dict) -> None:
        pdfpath = self.get_pdf_path(pub_dict['doi'])
        if os.path.exists(pdfpath):
            os.remove(pdfpath)
            print(f"Removed pdf for pub with doi: {pub_dict['doi']}")

    def parse_publist(self) -> list:
        with open(self.pubs_file, 'r') as fin:
            return list(yaml.load_all(fin))

    def check_blacklist(self, pub_dict:dict) -> bool:
        if pub_dict['doi'] in self.blacklist:
            return True
        return False

    def check_publist(self, pub_dict:dict) -> bool:
        pubs = self.parse_publist()
        for pub in pubs:
            if pub['doi'] == pub_dict['doi']:
                return True
        return False

    def export(self, new_pubs:list, download=False) -> None:
        """
        fmt = 
        -
        """
        existing = self.parse_publist()
        _, new_pubs = partition(self.check_publist, new_pubs)

        current_pubs = existing + new_pubs
        blacklisted, filtered = partition(self.check_blacklist, current_pubs)

        with open(self.pubs_file, 'w+') as fout:
            yaml.dump_all(filtered, fout, explicit_start=True,
                          default_flow_style=False)

        if download:
            for pub in new_pubs:
                if not self.check_blacklist(pub):
                    self.download_pub(pub)

        for pub in blacklisted:
            self.remove_pdf(pub)

        self.write_blacklist()

    def _download(self, link):
        subprocess.check_call(['wget', '-P', self.download_dir, link],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.STDOUT)

    def download_pub(self, pub:dict):
        try:
            self._download(pub['pdflink'])
        except subprocess.CalledProcessError as e:
            # hack because biorxiv doesn't put pdflinks in RSS feed and the
            # dates don't match always
            # try going back 2 days
            for date in date_fudge(pub['date'], 2):
                try: 
                    new_link = PDF_URL_FMT.format(date=date.split('-'),
                                                  doi=pub['doi'].split('/',1)[1])
                    self._download(new_link)
                    pub['pdflink'] = new_link
                    break
                except subprocess.CalledProcessError:
                    pass
            else:
                print("Failed to download pdf: %s"%pub['pdflink'], file=sys.stderr)
                raise e

    @staticmethod
    def _sort_pubs(items, way='date'):
        ways = dict(date=lambda p: p['date'],
                    auth=lambda p: p['authors'][0].split()[0],
                    doi=lambda p: p['doi'])
        return sorted(items, key=ways.get(way, None))

    def list_pubs(self, sortway=None):
        pubs = self.parse_publist()
        if sortway:
            pubs = PubsList._sort_pubs(pubs, sortway)

        for pub in pubs:
            print(' | '.join((pub['doi'], pub['date'],
                              ','.join(pub['people'] + pub['keywords']),
                              pub['authors'][0], pub['title'])))

    def list_pubs_fancy(self, sortway=None):
        pubs = self.parse_publist()
        if sortway:
            pubs = PubsList._sort_pubs(pubs, sortway)

        for pub in pubs:
            doi = dye_out(pub['doi'], 'green')
            date = dye_out(pub['date'], 'white')
            kws = ', '.join(pub['people'] + pub['keywords'])
            kws = dye_out("KEYWORDS: " + kws, 'brightyellow')
            auth = dye_out(pub['authors'][0].strip() + ' et al.', 'bwhite')
            title = dye_out(pub['title'].strip(), 'white')
            print('* ' + ' | '.join((date, doi, kws)))
            print('  '.join(('', auth, title)))
            print()

    def call_pubs_add(self, pubs_cmd_prefix, doi, tags, move=True):
        prefix = ['/bin/bash', '-i', '-c']
        cmd = []
        if pubs_cmd_prefix:
            cmd += pubs_cmd_prefix.split(' ')
            cmd.append('&&')

        existing = self.parse_publist()
        for pub in existing:
            if pub['doi'] == doi:
                break
        else:
            print(f"doi {doi} doesn't exist! Exiting", file=sys.stderr)
            exit(2)

        cmd += ['pubs', 'add', '-D', doi]
        pdfpath = self.get_pdf_path(doi)
        if os.path.exists(pdfpath):
            cmd += ['-d', pdfpath]
        if move:
            cmd += ['-M']
        if tags:
            cmd += ['-t', tags]

        res = subprocess.check_output(prefix + [' '.join(cmd)])
        print(res.decode('ascii'))

        self.blacklist_doi(doi)
