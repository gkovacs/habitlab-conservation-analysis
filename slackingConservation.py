'''
    Find if the total time spent on the unproductive websites is reducing
    or keep constant, or even increasing.  --- the total time decreases.

    Find if the net time spent changes on the unproductive website is
    +/-.
'''
from dataUtil import *
import json
import pickle
import tldextract
from collections import Counter
import numpy as np
import os.path
import time
from scipy import stats
import matplotlib.pyplot as plt
from scipy.stats import sem
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

'''
This is a hack
'''
if os.path.isfile("domain_to_time_per_day"):
    with open("domain_to_time_per_day", "rb") as f:
        """
            This is from calculateBaseline data.
        """
        domain_to_time_per_day = pickle.load(f)
else:
    from calculateBaselinePerSession import *

user_to_total_unproductive_time_before = Counter()
user_to_fb_ytb_to_other_unproductive_time_before = dict()
for user in domain_to_time_per_day:
    user_to_fb_ytb_to_other_unproductive_time_before[user] = [0, 0]
    for website in domain_to_time_per_day[user]:
        if website in d2productivity:
            if d2productivity[website] < 0:
                user_to_total_unproductive_time_before[user] += domain_to_time_per_day[user][website]


            # since users always have goals for facebook and youtube...
            if website in ["facebook", "youtube"]:
                user_to_fb_ytb_to_other_unproductive_time_before[user][0] += domain_to_time_per_day[user][website]/1000
            elif website not in ["facebook", "youtube"] and d2productivity[website] < 0:
                user_to_fb_ytb_to_other_unproductive_time_before[user][1] += domain_to_time_per_day[user][website]/1000

print("unproductive time before")
print(np.nanmedian(list(user_to_total_unproductive_time_before.values())))
print(np.nanmean(list(user_to_total_unproductive_time_before.values())))
print(sem(list(user_to_total_unproductive_time_before.values())))


with open("user_to_total_unproductive_time_before", "wb") as f:
    pickle.dump(user_to_total_unproductive_time_before, f)


user_to_total_unproductive_time_after = dict()
user_to_ungoal_time_comparison = dict()
user_to_goal_type = dict()
#user_to_fb_ytb_to_other_unproductive_time_after = dict()
#for user in domain_to_time_per_day:
# http://localhost:5000/printcollection?collection=8916c882cdc10370b3f3d205_synced:baseline_time_on_domains

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

