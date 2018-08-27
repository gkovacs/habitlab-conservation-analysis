'''
    Compare median time spent on target websites
    vs on unproductive website.
'''


from dataUtil import *
from data_visulization_util import *
import json
import pickle
import tldextract
from collections import Counter
import numpy as np
import os.path
import time
from scipy import stats
import matplotlib.pyplot as plt


DAYS_GROUPED_IN_MS = 5 * 8.64e+7
DAY_IN_MS = 8.64e+7
MORE_THAN_DAYS = 3
MORE_THAN_DAYS_IN_MS = MORE_THAN_DAYS * DAY_IN_MS
with open("domain_to_productivity.json", 'rb') as lc:
    d2productivity = json.load(lc)
d2productivity = {tldextract.extract(x).domain: d2productivity[x] for x in d2productivity}



link = "http://localhost:5000/get_user_to_is_logging_enabled"
userIDs = set(parse_url_as_json(link))
idx = 0

link = "http://localhost:5000/get_installs"
raw = parse_url_as_json(link)
user_to_install_version = dict()
for log in raw:
    try:
        user_to_install_version[log["user_id"]] = log["version"]
    except KeyError:
        print(log)

link = "http://localhost:5000/get_user_to_all_install_times"
user_to_installtime_multiple = parse_url_as_json(link)

user_to_installtime = {k: min(user_to_installtime_multiple[k]) for k in user_to_installtime_multiple}


user_to_goal_time = dict()
user_to_unproductive_time = dict()

for userid in userIDs:

    if idx % 100 == 0: print(str(idx) + '/' + str(len(userIDs)))
    idx += 1

    #if idx == 1000: break
    if user_to_install_version.get(userid, "0.0.0") <= "1.0.231": continue

    if len(user_to_installtime_multiple[userid]) != 1:
        continue

    link = "http://localhost:5000/get_last_intervention_seen_and_time?userid=" + userid
    last_intervention = parse_url_as_json(link)
    try:
        if last_intervention["time"] - user_to_installtime[userid] < MORE_THAN_DAYS_IN_MS: continue
    except TypeError:
        #print("typeerror:")
        #print(last_intervention)
        continue
    except KeyError:
        print("Key Error:")
        print(last_intervention)
        continue

    goal_log = parse_goal_log_for_user(userid, is_breaking_goal_list=True)
    goal_log = sorted(goal_log, key=get_time_stamp)
    link = "http://localhost:5000/printcollection?collection=" + userid + "_synced:seconds_on_domain_per_day"
    f2 = urlopen(link).read()
    seconds_on_domain_per_day = json.loads(f2.decode('utf-8'))

    # filter those productive websites
    seconds_on_domain_per_day = [x for x in seconds_on_domain_per_day if
                                 d2productivity.get(tldextract.extract(x["key"]).domain, 0) < 0]

    if seconds_on_domain_per_day == []:
        # if this user doesn't have data after, then continue.
        continue


    website_to_log = dict()
    website_to_goal_log = dict()

    # sort sessions by websites
    for line in seconds_on_domain_per_day:
        if tldextract.extract(line["key"]).domain not in website_to_log:
            website_to_log[tldextract.extract(line["key"]).domain] = [line]
        else:
            website_to_log[tldextract.extract(line["key"]).domain].append(line)

    for web in website_to_log:
        website_to_log[web] = clean_session_log(website_to_log[web])

    # sort goal logs to websites
    for line in goal_log:
        website_name = line["goal_name"].split("/")[0]
        if website_name == "custom":
            website_name = tldextract.extract(line["goal_name"].split("_")[3]).domain

        if line["goal_name"].split("/")[0] not in website_to_goal_log:
            website_to_goal_log[line["goal_name"].split("/")[0]] = [line]
        else:
            website_to_goal_log[line["goal_name"].split("/")[0]].append(line)

    # exclude the first days
    for web in website_to_log:
        if len(website_to_log[web]) == 0:
            continue
        first_day = np.min([x["key2"] for x in website_to_log[web]])
        for i, line in enumerate(website_to_log[web]):
            if line["key2"] == first_day:
                website_to_log[web].pop(i)

    web_to_time = dict()

    grouped_unproductive_time = Counter()
    grouped_goal_time = Counter()
    for web in website_to_log:
        if len(website_to_log[web]) == 0:
            continue
        for log in website_to_log[web]:
            time_since_install = log["timestamp_local"] - user_to_installtime[userid]
            current_time = log["timestamp_local"]
            '''
                Consider the time since install. Not which day calculated by the system.
            '''
            if is_habitlab_on(current_time, website_to_goal_log.get(web, [])):
                grouped_goal_time[int(time_since_install // DAY_IN_MS)] += log["val"]
            else:
                grouped_unproductive_time[int(time_since_install // DAY_IN_MS)] += log["val"]
    if len(grouped_goal_time) != 0:
        user_to_goal_time[userid] = grouped_goal_time
    if len(grouped_unproductive_time) != 0:
        user_to_unproductive_time[userid] = grouped_unproductive_time

day_since_install_to_goal_time = dict()
day_since_install_to_unproductive_time = dict()

# merge with days
for user in user_to_goal_time:
    for day in user_to_goal_time[user]:
        if day not in day_since_install_to_goal_time:
            day_since_install_to_goal_time[day] = [user_to_goal_time[user][day]]
        else:
            day_since_install_to_goal_time[day].append(user_to_goal_time[user][day])

for user in user_to_unproductive_time:
    for day in user_to_unproductive_time[user]:
        if day not in day_since_install_to_unproductive_time:
            day_since_install_to_unproductive_time[day] = [user_to_unproductive_time[user][day]]
        else:
            day_since_install_to_unproductive_time[day].append(user_to_unproductive_time[user][day])

# find average/ median for each day.

for day in day_since_install_to_goal_time:
    day_since_install_to_goal_time[day] = np.nanmean(day_since_install_to_goal_time[day])

for day in day_since_install_to_unproductive_time:
    day_since_install_to_unproductive_time[day] = np.nanmean(day_since_install_to_unproductive_time[day])

# plot function
plt.figure()
x_data_goal = sorted(day_since_install_to_goal_time.keys())
y_data_goal = [day_since_install_to_goal_time[x] for x in x_data_goal]
plt.scatter(x_data_goal, y_data_goal, label = "goal_time")

x_data_unproductive = sorted(day_since_install_to_unproductive_time.keys())
y_data_unproductive = [day_since_install_to_unproductive_time[x] for x in x_data_unproductive]
plt.scatter(x_data_unproductive, y_data_unproductive, label = "unproductive_time")

average = (np.array(y_data_unproductive[7:])+ np.array(y_data_goal))/2
plt.scatter(x_data_goal, average, label = "average")


plt.xlim(xmin = 0)
plt.xlabel("days")
plt.ylabel("time spent per day(s)")
plt.legend()

plt.show()
