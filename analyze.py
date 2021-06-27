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

script_name = os.path.basename(__file__)
user = 'MTagunova'
password = os.environ['GITHUB_TOKEN']
base_url = 'https://api.github.com'


def get_full_list(query: str, payload: typing.Dict[str, typing.Any]) -> typing.List[typing.Any]:
    results = []
    payload = copy.copy(payload)
    while True:
        result = requests.get(query,
                              auth=requests.auth.HTTPBasicAuth(user, password),
                              params=payload).json()
        results.extend(result)
        payload['page'] = payload['page'] + 1
        if len(result) == 0:
            break

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
        print(f'{item[0]}  {item[1]}')


def main():
    usage = f'Usage: {script_name} --url <url> --branch <branch> --start-date <dd.mm.yyyy> --end-date <dd.mm.yyyy>'
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

    analyze(url, branch, start_date, end_date)


if __name__ == '__main__':
    sys.exit(main())
