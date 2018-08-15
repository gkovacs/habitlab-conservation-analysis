# process data
#from collections import Counter

#import matplotlib.pyplot as plt
from dataUtil import *
import numpy as np

#from urllib.parse import urlparse
import pickle

#from data_visulization_util import chisquare, print_acceptance_rate, linear, plot_dictionary, time_period, \
#    select_timestamp

with open("user_took_action.json", 'rb') as lc:
    raw = json.load(lc)

with open("domain_to_productivity.json", 'rb') as lc:
    d2productivity = json.load(lc)

with open("interventionDifficulty", 'rb') as lc:
    intervention_to_difficulty = json.load(lc)

user_to_installtime = parse_url_as_json("http://localhost:5000/get_user_to_all_install_times")
user_to_installtime = {k: min(user_to_installtime[k]) for k in user_to_installtime}

# seperate -- users to suggestions.
# then find the last time see an intervention suggestion.
# then find the last time see an intervention. (?)
# last session spent. (?)

user_to_suggestions = dict()
for line in raw:
    user = line["userid"]
    if user not in user_to_suggestions:
        user_to_suggestions[user] = [line]
    else:
        print(user)
        user_to_suggestions[user].append(line)

# historical time spent on websites
with open("domain_to_time_per_day", "rb") as f:
    user_to_domain_to_time_per_day = pickle.load(f)


for user in user_to_suggestions:
    user_to_suggestions[user] = sorted(user_to_suggestions[user], key = lambda x: x["timestamp_local"])
    timestamps = [x["timestamp_local"] for x in user_to_suggestions[user]]
    timedifference = timestamps - np.roll(timestamps, 1)
    timedifference[0] = -1
    is_start = [False] * len(timestamps)
    is_start[0] = True
    for i, log in enumerate(user_to_suggestions[user]):
        log["website"] = log["intervention"].split("/")[0]
        log["unique_intervention"] = log["intervention"].split("/")[1]

        log["baseline_time"] = user_to_domain_to_time_per_day[user][log["website"]]

        log["is_start"] = is_start[i]
        log["last_time_seen"] = timedifference[i]
        log["day"] = log["localtime"].split(" ")[0]
        time = log["localtime"].split(" ")[4].split(":")[0]
        if 0 < int(time) <= 6:
            log["period_of_day"] = "midnight"
        elif 6 < int(time) <= 12:
            log["period_of_day"] = "morning"
        elif 12 < int(time) <= 18:
            log["period_of_day"] = "afternoon"
        else:
            log["period_of_day"] = "evening"
print(user_to_suggestions)
# train

# evaluate
