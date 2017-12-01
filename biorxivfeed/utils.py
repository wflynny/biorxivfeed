import re

def validate_doi(doi):
    doi_pattern = re.compile(r'^10.1101/\d+')
    if doi_pattern.match(doi):
        return True
    return False


def adjust_auth(a):
    last, first = map(str.strip, a.split(','))
    first = first.strip(',.')
    if len(first) > 1: first = first[0]
    last = last.lower().capitalize()
    return ', '.join((last, first))
