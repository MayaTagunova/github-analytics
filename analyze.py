#!/usr/bin/env python3
import sys
import getopt


def analyze():
    ...


def main():
    usage = 'Usage: analyze.py --url <url> --branch <branch> --start-date <dd.mm.yyyy> --end-date <dd.mm.yyyy>'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', ['url=', 'branch=', 'start-date=', 'end-date='])
    except getopt.GetoptError:
        print(usage)
        return 1

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

    analyze(url, branch, start_date, end_date)


if __name__ == '__main__':
    sys.exit(main())
