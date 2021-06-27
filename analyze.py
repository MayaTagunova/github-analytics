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

script_name = os.path.basename(__file__)
user = 'MTagunova'
password = os.environ['GITHUB_TOKEN']
base_url = 'https://api.github.com'


def get_full_list(query: str, payload: typing.Dict[str, typing.Any]) -> typing.List[typing.Any]:
    results = []
    payload = copy.copy(payload)
    while True:
        response = requests.get(query,
                              auth=requests.auth.HTTPBasicAuth(user, password),
                              params=payload)
        response.raise_for_status()
        result = response.json()
        if len(result) == 0:
            break
        results.extend(result)
        payload['page'] = payload['page'] + 1

    return results


def show_authors(owner: str, repo: str, branch: str):
    payload = {'per_page': 100, 'page': 1, 'sha': branch}
    results = get_full_list(f'{base_url}/repos/{owner}/{repo}/commits', payload)

    authors = collections.defaultdict(int)
    for item in results:
        name = item['commit']['author']['name']
        authors[name] = authors[name] + 1

    authors = sorted(authors.items(), key=lambda kv: kv[1], reverse=True)

    for item in authors[:30]:
        print(f'{item[0]}: {item[1]}')


def filter_by_date(entries: typing.List[typing.Any],
                   start_date: typing.Optional[str] = None, end_date: typing.Optional[str] = None) \
        -> typing.List[typing.Any]:
    results = []
    if start_date is None or end_date is None:
        return entries
    start_date = f'{start_date}T00:00:00Z'
    end_date = f'{end_date}T23:59:59Z'

    for item in entries:
        if item['created_at'] < start_date:
            break
        if start_date < item['created_at'] < end_date:
            results.append(item)

    return results


def filter_old(entries: typing.List[typing.Any], days=30) -> typing.List[typing.Any]:
    results = []
    one_month_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    for item in entries:
        if item['created_at'] < one_month_ago:
            results.append(item)

    return results


def show_pull_requests(owner: str, repo: str, branch: str,
                       start_date: typing.Optional[str] = None, end_date: typing.Optional[str] = None):
    payload = {'per_page': 100, 'page': 1, 'base': branch}

    results_open = filter_by_date(
                   get_full_list(f'{base_url}/repos/{owner}/{repo}/pulls', payload), start_date, end_date)
    payload['state'] = 'closed'
    results_closed = filter_by_date(
                    get_full_list(f'{base_url}/repos/{owner}/{repo}/pulls', payload), start_date, end_date)
    results_old = filter_old(results_open, days=30)

    print(f'Open pull requests: {len(results_open)}')
    print(f'Closed pull requests: {len(results_closed)}')
    print(f'Old pull requests: {len(results_old)}')


def show_issues(owner: str, repo: str,
                start_date: typing.Optional[str] = None, end_date: typing.Optional[str] = None):
    payload = {'per_page': 100, 'page': 1}
    if start_date is not None:
        payload['since'] = f'{start_date}T00:00:00Z'

    results_open = filter_by_date(
                   get_full_list(f'{base_url}/repos/{owner}/{repo}/issues', payload), start_date, end_date)
    payload['state'] = 'closed'
    results_closed = filter_by_date(
                    get_full_list(f'{base_url}/repos/{owner}/{repo}/issues', payload), start_date, end_date)
    results_old = filter_old(results_open, days=14)

    print(f'Open issues: {len(results_open)}')
    print(f'Closed issues: {len(results_closed)}')
    print(f'Old issues: {len(results_old)}')


def analyze(url, branch, start_date: typing.Optional[str] = None, end_date: typing.Optional[str] = None):
    repo_info = url.split('/')
    owner = repo_info[-2]
    repo = repo_info[-1]

    show_authors(owner, repo, branch)
    print('...')
    show_pull_requests(owner, repo, branch, start_date, end_date)
    print('...')
    show_issues(owner, repo, start_date, end_date)


def main():
    usage = f'Usage: {script_name} --url <url> [--branch <branch>] [--start-date <dd.mm.yyyy> --end-date <dd.mm.yyyy>]'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', ['url=', 'branch=', 'start-date=', 'end-date='])
    except getopt.GetoptError:
        print(usage)
        return 1

    url = ''
    branch = 'master'
    start_date = None
    end_date = None

    for opt, arg in opts:
        if opt == '-h':
            print(usage)
            return 1
        elif opt == '--url':
            url = arg
        elif opt == '--branch':
            branch = arg
        elif opt == '--start-date':
            start_date = arg
        elif opt == '--end-date':
            end_date = arg

    if url == '':
        print(usage)
        return 1

    try:
        analyze(url, branch, start_date, end_date)
    except requests.exceptions.HTTPError as err:
        print(err)
        return 1


if __name__ == '__main__':
    sys.exit(main())
