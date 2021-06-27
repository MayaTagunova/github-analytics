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


def get_all_pages(query: str,
                  payload: typing.Dict[str, typing.Any],
                  options: typing.Dict[str, typing.Any]) \
        -> typing.List[typing.Any]:
    results = []
    payload = copy.copy(payload)

    auth = None
    if 'username' in options and 'token' in options:
        auth = requests.auth.HTTPBasicAuth(options['username'], options['token'])

    while True:
        response = requests.get(query,
                                auth=auth,
                                params=payload)
        response.raise_for_status()
        result = response.json()
        if len(result) == 0:
            break
        results.extend(result)
        payload['page'] = payload['page'] + 1

    return results


def print_as_table(data: typing.List[typing.Tuple[str, typing.Any]]):
    for item in data:
        print("{:<30} {:<30}".format(item[0], item[1]))


def show_authors(options: typing.Dict[str, typing.Any]):
    payload = {'per_page': 100, 'page': 1, 'sha': options['branch']}
    if 'start_date' in options:
        payload['since'] = options['start_date']
    if 'end_date' in options:
        payload['until'] = options['end_date']
    results = get_all_pages(f'''{options['base_url']}/repos/{options['owner']}/{options['repo']}/commits''',
                            payload, options)

    authors = collections.defaultdict(int)
    for item in results:
        name = item['commit']['author']['name']
        authors[name] = authors[name] + 1

    authors = sorted(authors.items(), key=lambda kv: kv[1], reverse=True)

    print_as_table([('Contributor', 'Commits count')])
    print_as_table(authors[:30])


def filter_by_date(entries: typing.List[typing.Any],
                   options: typing.Dict[str, typing.Any]) \
        -> typing.List[typing.Any]:
    results = []
    start_date = options.get('start_date', '0000-00-00T00:00:00Z')
    end_date = options.get('end_date', '9999-99-99T99:99:99Z')

    return [item for item in entries if start_date < item['created_at'] < end_date]


def filter_old(entries: typing.List[typing.Any],
               days=30) \
        -> typing.List[typing.Any]:
    results = []
    one_month_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    return [item for item in entries if item['created_at'] < one_month_ago]


def show_pull_requests(options: typing.Dict[str, typing.Any]):
    payload = {'per_page': 100, 'page': 1, 'base': options['branch']}
    pulls_url = f'''{options['base_url']}/repos/{options['owner']}/{options['repo']}/pulls'''
    results_open = filter_by_date(
                   get_all_pages(pulls_url, payload, options), options)
    payload['state'] = 'closed'
    results_closed = filter_by_date(
                     get_all_pages(pulls_url, payload, options), options)
    results_old = filter_old(results_open, days=30)

    total_data = [('Open pull requests', len(results_open)),
                  ('Closed pull requests', len(results_closed)),
                  ('Old pull requests', len(results_old))]

    print_as_table(total_data)


def show_issues(options: typing.Dict[str, typing.Any]):
    payload = {'per_page': 100, 'page': 1}
    if 'start_date' in options:
        payload['since'] = options['start_date']
    issues_url = f'''{options['base_url']}/repos/{options['owner']}/{options['repo']}/issues'''
    results_open = filter_by_date(
                   get_all_pages(issues_url, payload, options), options)
    payload['state'] = 'closed'
    results_closed = filter_by_date(
                     get_all_pages(issues_url, payload, options), options)
    results_old = filter_old(results_open, days=14)

    total_data = [('Open issues', len(results_open)),
                  ('Closed issues', len(results_closed)),
                  ('Old issues', len(results_old))]

    print_as_table(total_data)


def analyze(options: typing.Dict[str, typing.Any]):
    options['base_url'] = 'https://api.github.com'
    repo_info = options['url'].split('/')
    options['owner'] = repo_info[-2]
    options['repo'] = repo_info[-1]

    show_authors(options)
    print()
    show_pull_requests(options)
    print()
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

    options = {'branch': 'master'}

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

    if 'url' not in options:
        print(usage)
        return 1

    try:
        analyze(options)
    except requests.exceptions.HTTPError as err:
        print(err)
        return 1


if __name__ == '__main__':
    sys.exit(main())
