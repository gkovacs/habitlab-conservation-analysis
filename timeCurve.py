
# import
import numpy as np
import json
from urllib.request import urlopen
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import pickle
import os.path

def linear(x, a, b):
    return a * x + b

def poly(x, a, b, c, d, e):
    return a * x ** 4+ b * x ** 3 + c * x ** 2 + d * x + e

def rsquare(xdata, ydata, popt, func):
    residuals = ydata - func(xdata, *popt)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((ydata - np.mean(ydata)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared

def bisection(array, value):
    '''Given an ``array`` , and given a ``value`` , returns an index j such that ``value`` is between array[j]
        and array[j+1]. ``array`` must be monotonic increasing. j=-1 or j=len(array) is returned
        to indicate that ``value`` is out of range below and above respectively.'''
    n = len(array)
    if (value < array[0]):
        return -1
    elif (value > array[n - 1]):
        return n
    jl = 0  # Initialize lower
    ju = n - 1  # and upper limits.
    while (ju - jl > 1):  # If we are not yet done,
        jm = (ju + jl) >> 1  # compute a midpoint with a bitshift
        if (value >= array[jm]):
            jl = jm  # and replace either the lower limit

        else:
            ju = jm  # or the upper limit, as appropriate.

        # Repeat until the test condition is satisfied.

    if (value == array[0]):  # edge cases at bottom
        return 0
    elif (value == array[n - 1]):  # and top
        return n - 1
    else:
        return jl


def if_habitlab_on(timestamp, log):
    '''
            given a timestamp, and a log of the user goal enableness, determine
            if the habit lab is on at that timestamp
        '''
    timestamp_list = [x["timestamp"] for x in log]
    index = bisection(timestamp_list, timestamp)  # the index of which the timestamp just falls after
    # print(str(index) + " " + str(timestamp_list[index]) + " " + str(timestamp))
    # for prehistoric time no one enables HabitLab
    if index == -1:
        return False
    if index == len(log):
        '''if the value is above the largest value in the list
                '''
        index -= 1

    if log[index]["type"] == "goal_enabled":
        return True
    elif log[index]["type"] == "goal_disabled":
        return False
    return


def get_time_stamp(item):
    return item["timestamp"]


with open("get_user_to_all_install_times.json") as lc:
    installtime = json.load(lc)
installtime = {k: min(installtime[k]) for k in installtime}
# read a unique user list

with open("uniqueUserIds.json") as lc:
    userIDs = set(json.load(lc))

    success = 0
    fail = 0

we = ["facebook", "reddit", "twitter", "youtube", "gmail"]

for w in we:
    print("processing " + w)
    # traverse thu all users to obtain t/f average time spent on websites per day/ per session reduced after enabling the goals
    timeon_months_list = [[], [], [], [], [], [], [], [], [], [], [], [], [], []]
    time_since_months_list = [[], [], [], [], [], [], [], [], [], [], [], [], [], []]
    idx = 0
    if os.path.isfile(w + "timeon_months_list.pickel") and os.path.isfile(w + "time_since_months_list.pickel"):
        with open(w + "timeon_months_list.pickel", 'rb') as f:
            timeon_months_list = pickle.load(f)

        with open(w + "time_since_months_list.pickel", 'rb') as f:
            time_since_months_list = pickle.load(f)
    else:
        for userid in userIDs:
            if idx % 100 == 0 : print(str(idx) + "/" + str(len(userIDs)))

            idx += 1
            num_month = 0
            try:
                install = installtime[userid]
            except KeyError:
                continue
            # user log
            # http://localhost:5000/printcollection?collection=e98febf6f84d010a469e9d0f_logs:goals
            link = "http://localhost:5000/printcollection?collection=" + userid + "_logs:goals"
            # print(link)
            # print("retrieving log for userid = " + userid)
            f = urlopen(link).read()
            parsed_raw = json.loads(f.decode('utf-8'))

            '''
            raw = ""
            with open("data.txt",encoding='utf-8', mode = 'r') as f:
                raw = f.read()
            parsed_raw = json.loads(raw)
            '''

            # filter out those without goal_name
            parsed_raw = [i for i in parsed_raw if "goal_name" in i]

            # secs on a website per session
            # http://localhost:5000/printcollection?collection=683c1e28dcad53573b3f2c83_synced:seconds_on_domain_per_day
            link = "http://localhost:5000/printcollection?collection=" + userid + "_synced:seconds_on_domain_per_day"
            # print(link)
            # print("retrieving seconds_on_domain_per_day for userid = " + userid)

            f2 = urlopen(link).read()
            seconds_on_domain_per_session = json.loads(f2.decode('utf-8'))



            '''
            seconds_on_domain_per_session = ""
            with open("seconds_on_domain_per_day.txt",encoding='utf-8', mode = 'r') as f:
                seconds_on_domain_per_session = f.read()
            seconds_on_domain_per_session = json.loads(seconds_on_domain_per_session)
            '''

            # sort to websites
            websites = set()
            for line in parsed_raw:
                websites.add(line["goal_name"].split("/")[0])

            website_vs_raw = {w: [] for w in websites}
            for line in parsed_raw:
                website_vs_raw[line["goal_name"].split("/")[0]].append(line)

            website_vs_sec_on_domain = {w: [] for w in websites}
            for web in websites:
                for line in seconds_on_domain_per_session:
                    # print(line)
                    # print()
                    try:
                        if web in line["key"]:
                            website_vs_sec_on_domain[web].append(line)
                    except KeyError:
                        pass
                        # print(line)
            if w not in website_vs_sec_on_domain:
                continue
            sec_on_domain_per_for_w = website_vs_sec_on_domain[w]
            raw_for_w = website_vs_raw[w]

            # notuniquekeys = set([line["key2"] for line in sec_on_domain_per_for_w])

            # get the largest value on the same day
            largest = dict()
            pop_list = []
            for i, line in enumerate(sec_on_domain_per_for_w):
                try:
                    if largest[line["key2"]][1] > line["val"]:
                        pop_list.append(i)
                    else:
                        pop_list.append(largest[line["key2"]][0])
                        largest[line["key2"]] = (i, line["val"])
                except KeyError:
                    largest[line["key2"]] = (i, line["val"])
            # pop all
            pop_list = sorted(pop_list, reverse= True)
            for p in pop_list:
                sec_on_domain_per_for_w.pop(p)

            # test if unique
            # uniquekeys = [line["key2"] for line in sec_on_domain_per_for_w]

            '''
            if len(uniquekeys) > len(set(uniquekeys)):
                print("not unique!!")
            # check if poppsed too much
            if len(uniquekeys) < len(notuniquekeys):
                print("popped too much!!")
            '''
            #sort by timestamp

            raw_for_w = sorted(raw_for_w, key=get_time_stamp)

            sec_on_domain_per_for_w = sorted(sec_on_domain_per_for_w, key=get_time_stamp)


            timeonStack = []
            timeSinceInstallStack = []

            for line in sec_on_domain_per_for_w:
                if (line["timestamp"] - installtime[userid] < 0):
                    continue
                timeonStack.append(line["val"])
                timeSinceInstallStack.append(line["timestamp"] - installtime[userid])

            # print(timeSinceInstall)
            if (len(timeSinceInstallStack) >= 4):
                num_month = int(max(timeSinceInstallStack) // (2.628e+9))
                # print(max(timeSinceInstallStack))
                # print(timeon_months_list[num_month])
                # print(timeonStack)
                # timeon_months_list[num_month] =
                try:
                    timeon_months_list[num_month] += timeonStack
                    time_since_months_list[num_month] += timeSinceInstallStack
                    # print(timeon_months_list)
                except IndexError:
                    timeon_months_list[13] += timeonStack
                    time_since_months_list[13] += timeSinceInstallStack

        for month in range(len(timeon_months_list)):
            for m2 in range(month + 1, len(timeon_months_list)):
                for item in range(len(timeon_months_list[m2])):
                    if time_since_months_list[m2][item]  // (2.628e+9) <= month:
                        timeon_months_list[month] += [timeon_months_list[m2][item]]
                        time_since_months_list[month] += [time_since_months_list[m2][item]]
        with open(w + "timeon_months_list.pickel", 'wb') as f:
            pickle.dump(timeon_months_list, f, pickle.HIGHEST_PROTOCOL)

        with open(w + "time_since_months_list.pickel", 'wb') as f:
            pickle.dump(time_since_months_list, f, pickle.HIGHEST_PROTOCOL)

    for month in range(len(timeon_months_list)):
        xdata = np.array(time_since_months_list[month]) * 3.80517e-10
        ydata = np.log(np.array(timeon_months_list[month]) / 3600)
        popt, pcov = curve_fit(linear, xdata, ydata)
        plt.title(w + " " + str(month) + " months old users "+ "$R^2$=" + str(rsquare(xdata, ydata, popt, linear)))
        plt.plot(np.sort(xdata),
                 linear(np.sort(xdata),*popt), 'r',
                 label='fit: a=%5.3f, b=%5.3f' % tuple(popt))
        plt.scatter(xdata, ydata, c="g", alpha=0.5,
                    marker=r'$\clubsuit$')

        #plt.text(3, 8, )
        plt.xlabel("time since installed (months)")
        plt.ylabel("time on site(hrs)")
        plt.legend(loc=2)
        plt.show()
