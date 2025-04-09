import os
from dotenv import load_dotenv
import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
hdlr = logging.StreamHandler()
fhdlr = logging.FileHandler("main.log")
logger.addHandler(hdlr)
logger.addHandler(fhdlr)
logger.setLevel(logging.INFO)

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
    try:
        request = requests.post(url, data=payload, headers=headers)
        return request.json()['access_token']
    except:
        logger.error('API Authentication failed, credentials incorrect or API inaccessible')

#Helper function to paginate API responses since we get 10 records per page
def paginate(url, headers, params, page):
    params['page_index'] = page
    request = requests.get(url, headers=headers, params=params)
    return request

#Takes platform, version, severity (n or higher), cases (filters bugs that don't have at least this many cases attached)
#GET using the Search Bugs by Product Series and Affected Release endpoint. Returns a list of bugids.
def get_bug_list_platform_version(platform, version, severity, cases):

    bug_list = []
    headers = {
        'Authorization' : 'Bearer ' + TOKEN
    }
    params = {
        'severity' : severity,
        'modified_date' : 5
    }

    url = BUG_SERVER + '/product_series/' + platform + '/affected_releases/' + version
    
    request = requests.get(url, headers=headers, params=params)
    last_index = request.json()['pagination_response_record']['last_index']
    page_index = request.json()['pagination_response_record']['page_index']

    #paginates the responses and stores bug IDs if there are 3 or more cases attached.
    try:
        while last_index >= page_index:
            for b in request.json()['bugs']:
                if int(b['support_case_count']) >= int(cases):
                    bug_list.append(b['bug_id'])
            
            request = paginate(url, headers, params, page_index+1)
            page_index += 1

        return bug_list
    except:
        logger.info("BUG API Response Error: " + str(request.status_code) + " " + str(request.content))


    

#Helper function to read platform.cfg file
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

#Helper function to lookup bug details in bug_list to put them in the notification
def bugs_lookup(bug_list):
    result_list = []
    headers = {
        'Authorization' : 'Bearer ' + TOKEN
    }
    url = BUG_SERVER + 'bug_ids/'
    for b in bug_list:
        request = requests.get(url + b, headers=headers)
        result_list.append(request.json()['bugs'])

    return result_list


#Log and notify based on new bugs
def notify(notify_list):
    #dedup using set. Some platforms will have the same bugs
    notify_list = set(notify_list)
    if not notify_list:
        logger.info('Ran ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' no changes ')
    else:
        logger.info('Ran ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' found bugs ' + str(notify_list))

        results_list=bugs_lookup(notify_list)

        mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        response = requests.post(
                "https://api.mailgun.net/v3/" + mailgun_domain + "/messages",
                auth=("api", os.getenv('MAILGUN_KEY')),
                data={
                    "from": "Cisco Bug Notification <postmaster@" + mailgun_domain + ">",
                    "to": "Edgar Lim <evelasq31@gmail.com>",
                    "subject": "New Cisco Bugs Discovered on Monitored Platforms",
                    "text": "List of new bugs: " + str(notify_list) + "\n" + json.dumps(results_list, indent=4)
                    }
            )
        logger.info("Mail Service Response: " + str(response.status_code) + " " + str(response.content))

#Compare bug_list to the list from saved files to see if there's anything new. Write bug files with new data.
def check_list(platform, ver, bug_list):
    #A file with old bugs exists from the last time we ran, let's check what's new, add them to notify_list
    if os.path.isfile(platform + ver + '.bug'):
            logger.info('Found File - ' + platform + ver + '.bug')
            try:
                f = open(platform + ver + '.bug', 'r')
                bugs_old = f.read().split(',')
                f.close()
                notify_list = list(set(bug_list) - set(bugs_old))
                #if list has new things, write it into the bug file.
                if notify_list:
                    f = open(platform + ver + '.bug', 'a')
                    delimiter = ","
                    f.write(',' + delimiter.join(notify_list))
                    f.close()
                return notify_list
            except:
                logger.error('Error opening file: ' + platform + ver + '.bug')

        #Initialize a file with a list of bugs, we'll use this to track compare and track changes next time this code runs.
    else:
        try:
            f = open(platform + ver + '.bug', 'w')
            delimter = ","
            f.write(delimter.join(bug_list))
            f.close()
            logger.info('New platform discovered, creating: ' + platform + ver + '.bug')
        except:
            logger.error('Error creating bug files')
        empty_list = []
        return empty_list

load_dotenv()

#load API credentials from venv


def main():
    
    global API_KEY
    global API_SECRET
    global BUG_SERVER
    global TOKEN

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

if __name__ == '__main__':
    main()
