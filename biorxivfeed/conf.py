import yaml
from .utils import adjust_auth

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
        blacklist = conf.get('blacklist', None)
        pubs_cmd = conf.get('pubs_cmd_prefix', None)

        authors = list(map(adjust_auth, authors))

        self.keywords = keywords
        self.authors = authors
        self.pubs_file = pubsfile
        self.download_dir = download_dir
        self.blacklist_file = blacklist
        self.pubs_cmd_prefix = pubs_cmd
