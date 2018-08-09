from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import json
from scipy import stats
from urllib.request import urlopen
import os
from scipy.optimize import curve_fit
from dataUtil import *

from urllib.parse import urlparse
import pickle
with open("user_took_action.txt", 'rb') as lc:
    raw = json.load(lc)

with open("domain_to_productivity.json", 'rb') as lc:
    d2productivity = json.load(lc)

with open("interventionDifficulty", 'rb') as lc:
    intervention_to_difficulty = json.load(lc)

user_to_installtime = parse_url_as_json("http://localhost:5000/get_user_to_all_install_times")
user_to_installtime = {k: min(user_to_installtime[k]) for k in user_to_installtime}

# filter Geza
def is_blacklisted(item):
  if 'developer_mode' in item:
    return True
  if 'unofficial_version' in item:
    return True
  if item['userid'] == 'd8ae5727ab27f2ca11e331fe':
    return True
  return

def chisquare(dictionary):
    contigency_matrix = [[],[]]

    for line in dictionary:
        acc = 0
        rej = 0
        #print(line)
        for item in dictionary[line]:
            if item["action"] == "accepted":
                acc += 1
            else:
                rej += 1

        contigency_matrix[0].append(acc)
        contigency_matrix[1].append(rej)
    print(contigency_matrix)
    return stats.chi2_contingency(contigency_matrix)


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


def print_acceptance_rate(dictionary):
    for line in dictionary:
        acc_int = 0
        for item in dictionary[line]:
            if item['action'] == 'accepted': acc_int += 1
        print(line)
        print(acc_int / len(dictionary[line]))

def bin_confidence(p, n):
    print([p, n])
    return 1.96 * np.sqrt(p*(1- p)/n)

def linear(x, a, b):
    return a + np.multiply(x,b)

def plot_dictionary(dictionary, isRegression = False, func = None):
    acc_rate = dict()
    p = []
    n = []
    for line in sorted(dictionary.keys()):
        acc_int = 0
        for item in dictionary[line]:
            if item['action'] == 'accepted': acc_int += 1
        acc_rate[line] = (acc_int / len(dictionary[line]))
        p.append(acc_rate[line])
        n.append(len(dictionary[line]))
    p = np.array(p)
    n = np.array(n)
    plt.figure()
    plt.barh(range(len(acc_rate)), list(acc_rate.values()), align='center', xerr=bin_confidence(p, n))
    plt.yticks(range(len(acc_rate)), list(acc_rate.keys()))
    plt.show()

    if isRegression and func:
        dellist = []
        for i in range(len(p))[::-1]:
            if p[i] == 0:
                dellist.append(i)
        ydata = np.log(p)
        xdata = np.array(sorted(dictionary.keys()))
        err =  np.log(bin_confidence(p, n))



        ydata = np.delete(ydata, dellist)
        xdata = np.delete(xdata, dellist)
        err = np.delete(err, dellist)

        params, cov = curve_fit(func, xdata, ydata, sigma = err)
        residuals = ydata - func(xdata, float(params[0]), float(params[1]))
        ss_red = np.sum(residuals ** 2)
        ss_tot = np.sum((ydata - np.mean(ydata)) ** 2)
        r_sq = 1 - (ss_red / ss_tot)
        plt.figure()
        plt.title("log regression")
        plt.ylabel("log(acceptance rate)")
        plt.errorbar(xdata, ydata, err)
        plt.plot(xdata, func(xdata, params[0], params[1]), 'r-', label='fit: a=%5.3f, b=%5.3f' % tuple(params))
        print('R^2 = %1.3f' % r_sq)
    return acc_rate

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
plot_dictionary(unique_interventions)

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

def time_period(hour):
    if 0 <= int(hour) < 6:
        return 'midnight'
    if 6 <= int(hour) <= 12:
        return 'morning'
    if 12 < int(hour) <= 18:
        return 'afternoon'
    if 18 < int(hour) < 24:
        return 'evening'

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
def select_timestamp(line):
    return line["timestamp"]
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
plt.xlabel("# of acceptance")
plt.ylabel("# of users")
#plt.axis([0, 10, 0, 600])
#plt.grid(True)