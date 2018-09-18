'''
    Find user's average visits to all websites and dump to a
    pickle.
    Consider user of above 1 day of usage and data after 1 day
    jmhnuyylk

'''
import lzstring
import json
import pickle
from urllib.request import urlopen
# from urllib.parse import urlparse
import tldextract
from dataUtil import *
'''
    Parse historic daily visit seconds.

'''


#with open(r"log_data\user_to_logging_enabled") as lc:
#    userIDs = set(json.load(lc))

raw = parse_url_as_json("http://localhost:5000/get_user_to_is_logging_enabled")
userIDs = [x for x in raw if raw[x]]

# http://localhost:5000/printcollection?collection=4b4f9c958b5ac79e3deb470c_synced:history_vars

lzs = lzstring.LZString()
user_to_average_website_visits = dict()
idx = 0
for userid in userIDs:
    user_to_average_website_visits[userid] = dict()
    if idx % 100 == 0: print(str(idx) + "/" + str(len(userIDs)))
    idx += 1

    link = "http://localhost:5000/printcollection?collection=" + userid + "_synced:history_vars"

    f = urlopen(link).read()
    parsed_raw = json.loads(f.decode('utf-8'))

    if len(parsed_raw) == 0: continue
    # print(parsed_raw)
    history_string = parsed_raw[0]["val"]
    # decode
    history_string = lzs.decompressFromEncodedURIComponent(history_string)
    try:
        history = eval(history_string)
    except UnicodeEncodeError:
        print("unicode error")
        continue
    website_to_visits = dict()

    for line in history:
        try:
            visits = history[line][2]
            first = history[line][4]
            last = history[line][5]
        except TypeError:
            print(line)
            continue
        domain = tldextract.extract(line)
        #print(domain.domain)
        if last - first != 0:
            ONEDAY = 8.64e+7
            time_gap = last - first
            if domain.domain in website_to_visits:
                if time_gap > ONEDAY:
                    website_to_visits[domain.domain][0] += visits
                    website_to_visits[domain.domain][1] = min(website_to_visits[domain.domain][1], first)
                    website_to_visits[domain.domain][2] = max(website_to_visits[domain.domain][2], last)
            else:
                if time_gap > ONEDAY: website_to_visits[domain.domain] = [visits, first, last]
        else:
            website_to_visits[domain.domain] = [0, 0, 0]
    for domain in website_to_visits:
        item = website_to_visits[domain]
        timegap = item[2] - item[1]
        if timegap == 0:
            visits_to_time = 0
        else:
            visits_to_time = item[0]/ timegap

        user_to_average_website_visits[userid][domain] = visits_to_time

with open("user_to_average_website_visits", 'wb') as f:
    pickle.dump(user_to_average_website_visits, f, pickle.HIGHEST_PROTOCOL)

