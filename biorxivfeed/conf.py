import os
import sys
import yaml
import subprocess
from itertools import filterfalse

class ConfigParser(object):
    def __init__(self, conf_file):
        self.conf_file = conf_file
        self.parse_conf()

    def parse_conf(self) -> None:
        with open(self.conf_file, 'r') as fin:
            conf = yaml.load(fin)
        keywords = conf.get('keywords')
        authors = conf.get('authors')
        pubsfile = conf.get('pubsfile')
        download_dir = conf.get('pubsdownloaddir', None)

        authors = list(map(adjust_auth, authors))

        self.keywords = keywords
        self.authors = authors
        self.pubs_file = pubsfile
        self.download_dir = download_dir

class PubsList(object):
    def __init__(self, pubs_file, download_dir=None):
        self.pubs_file = pubs_file
        if download_dir:
            self.download_dir = download_dir
        else:
            self.download_dir = os.path.dirname(os.path.abspath(pubs_file))

    def parse_publist(self) -> list:
        with open(self.pubs_file, 'r') as fin:
            return list(yaml.load_all(fin))

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
        new_pubs = list(filterfalse(self.check_publist, new_pubs))
        if not new_pubs:
            return

        existing = self.parse_publist()
        pubs = existing + new_pubs
        with open(self.pubs_file, 'w+') as fout:
            yaml.dump_all(pubs, fout, explicit_start=True,
                          default_flow_style=False)

        if download:
            for pub in new_pubs:
                self.download_pub(pub)

    def download_pub(self, pub):
        try:
            subprocess.check_call(['wget', '-P', self.download_dir,
                                   pub['pdflink']])
        except subprocess.CalledProcessError:
            print("Failed to download pdf: %s"%pub['pdflink'], file=sys.stderr)

def adjust_auth(a):
    last, first = map(str.strip, a.split(','))
    first = first.strip(',.')
    if len(first) > 1: first = first[0]
    last = last.lower().capitalize()
    return ', '.join((last, first))

if __name__ == "__main__":
    test()
