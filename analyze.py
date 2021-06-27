#!/usr/bin/env python3
import sys
import getopt
import os
import typing
import requests
import json
import collections

script_name = os.path.basename(__file__)
user = 'MTagunova'
password = os.environ['GITHUB_TOKEN']
base_url = 'https://api.github.com'


def show_authors(url, branch):
    repo_info = url.split('/')
    org = repo_info[-2]  # 'smartiko-ru'
    repo = repo_info[-1]  # 'loraservers'

    payload = {'per_page': 100, 'page': 1, 'sha': branch}
    if start_date is not None and end_date is not None:
        payload['since'] = f'{start_date}T00:00:00Z'
        payload['until'] = f'{end_date}T23:59:59Z'

    results = []
    while True:
        result = requests.get(f'{base_url}/repos/{org}/{repo}/commits',
                              auth=requests.auth.HTTPBasicAuth(user, password),
                              params=payload).json()
        results.extend(result)
        payload['page'] = payload['page'] + 1
        if len(result) == 0:
            break

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