for userid in userIDs:

    if idx %100 == 0: print(str(idx) + '/' + str(len(userIDs)))
    idx += 1

    #if idx == 1000: break
    if user_to_install_version.get(userid, "0.0.0") <= "1.0.231": continue


    goal_log = parse_goal_log_for_user(userid, is_breaking_goal_list=False)
    goal_log = sorted(goal_log, key=get_time_stamp)
    link = "http://localhost:5000/printcollection?collection=" + userid + "_synced:seconds_on_domain_per_day"
    # print(link)
    # print("retrieving seconds_on_domain_per_day for userid = " + userid)
    f2 = urlopen(link).read()
    seconds_on_domain_per_day = json.loads(f2.decode('utf-8'))
    # filter out older version where habitlab doesn't track all websites.
    seconds_on_domain_per_day = [x for x in seconds_on_domain_per_day if
                                 x.get("habitlab_version", "0.0.0") >= "1.0.231"]
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
        website_to_log[web] = clean_session_log(website_to_log[web])


    # exclude the first days
    for web in website_to_log:
        if len(website_to_log[web]) == 0:
            continue
        first_day = np.min([x["key2"] for x in website_to_log[web]])
        for i, line in enumerate(website_to_log[web]):
            if line["key2"] == first_day:
                website_to_log[web].pop(i)

    website_to_log = {x:website_to_log[x] for x in website_to_log if website_to_log[x] != []}
    day_to_unproductive_time_total = Counter()
    #day_to_fb_ytb_unproductive_time_to_others = dict()

    for web in website_to_log:
        for line in website_to_log[web]:
            day_to_unproductive_time_total[line["key2"]] += line["val"]

    '''
        do the comparison between ungoaled sites.
    
    '''
    group_time = [[user_to_fb_ytb_to_other_unproductive_time_before[userid][1], 0]]
    group_goal_type = []
    num_log = 0
    while num_log < len(goal_log):
        is_enable = True
        prev = goal_log[num_log]["timestamp_local"]
        if num_log == len(goal_log) - 1:
            aft = int(time.time() * 1000)
        else:
            aft = goal_log[num_log + 1]["timestamp_local"]
        prev_goals = list(goal_log[num_log].get('prev_enabled_goals'))
        after_goals = list(goal_log[num_log].get('enabled_goals'))

        """
        next_goal = goal_log[num_log].get('goal_name', goal_log[num_log]['goal_list'])

        if goal_log[num_log + 1]["type"] == "goal_enabled":
            after_goals = prev_goals.remove(next_goal)
        else:
            after_goals = prev_goals.append(next_goal)
            is_enable = False
        """

        group_goal_type.append(goal_log[num_log]["type"] == "goal_enabled")
        # strip the goals to website names
        #prev_goals = [x.split("/")[0] for x in prev_goals]
        for i in range(len(prev_goals)):
            if prev_goals[i].split("/")[0] != "custom":
                prev_goals[i] = prev_goals[i].split("/")[0]
            else:
                prev_goals[i] = tldextract.extract(prev_goals[i].split("/")[1].split("_")[3]).domain

        for i in range(len(after_goals)):
            if after_goals[i].split("/")[0] != "custom":
                after_goals[i] = after_goals[i].split("/")[0]
            else:
                after_goals[i] = tldextract.extract(after_goals[i].split("/")[1].split("_")[3]).domain

        '''
        # strip the "generated" sites goals into website names
        for i, goal in enumerate(prev_goals):
            if "generated" in goal:
                prev_goals[i] = goal.split("_")[1]

        for i, goal in enumerate(after_goals):
            if "generated" in goal:
                after_goals[i] = goal.split("_")[1]
        '''

        group_time.append([0, 0])
        for web in website_to_log:
            web_domain = tldextract.extract(web).domain
            if web_domain not in prev_goals:
                temp = [x for x in website_to_log[web] if
                        x["timestamp_local"] <
                        aft]
                temp = [x for x in temp if x["timestamp_local"] > prev]

                sum_time = sum([t["val"] for t in temp])
                group_time[num_log][1] += sum_time

            if web_domain not in prev_goals and web_domain not in after_goals:
                temp = [x for x in website_to_log[web] if
                        x["timestamp_local"] < aft]
                temp = [x for x in temp if x["timestamp_local"] > prev]

                sum_time = sum([t["val"] for t in temp])
                group_time[num_log + 1][0] += sum_time

        num_log += 1
    user_to_ungoal_time_comparison[userid] = group_time
    user_to_goal_type[userid] = group_goal_type

    user_to_total_unproductive_time_after[userid] = day_to_unproductive_time_total
    #user_to_fb_ytb_to_other_unproductive_time_after[userid] = day_to_fb_ytb_unproductive_time_to_others

for user in user_to_ungoal_time_comparison:
    user_to_ungoal_time_comparison[user].pop(len(user_to_ungoal_time_comparison[user]) - 1)

user_to_enable_disable = dict()
enabled_net_change = []
disabled_net_change = []
for user in user_to_ungoal_time_comparison:
    if len(user_to_ungoal_time_comparison[user]) == 0: continue
    user_to_ungoal_time_comparison[user] = np.array(user_to_ungoal_time_comparison[user])[..., 1] - \
                                           np.array(user_to_ungoal_time_comparison[user])[..., 0]
    enabled_net_change.append(np.mean([item for x, item in enumerate(user_to_ungoal_time_comparison[user]) if
                                   user_to_goal_type[user][x] and item != 0]))
    disabled_net_change.append(np.mean([item for x, item in enumerate(user_to_ungoal_time_comparison[user]) if
                                    not user_to_goal_type[user][x] and item != 0]))

'''
print(np.average(list(user_to_total_unproductive_time_before.values())) * 2.7778e-7)
data_total = [np.mean(list(user_to_total_unproductive_time_after[x].values())) for x in user_to_total_unproductive_time_after]
print(np.nanmean(data_total))
print(np.nanmedian(data_total))
'''
enabled_net_change = [x for x in enabled_net_change if not np.isnan(x)]
disabled_net_change = [x for x in disabled_net_change if not np.isnan(x)]

print(np.nanmedian(enabled_net_change))
print(np.nanmedian(disabled_net_change))
stats.ttest_ind(enabled_net_change, disabled_net_change)
plt.bar(["enabled", "disabled"], [np.nanmedian(enabled_net_change), np.nanmedian(disabled_net_change)],align='center',
        yerr = [sem(enabled_net_change), sem(disabled_net_change)])
plt.title("net change in time spent after goal switch")
plt.ylable("time(s)")
'''
print(np.average(list(user_to_fb_ytb_to_other_unproductive_time_before.values())) * 2.7778e-7)
data_fb_to_others = [np.mean(list(user_to_fb_ytb_to_other_unproductive_time_after[x].values())) for x in user_to_fb_ytb_to_other_unproductive_time_before]
print(np.nanmean(data_fb_to_others))
print(np.nanmedian(data_fb_to_others))
'''

#print(np.average(list(user_to_total_unproductive_time_after.values())))
