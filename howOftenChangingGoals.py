'''
    This script shows how often people change goals
    after on boarding
'''
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
import json
import pickle
from urllib.request import urlopen

with open(r"log_data\user_to_logging_enabled") as lc:
    userIDs = set(json.load(lc))

with open("get_user_to_all_install_times.json") as lc:
    installtime = json.load(lc)
installtime = {k: min(installtime[k]) for k in installtime}

num_goal_disable = []
num_goal_enable = []
for user in userIDs:
    if user not in installtime:
        continue
    # user log
    # http://localhost:5000/printcollection?collection=e98febf6f84d010a469e9d0f_logs:goals
    link = "http://localhost:5000/printcollection?collection=" + user + "_logs:goals"
    # print(link)
    # print("retrieving log for userid = " + userid)
    f = urlopen(link).read()
    parsed_raw = json.loads(f.decode('utf-8'))
    larger_than_time = 5 * 300000  # 5 min in ms
    parsed_raw = [x for x in parsed_raw if (x['timestamp'] - installtime[user] > larger_than_time)]
    # f.close()
    disabled_ = [x for x in parsed_raw if x["type"] == "goal_disabled"]
    num_goal_disable.append(len(disabled_))
    enabled_ = [x for x in parsed_raw if x["type"] == "goal_enabled"]
    num_goal_enable.append(len(enabled_))

num_goal_disable = np.array(num_goal_disable)
num_goal_enable = np.array(num_goal_enable)
# % who enabled goals
enable = (num_goal_enable != 0)
rate_enable = sum(enable)/len(userIDs)

# % who disabled goals
disable = (num_goal_disable != 0)
rate_disable = sum(disable)/len(userIDs)

# % who stayed default
default = np.logical_and(num_goal_disable == 0, num_goal_enable == 0)
rate_default = sum(default)/len(userIDs)

# % who stayed both disabled abd abled
both = sum(np.logical_and(enable, disable))
both_rate = both/len(userIDs)
# % who changed at least one
either = sum(np.logical_or(enable, disable))
either_rate = either/len(userIDs)

print(np.average(num_goal_disable))
print(np.average(num_goal_enable))

print(rate_enable)
print(rate_disable)
print(rate_default)
print(both_rate)
print(either_rate)
'''
    1. Get when usually is the first time people change their goal
    2. Get goal change/ time 
    3. 
'''