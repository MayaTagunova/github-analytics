# github-analytics

This script can analyze Git repositories and show some metrics

## Usage

    ./analyze.py [-h] [-b BRANCH] [-s START_DATE] [-e END_DATE] [-u USERNAME] [-t TOKEN] URL

### Positional arguments:

    URL                   Repository URL

### Optional arguments:

    -h, --help            show this help message and exit  
    
    -b BRANCH, --branch BRANCH 
    
        Branch
    
    -s START_DATE, --start_date START_DATE
    
        Start date as YYYY-MM-DD
    
    -e END_DATE, --end_date END_DATE
    
        End date as YYYY-MM-DD
    
    -u USERNAME, --username USERNAME
    
        Username
    
    -t TOKEN, --token TOKEN
    
        Authentication token  
                        
For unauthenticated requests, the API rate limit allows for up to 60 requests per hour. If that is not sufficient, you can make up to 5,000 requests per hour using an OAuth token. Provide the username and
token using the -u and -t keys.
