#!/usr/bin/env python3
import copy
import sys
import getopt
import os
import typing
import requests
import json
import collections
import copy
from datetime import datetime, timedelta


def get_full_list(query: str,
                  payload: typing.Dict[str, typing.Any],
                  options: typing.Dict[str, typing.Any]) \
        -> typing.List[typing.Any]:
    results = []
    payload = copy.copy(payload)
    while True:
        response = requests.get(query,
                                auth=requests.auth.HTTPBasicAuth(options['username'], options['token']),
                                params=payload)
        response.raise_for_status()
        result = response.json()
        if len(result) == 0:
            break
        results.extend(result)
        payload['page'] = payload['page'] + 1

    return results


def show_authors(options: typing.Dict[str, typing.Any]):
    payload = {'per_page': 100, 'page': 1, 'sha': options['branch']}
    if options['start_date'] is not None:
        payload['since'] = f'''{options['start_date']}T00:00:00Z'''
    if options['end_date'] is not None:
        payload['until'] = f'''{options['end_date']}T23:59:59Z'''
    results = get_full_list(f'''{options['base_url']}/repos/{options['owner']}/{options['repo']}/commits''',
                            payload, options)

    authors = collections.defaultdict(int)
    for item in results:
        name = item['commit']['author']['name']
        authors[name] = authors[name] + 1

    authors = sorted(authors.items(), key=lambda kv: kv[1], reverse=True)

    for item in authors[:30]:
        print(f'{item[0]}: {item[1]}')


def filter_by_date(entries: typing.List[typing.Any],
                   options: typing.Dict[str, typing.Any]) \
        -> typing.List[typing.Any]:
    results = []
    if options['start_date'] is None or options['end_date'] is None:
        return entries

    for item in entries:
        if item['created_at'] < options['start_date']:
            break
        if options['start_date'] < item['created_at'] < options['end_date']:
            results.append(item)

    return results


def filter_old(entries: typing.List[typing.Any],
               days=30) \
        -> typing.List[typing.Any]:
    results = []
    one_month_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    for item in entries:
        if item['created_at'] < one_month_ago:
            results.append(item)

    return results


def show_pull_requests(options: typing.Dict[str, typing.Any]):
    payload = {'per_page': 100, 'page': 1, 'base': options['branch']}
    pulls_url = f'''{options['base_url']}/repos/{options['owner']}/{options['repo']}/pulls'''
    results_open = filter_by_date(
                   get_full_list(pulls_url, payload, options), options)
    payload['state'] = 'closed'
    results_closed = filter_by_date(
                    get_full_list(pulls_url, payload, options), options)
    results_old = filter_old(results_open, days=30)

    print(f'Open pull requests: {len(results_open)}')
    print(f'Closed pull requests: {len(results_closed)}')
    print(f'Old pull requests: {len(results_old)}')


def show_issues(options: typing.Dict[str, typing.Any]):
    payload = {'per_page': 100, 'page': 1}
    if options['start_date'] is not None:
        payload['since'] = f'''{options['start_date']}T00:00:00Z'''
    issues_url = f'''{options['base_url']}/repos/{options['owner']}/{options['repo']}/issues'''
    results_open = filter_by_date(
                   get_full_list(issues_url, payload, options), options)
    payload['state'] = 'closed'
    results_closed = filter_by_date(
                    get_full_list(issues_url, payload, options), options)
    results_old = filter_old(results_open, days=14)

    print(f'Open issues: {len(results_open)}')
    print(f'Closed issues: {len(results_closed)}')
    print(f'Old issues: {len(results_old)}')


def analyze(options: typing.Dict[str, typing.Any]):
    options['base_url'] = 'https://api.github.com'
    repo_info = options['url'].split('/')
    options['owner'] = repo_info[-2]
    options['repo'] = repo_info[-1]

    show_authors(options)
    print('...')
    show_pull_requests(options)
    print('...')
    show_issues(options)


def main():
    script_name = os.path.basename(__file__)
    usage = f'Usage: {script_name} < -u url > ' \
            f'[ -B branch ] [ -S start-date ] [ -E end-date ] ' \
            f'[ -U username ] [ -T token ] '
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hu:B:S:E:U:T:',
                                   ['help', 'url=', 'branch=', 'start-date=', 'end-date=', 'username=', 'token='])
    except getopt.GetoptError:
        print(usage)
        return 1

    options = {'url': '',
                  'branch': 'master',
                  'start_date': None,
                  'end_date': None}

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage)
            return 1
        elif opt in ('-u', '--url'):
            options['url'] = arg
        elif opt in ('-B', '--branch'):
            options['branch'] = arg
        elif opt in ('-S', '--start-date'):
            options['start_date'] = f'''{arg}T00:00:00Z'''
        elif opt in ('-E', '--end-date'):
            options['end_date'] = f'''{arg}T23:59:59Z'''
        elif opt in ('-U', '--username'):
            options['username'] = arg
        elif opt in ('-T', '--token'):
            options['token'] = arg

    if options['url'] == '':
        print(usage)
        return 1

    try:
        analyze(options)
    except requests.exceptions.HTTPError as err:
        print(err)
        return 1


if __name__ == '__main__':
    sys.exit(main())
