'''
    Find if the total time spent on the unproductive websites is reducing
    or keep constant, or even increasing.

'''
from dataUtil import *
import json
import pickle
import tldextract
from collections import Counter
import numpy as np

'''
Helpers
'''
def get_time_stamp(line):
    return line["timestamp"]

'''
    Check if the total time spent on all unproductive websites decreases
'''

with open("domain_to_productivity.json", 'rb') as lc:
    d2productivity = json.load(lc)
d2productivity = {tldextract.extract(x).domain: d2productivity[x] for x in d2productivity}

precise_user_to_total_unproductive_time_after = dict()
#for user in domain_to_time_per_day:
# http://localhost:5000/printcollection?collection=8916c882cdc10370b3f3d205_synced:baseline_time_on_domains
link = "http://localhost:5000/get_user_to_is_logging_enabled"
userIDs = set(parse_url_as_json(link))
idx = 0
for userid in userIDs:
    if idx %100 == 0: print(str(idx) + '/' + str(len(userIDs)))
    idx+= 1
    link = "http://localhost:5000/printcollection?collection=" + userid + "_synced:seconds_on_domain_per_day"
    # print(link)
    # print("retrieving seconds_on_domain_per_day for userid = " + userid)
    f2 = urlopen(link).read()
    seconds_on_domain_per_day = json.loads(f2.decode('utf-8'))
    # filter out older version where habitlab doesn't track all websites.
    seconds_on_domain_per_day = [x for x in seconds_on_domain_per_day if
                                 x.get("habitlab_version", "0.0.0") > "1.0.231"]
    # filter those productive websites
    seconds_on_domain_per_day = [x for x in seconds_on_domain_per_day if
                                 d2productivity.get(tldextract.extract(x["key"]).domain, 0) < 0]

    if seconds_on_domain_per_day == []:
        # if this user doesn't have data after, then continue.
        continue

    '''
    # find the duration of which this user visits unproductive websites
    timestamps = [x["timestamp"] for x in seconds_on_domain_per_session]
    time_duration = np.max(timestamps) - np.min(timestamps)
    if time_duration == 0:
    # insufficient data
        continue
    '''

    website_to_log = dict()
    for line in seconds_on_domain_per_day:
        if line["key"] not in website_to_log:
            website_to_log[line["key"]] = []
        else:
            website_to_log[line["key"]].append(line)

    for web in website_to_log:
        # get the largest value on the same days with the same 'key' and 'key2'
        largest = dict()
        pop_list = []
        for i, line in enumerate(website_to_log[web]):
            try:
                if largest[line["key2"]][1] > line["val"]:
                    pop_list.append(i)
                else:
                    pop_list.append(largest[line["key2"]][0])
                    largest[line["key2"]] = (i, line["val"])
            except KeyError:
                largest[line["key2"]] = (i, line["val"])
        # pop all
        pop_list = sorted(pop_list, reverse=True)
        for p in pop_list:
            website_to_log[web].pop(p)

    day_to_unproductive_time = Counter()
    for web in website_to_log:
        for line in website_to_log[web]:
            day_to_unproductive_time[line["key2"]] += line["val"]

    # exclude the first days
    for web in website_to_log:
        if len(website_to_log[web]) == 0:
            continue
        first_day = np.min([x["key2"] for x in website_to_log[web]])
        for i, line in enumerate(website_to_log[web]):
            if line["key2"] == first_day:
                website_to_log[web].pop(i)



    precise_user_to_total_unproductive_time_after[userid] = day_to_unproductive_time


data = [np.mean(list(precise_user_to_total_unproductive_time_after[x].values())) for x in precise_user_to_total_unproductive_time_after]
print(np.nanmean(data))
print(np.nanmedian(data))

#print(np.average(list(user_to_total_unproductive_time_after.values())))

estimate_user_to_total_unproductive_time_after = dict()





