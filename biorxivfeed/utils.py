import re
import sys
from datetime import datetime, timedelta
from itertools import tee, filterfalse

DOI_PREFIX = '10.1101'

def standardize_doi_list(dois):
    accepted, rejected = [], []
    for doi in dois:
        sdoi = standardize_doi(doi)
        if sdoi:
            accepted.append(sdoi)
        else:
            rejected.append(sdoi)
    return accepted, rejected
    #return list(filter(None, map(standardize_doi, dois)))

def standardize_doi(doi):
    if len(doi) == 6 and DOI_PREFIX not in doi:
        doi = '/'.join((DOI_PREFIX, doi))
    valid = validate_doi(doi)

    if valid:
        return doi
    return None

def validate_doi(doi):
    doi_pattern = re.compile(r'^%s/\d+'%DOI_PREFIX)
    _validate = lambda d: doi_pattern.match(d)

    if _validate(doi):
        return True
    return False

def adjust_auth(a):
    if ',' not in a:
        print(f'weird author name: {a}', file=sys.stderr)
    last, first = map(str.strip, a.split(','))
    first = first.strip(',.')
    if len(first) > 1: first = first[0]
    last = last.lower().capitalize()
    return ', '.join((last, first))

def partition(predicate, iterable):
    if predicate is None:
        predicate = bool
    t1, t2 = tee(iterable)
    return list(filter(predicate, t1)), list(filterfalse(predicate, t2))

def date_fudge(date_str, ndays):
    fmt = '%Y-%m-%d'
    curr_date = datetime.strptime(date_str, fmt)
    return [(curr_date - timedelta(days=i)).strftime(fmt)
            for i in range(1, ndays+1)]
