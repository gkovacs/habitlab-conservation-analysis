from collections import Counter

import matplotlib.pyplot as plt
from dataUtil import *

from urllib.parse import urlparse
import pickle

from data_visulization_util import chisquare, print_acceptance_rate, linear, plot_dictionary, time_period, \
    select_timestamp

with open("user_took_action.json", 'rb') as lc:
    raw = json.load(lc)

with open("domain_to_productivity.json", 'rb') as lc:
    d2productivity = json.load(lc)

with open("interventionDifficulty", 'rb') as lc:
    intervention_to_difficulty = json.load(lc)

with open("log_data\\users_to_conditions_in_experiment_by_name", 'rb') as lc:
    users_to_conditions_in_experiment_by_name = json.load(lc)

user_to_installtime = parse_url_as_json("http://localhost:5000/get_user_to_all_install_times")
user_to_installtime = {k: min(user_to_installtime[k]) for k in user_to_installtime}
user_to_installtime_multiple = parse_url_as_json("http://localhost:5000/get_user_to_all_install_times")
# filter Geza
def is_blacklisted(item):
  if 'developer_mode' in item:
    return True
  if 'unofficial_version' in item:
    return True
  if item['userid'] == 'd8ae5727ab27f2ca11e331fe':
    return True
  return


raw = [x for x in raw if not is_blacklisted(x)]


#how likely are they to accept overall?
acc = 0
unique_interventions = dict()
days_of_week = dict()
day_since_install = dict()
websites = dict()
time_of_day = dict()
keys = raw[0].keys()
difficulty_to_intervention = dict()
website_to_difficulty_to_intervention = dict()
user_to_decision = dict()
user_to_yes = dict()
frequency_to_acceptance = dict()
for line in raw:
    timestamp = line['timestamp_local']
    if line['userid'] in user_to_installtime:
        install_time = user_to_installtime[line['userid']]
        d = (timestamp - install_time ) // (8.64e+7 * 7)
    else:
        d = 0


    if line['action'] == 'accepted':
        acc += 1
    website, intervention = line["intervention"].split('/')[0], line["intervention"].split('/')[1]
    if 'generated' in website:
        website = "generated"
    day, time = line["localtime"].split(' ')[0], line["localtime"].split(' ')[4].split(":")[0]
    # sort into users
    # find the chain of reactions

    if line['userid'] in user_to_decision:
        user_to_decision[line['userid']].append(line)
    else:
        user_to_decision[line['userid']] = [line]
    # sort into interventions
    if intervention not in unique_interventions:
        unique_interventions[intervention] = [line]

    else:
        unique_interventions[intervention].append(line)

    if line["intervention"] in intervention_to_difficulty:
        diff = intervention_to_difficulty[line["intervention"]]["difficulty"]
        if diff not in difficulty_to_intervention:
            difficulty_to_intervention[diff] = [line]
        else:
            difficulty_to_intervention[diff].append(line)

    # sort into day of the week
    if day not in days_of_week:
        days_of_week[day] = [line]
    else:
        days_of_week[day].append(line)

    # sort into day since install
    if d not in day_since_install:
        day_since_install[d] = [line]
    else:
        day_since_install[d].append(line)

    # sort into websites
    if website not in websites:
        websites[website] = [line]
    else:
        websites[website].append(line)

    # sort into times
    if time not in time_of_day:
        time_of_day[time] = [line]
    else:
        time_of_day[time].append(line)

    if line['userid'] in user_to_installtime_multiple:
        if len(user_to_installtime_multiple[line['userid']]) != 1:
            continue

    # sort into frequency
    try:
        condition = users_to_conditions_in_experiment_by_name[line["userid"]]
    except KeyError:
        continue

    if condition not in frequency_to_acceptance:
        frequency_to_acceptance[condition] = [line]
    else:
        frequency_to_acceptance[condition].append(line)

website_to_difficulty_to_intervention = {x:dict() for x in websites}

for website in website_to_difficulty_to_intervention:
    # sort into difficulty
    for line in websites[website]:
        if line["intervention"] in intervention_to_difficulty:
            if intervention_to_difficulty[line["intervention"]]["difficulty"] in website_to_difficulty_to_intervention[website]:
                website_to_difficulty_to_intervention[website][intervention_to_difficulty[line["intervention"]]["difficulty"]].append(line)
            else:
                website_to_difficulty_to_intervention[website][intervention_to_difficulty[line["intervention"]]["difficulty"]] = [line]

print("overall")
print(acc/len(raw))
print("---------------interventions---------------")

print_acceptance_rate(unique_interventions)
print("-----------days of the week---------------")
print_acceptance_rate(days_of_week)
print(chisquare(days_of_week))
print("---------------websites-------------------")
print_acceptance_rate(websites)
print(chisquare(websites))
print("---------------time of the day------------")
print_acceptance_rate(time_of_day)
print(chisquare(time_of_day))
print("---------------day since install----------")
print_acceptance_rate(day_since_install)
plot_dictionary(day_since_install, True, linear)
print("----------------interventions-------------")
print_acceptance_rate(unique_interventions)
acceptance_rate = plot_dictionary(unique_interventions)
print("----------------frequency-------------")
print_acceptance_rate(frequency_to_acceptance)
plot_dictionary(frequency_to_acceptance)


