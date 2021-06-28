#!/usr/bin/env python3
import copy
import sys
import argparse
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
    return [item for item in entries if options['start_date'] < item['created_at'] < options['end_date']]


def filter_old(entries: typing.List[typing.Any],
               days: int = 30) \
        -> typing.List[typing.Any]:
    one_month_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [item for item in entries if item['created_at'] < one_month_ago]


def filter_issues(entries: typing.List[typing.Any]):
    return [item for item in entries if 'pull_request' not in item]


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
    results_open = filter_issues(filter_by_date(
                   get_all_pages(issues_url, payload, options), options))
    payload['state'] = 'closed'
    results_closed = filter_issues(filter_by_date(
                     get_all_pages(issues_url, payload, options), options))
    results_old = filter_old(results_open, days=14)

    total_data = [('Open issues', len(results_open)),
                  ('Closed issues', len(results_closed)),
                  ('Old issues', len(results_old))]

    print_as_table(total_data)


def analyze(options: typing.Dict[str, typing.Any]):
    options['base_url'] = 'https://api.github.com'
    repo_info = options['URL'].split('/')
    options['owner'] = repo_info[-2]
    options['repo'] = repo_info[-1]

    show_authors(options)
    print()
    show_pull_requests(options)
    print()
    show_issues(options)


def valid_date(date):
    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        msg = f''''{date}' is not a valid date'''
        raise argparse.ArgumentTypeError(msg)


def main():
    auth_info = 'For unauthenticated requests, the API rate limit allows for up to 60 requests per hour. ' \
                'If that is not sufficient, you can make up to 5,000 requests per hour using an OAuth token. ' \
                'Provide the username and token using the -u and -t keys'
    parser = argparse.ArgumentParser(epilog=auth_info)
    parser.add_argument('-b', '--branch', default='master', help='Branch')
    parser.add_argument('-s', '--start_date', type=valid_date, default='1970-01-01',
                        help='Start date as YYYY-MM-DD')
    parser.add_argument('-e', '--end_date', type=valid_date, default='9999-12-31',
                        help='End date as YYYY-MM-DD')
    parser.add_argument('-u', '--username', help='Username')
    parser.add_argument('-t', '--token', help='OAuth token')
    parser.add_argument('URL', help='Repository URL')

    try:
        options = vars(parser.parse_args())
    except argparse.ArgumentTypeError as err:
        print(err)
        return 2

    options['start_date'] = f'''{options['start_date']}T00:00:00Z'''
    options['end_date'] = f'''{options['end_date']}T23:59:59Z'''

    try:
        analyze(options)
    except requests.exceptions.HTTPError as err:
        print(err)
        return 1


if __name__ == '__main__':
    sys.exit(main())
