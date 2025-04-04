import os
from dotenv import load_dotenv
import requests
import json
import logging
from datetime import datetime

#TEST new bug. Two new bugs in consecutive days. Two new bugs in the same day. Duplicate bugs in platforms. 3+ platforms

logger = logging.getLogger(__name__)
logging.basicConfig(filename='main.log', level=logging.INFO)
#Setup Authentication Token
def get_token():

    url='https://id.cisco.com/oauth2/default/v1/token'

    headers = {
        "Content-Type":"application/x-www-form-urlencoded"
    }
    payload = {
        "grant_type" : "client_credentials",
        "client_id" : API_KEY,
        "client_secret" : API_SECRET
    }

    request = requests.post(url, data=payload, headers=headers)
    return request.json()['access_token']

#Helper function to paginate API responses since we get 10 records per page
def paginate(url, headers, params, page):
    params['page_index'] = page
    request = requests.get(url, headers=headers, params=params)
    return request

#Takes platform, version, severity (n or higher), cases (filters bugs that don't have at least this many cases attached)
#Gets the Search Bugs by Product Series and Affected Release endpoint
def get_bug_list_platform_version(platform, version, severity, cases):

    bug_list = []
    headers = {
        'Authorization' : 'Bearer ' + TOKEN
    }
    params = {
        'severity' : severity,
    }

    url = BUG_SERVER + '/product_series/' + platform + '/affected_releases/' + version
    
    request = requests.get(url, headers=headers, params=params)
    last_index = request.json()['pagination_response_record']['last_index']
    page_index = request.json()['pagination_response_record']['page_index']

    #paginates the responses and stores bug IDs if there are 3 or more cases attached.

    while last_index > page_index:
        for b in request.json()['bugs']:
            if int(b['support_case_count']) > int(cases):
                bug_list.append(b['bug_id'])
        
        request = paginate(url, headers, params, page_index+1)
        page_index += 1


    return bug_list

def read_platform_cfg():
    platform_list = []
    if os.path.isfile('platform.cfg'):
        try:
            platforms = open('platform.cfg', 'r')
            platform_list = platforms.read().splitlines()
            platforms.close()
        except:
            print('Error opening platform.cfg')
    return platform_list


def notify(notify_list):
    if not notify_list:
        logging.info('Ran ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' no changes ')
    else:
        #REMEMBER TO DEDUP
        logging.info('Ran ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' found bugs ' + str(notify_list))

def check_list(platform, ver, bug_list):
    #A file with old bugs exists from the last time we ran, let's check what's new, add them to notify_list
    if os.path.isfile(platform + ver):
            logger.info('Found File - ' + platform + ver)
            try:
                f = open(platform + ver, 'r')
                bugs_old = f.read().split(',')
                f.close()
                notify_list = list(set(bug_list) - set(bugs_old))
                f = open(platform + ver, 'a')
                delimiter = ","
                f.write(',' + delimiter.join(notify_list))
                f.close()
                return notify_list
            except:
                logging.error('Error opening file: ' + platform + ver)

        #Initialize a file with a list of bugs, we'll use this to track compare and track changes next time this code runs.
    else:
        try:
            f = open(platform + ver, 'w')
            delimter = ","
            f.write(delimter.join(bug_list))
            f.close()
        except:
            logging.error('Error creating bug files')



#load API credentials from venv
load_dotenv()
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BUG_SERVER = 'https://apix.cisco.com/bug/v2.0/bugs/'
TOKEN = get_token()

#iterate through platform.cfg to get the platform/software and parameters we're checking
platform_list = read_platform_cfg()
notify_list = []
for line in platform_list:
    line = line.split(',')
    platform = line[0].strip()
    ver = line[1].strip()
    sev = line[2].strip()
    cases = line[3].strip()

    #get fresh list of all bugids for the given platform/software
    bug_list = get_bug_list_platform_version(platform, ver, sev, cases)

    #check if there's any new bugs, if so append it to notify_list
    notify_list.extend(check_list(platform, ver, bug_list))

#check for duplicates and then send notification!
notify(notify_list)


#print(get_bug_list_platform_version('Cisco Catalyst 9300 Series Switches', '17.6.5', 2, 3))
#If file does not exist, write a file with comma seperated list of bug ids.
#If file exists, do we have a new bug? If yes, call api for bug details. Send notification. Write file with new list

#if os.path.isfile('')