print("----------------difficulty----------------")
print("------total-----")
print_acceptance_rate(difficulty_to_intervention)
plot_dictionary(difficulty_to_intervention)
for website in website_to_difficulty_to_intervention:
    print("------------------------------------------")
    print(website)
    print_acceptance_rate(website_to_difficulty_to_intervention[website])
print("------------------------------------------")
for line in raw:
    if line['action'] == 'rejected':
        line['action'] == 0
    if line['action'] == 'accepted':
        line['action'] == 1

x_input = []
day_number = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, "Sat": 6, "Sun": 7}
action = {'rejected': 0, 'accepted': 1}
for line in raw:
    x = []
    for i in line:
        if i == "action":
            x.append(action[line[i]])

        if i == 'day': #or i == 'timestamp' or i == 'timestamp_local':
            x.append(int(line[i]))

        if i == 'localtime':
            x.append(line[i].split(' ')[0])
            x.append(time_period(line[i].split(' ')[4].split(':')[0]))

        if i == 'url':
            o = urlparse(line[i])
            #print(o.netloc)
            x.append(int(d2productivity.get(o.netloc, 0)))
    x_input.append(x)
with open("x_input", 'wb') as f:
    pickle.dump(x_input, f, pickle.HIGHEST_PROTOCOL)

print("-------------CHISQUARE------------------------")
print(chisquare(difficulty_to_intervention))
print("------------------------------------------")
# sort lines in user by their timestamp
for user in user_to_decision:
    user_to_decision[user] = sorted(user_to_decision[user], key=select_timestamp)

user_to_num_acc = Counter()
for user in user_to_decision:
    for line in user_to_decision[user]:
        if line["action"] == "accepted":
            user_to_num_acc[user] += 1

    if user not in user_to_num_acc:
        user_to_num_acc[user] = 0
plt.figure()
plt.hist(list(user_to_num_acc.values()), alpha=0.5)
plt.ylabel("# of users")
plt.xlabel("# of acceptance")

user_to_acc_rate = dict()

for user in user_to_decision:
    if len(user_to_decision[user]) >= 7:
        user_to_acc_rate[user] = user_to_num_acc[user]/ len(user_to_decision[user])

plt.figure()
plt.hist(list(user_to_acc_rate.values()), alpha=0.5)
plt.ylabel("# of users")
plt.xlabel("percentage of acceptance")
plt.title("Intervention Suggestions")




for user in user_to_decision:
    user_to_decision[user] = sorted(user_to_decision[user], key = lambda x: x["timestamp_local"])

last_seen_to_action = dict()
'''
for user in user_to_decision:
    timestamps = [x["timestamp"] for x in user_to_decision[user]]
    timestamps = sorted(timestamps)
    last_seens = timestamps - np.roll(timestamps, 1)
    last_seens[0] = -1
    for l in last_seens:
        last_seen_to_action[l] = (user_to_decision[user]["action"] == 'rejected')

plt.figure()
#plt.hist(list(last_seen_to_action.keys()), np.array(list(last_seen_to_action.values())))
plt.ylabel("percentage of acceptance")
plt.xlabel("time since last one")
plt.title("Intervention Suggestions")
'''


num_acc_to_median_spent_on_goal = dict()
idx = 0
for user in user_to_num_acc:
    if idx % 100 == 0: print(str(idx) + '/' + str(len(user_to_num_acc)))
    idx += 1
    num = user_to_num_acc[user]
    if user in user_to_installtime_multiple:
        if len(user_to_installtime_multiple[line['userid']]) != 1:
            continue

    if num in num_acc_to_median_spent_on_goal:
        num_acc_to_median_spent_on_goal[user_to_num_acc[user]].append(calculate_user_sec_on_goal_per_day(user))
    else:
        num_acc_to_median_spent_on_goal[user_to_num_acc[user]] = [calculate_user_sec_on_goal_per_day(user)]


plt.figure()
for num in num_acc_to_median_spent_on_goal:
    plt.hist(list(num_acc_to_median_spent_on_goal[num]), alpha=0.5, label = str(num))

plt.legend(loc='upper right')
plt.xlabel("secs on goals domain")

from scipy import stats
stats.f_oneway(list(num_acc_to_median_spent_on_goal.values()))

condition_to_median_time_spent = dict()
for user in users_to_conditions_in_experiment_by_name:
    if user in user_to_installtime_multiple:
        if len(user_to_installtime_multiple[line['userid']]) != 1:
            continue
    condition = users_to_conditions_in_experiment_by_name.get(user, "none")
    if condition == "none":
        continue
    else:
        if condition in condition_to_median_time_spent:
            condition_to_median_time_spent[condition].append(calculate_user_sec_on_goal_per_day(user))
        else:
            condition_to_median_time_spent[condition] = [calculate_user_sec_on_goal_per_day(user)]

#plt.axis([0, 10, 0, 600])
#plt.grid(True)




