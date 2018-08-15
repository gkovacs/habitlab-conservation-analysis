# import
import numpy as np
import json
from urllib.request import urlopen
from dataUtil import parse_url_as_json

from collections import Counter

with open(r"log_data\users_to_conditions_in_experiment_by_name", 'rb') as lc:
    users_to_conditions_in_experiment_by_name = json.load(lc)
user_to_uninstall_times = parse_url_as_json("http://localhost:5000/get_user_to_all_uninstall_times")
user_to_uninstall_times = {k: max(user_to_uninstall_times[k]) for k in user_to_uninstall_times}
user_to_install_times = parse_url_as_json("http://localhost:5000/get_user_to_all_install_times")
user_to_install_times = {k: min(user_to_install_times[k]) for k in user_to_install_times}
user_to_is_alive = dict()

with open("user_suggested.txt", 'rb') as lc:
    user_suggested = json.load(lc)
# sort into user to timestamp
user_to_suggestion_timestamp = dict()
for line in user_suggested:
    if line['userid'] in user_to_suggestion_timestamp:
        if line['timestamp'] < user_to_suggestion_timestamp[line['userid']]:
            user_to_suggestion_timestamp[line['userid']] = line['timestamp']
    else:
        user_to_suggestion_timestamp[line['userid']] = line['timestamp']

print("processing users")
suggested = []
not_suggested = []
intervention_suggestion = []
idx = 0
for user in users_to_conditions_in_experiment_by_name:
    if idx % 10 == 0: print(str(idx) + "/" + str(len(users_to_conditions_in_experiment_by_name)))
    idx+= 1
    if user not in user_to_install_times:
        continue

    link = "http://localhost:5000/get_last_intervention_seen_and_time?userid=" + user
    f = urlopen(link).read()
    last_visit = json.loads(f.decode('utf-8'))["time"]
    if last_visit is None:
        continue
    time_since_install = last_visit - user_to_install_times[user]
    if user in user_to_uninstall_times:
        is_alive = 0
    else:
        is_alive = 1
    #if time_since_install/ 8.64e+7 <= 7:
    #    continue
    if users_to_conditions_in_experiment_by_name[user] == 'off':
        not_suggested.append([time_since_install/8.64e+7, int(is_alive)])
        intervention_suggestion.append([time_since_install/ 8.64e+7, int(is_alive), 0])
    else:
        suggested.append([time_since_install/8.64e+7, int(is_alive), 1])
        intervention_suggestion.append([time_since_install/ 8.64e+7, int(is_alive), 1])

import csv
with open('time_to_is_alive_suggestion.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(["days", "isAlive"])
    for i in suggested:
        spamwriter.writerow(i)
with open('time_to_is_alive_no_suggestion.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(["days", "isAlive"])
    for i in not_suggested:
        spamwriter.writerow(i)
with open('intervention_suggestion.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(["days", "isAlive", "isShownSuggesion"])
    for i in intervention_suggestion:
        spamwriter.writerow(i)

'''
user_to_time_since_first_suggestion = dict()
for user in user_to_uninstall_times:
    if user in user_to_suggestion_timestamp:
        user_to_time_since_first_suggestion[user] = user_to_uninstall_times[user] - user_to_suggestion_timestamp[user]
        user_to_is_alive[user] = False
idx = 0

for user in users_to_conditions_in_experiment_by_name:
    if idx % 100 == 0: print(str(idx) + '/' + str(len(users_to_conditions_in_experiment_by_name)))
    link = "http://localhost:5000/get_last_intervention_seen_and_time?userid=" + user
    f = urlopen(link).read()
    last_visit = json.loads(f.decode('utf-8'))["time"]
    if user in user_to_suggestion_timestamp:
        user_to_time_since_first_suggestion[user] = last_visit - user_to_suggestion_timestamp[user]
        user_to_is_alive[user] = True
    idx += 1
print("cox starting")
'''
"""
'''
do cox regression

'''
time_to_is_alive_no_suggestion = [[], []]
time_to_is_alive_suggestion = [[], []]
for user in user_to_time_since_first_suggestion:
    if users_to_conditions_in_experiment_by_name[user] == "off":
        time_to_is_alive_no_suggestion[0] += [user_to_time_since_first_suggestion[user]]
        time_to_is_alive_no_suggestion[1] += [user_to_is_alive[user]]
    else:
        time_to_is_alive_suggestion[0] += [user_to_time_since_first_suggestion[user]]
        time_to_is_alive_suggestion[1] += [user_to_is_alive[user]]

print("data processed")

import csv
with open('time_to_is_alive_suggestion.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
    for i in range(len(time_to_is_alive_suggestion[0])):
        spamwriter.writerow([time_to_is_alive_suggestion[0][i]] + [time_to_is_alive_suggestion[1][i]])
with open('time_to_is_alive_no_suggestion.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
    for i in range(len(time_to_is_alive_no_suggestion[0])):
        spamwriter.writerow([time_to_is_alive_no_suggestion[0][i]] + [time_to_is_alive_no_suggestion[1][i]])
"""
#cph = CoxPHFitter()
#cph.fit(time_to_is_alive_no_suggestion, show_progress=True, duration_col = 0, event_col=1)

#cph.print_summary()  # access the results using cph.summary

"""
sort_by_setting_tot = Counter(users_to_conditions_in_experiment_by_name.values())
sort_by_setting_uni = Counter()

for user in users_to_conditions_in_experiment_by_name:
    if user in user_to_uninstall_times:
        if user_to_uninstall_times[user] > user_to_suggestion_timestamp.get(user, 0):
            sort_by_setting_uni[users_to_conditions_in_experiment_by_name[user]] += 1

prob_tuples = []
for user in sort_by_setting_tot:
    prob_tuples.append((user,sort_by_setting_uni[user] / sort_by_setting_tot[user] ))

def get_sec(arr):
    return arr[1]
def bin_confidence(p, n):
    p = np.array(p)
    n = np.array(n)
    return 1.96 * np.sqrt(p*(1- p)/n)

prob_tuples = sorted(prob_tuples, key=get_sec)

print(prob_tuples)
print(bin_confidence([i[1] for i in prob_tuples], [sort_by_setting_tot[key[0]] for key in prob_tuples]))
# find the eaerliest intervention suggestions.
'''
plt.figure()
plt.errorbar([i[0] for i in prob_tuples], [i[1] for i in prob_tuples],yerr = bin_confidence([i[1] for i in prob_tuples],
 [sort_by_setting_tot[key[0]] for key in prob_tuples]),fmt='o')
plt.title("uninstall rate")
'''

conditions_to_time = dict()
for user in user_to_time_since_first_suggestion:
    if user_to_time_since_first_suggestion[user] > 0:
        condition = users_to_conditions_in_experiment_by_name[user]
        if condition in conditions_to_time:
            conditions_to_time[condition].append(user_to_time_since_first_suggestion[user])
        else:
            conditions_to_time[condition] = [user_to_time_since_first_suggestion[user]]

x = conditions_to_time.keys()
y = [np.average(item) * 1.15741e-8 for item in conditions_to_time.values()]
varrr = [np.var(item) * 1.15741e-8 for item in conditions_to_time.values()]

plt.figure()
plt.errorbar(x, y, fmt='o')
plt.title("average time to uninstall vs suggestion freq")

plt.figure()
plt.errorbar(x, y, fmt='o', yerr=varrr)
plt.title("average time to uninstall vs suggestion freq")

plt.show()
#stats.f_oneway(conditions_to_time.values())"""
