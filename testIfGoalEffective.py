# imports
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
import json
import pickle
from urllib.request import urlopen


# helper functions
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
        jm = (ju + jl) >> 1  # compute a midpoint with a bit shift
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

with open(r"log_data\all_users_in_experiment_by_name") as lc:
    userIDs = set(json.load(lc))

    success = 0
    fail = 0

we = ["facebook", "reddit", "twitter", "youtube", "gmail"]

result_string = ""
for w in we:
    test_data = []
    print("processing " + w)
    # traverse thu all users to obtain t/f average time spent on websites per day/ per session reduced after enabling the goals

    idx = 0
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
        #f.close()
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
        link = "http://localhost:5000/printcollection?collection=" + userid + "_synced:visits_to_domain_per_day"
        # print(link)
        # print("retrieving seconds_on_domain_per_day for userid = " + userid)

        f2 = urlopen(link).read()
        seconds_on_domain_per_session = json.loads(f2.decode('utf-8'))
        #f2.close()


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

        disabled_sec = 0
        abled_sec = 0
        disabled_num_visits = 0
        abled_num_visits = 0

        for line in sec_on_domain_per_for_w:
            if if_habitlab_on(line["timestamp"], raw_for_w):
                abled_sec += line["val"]
                abled_num_visits += 1
            else:
                disabled_sec += line["val"]
                disabled_num_visits += 1

            if disabled_num_visits == 0 or abled_num_visits == 0:
                continue
            else:
                avg_disabled_sec = disabled_sec / disabled_num_visits
                avg_abled_sec = abled_sec / abled_num_visits
                test_data.append({"userid": userid, "disabled_sec": disabled_sec, "abled_sec": abled_sec,
                                  "disabled_num_visits": disabled_num_visits, "abled_num_visits": abled_num_visits,
                                  "avg_disabled_sec": avg_disabled_sec, "avg_abled_sec": avg_abled_sec})

                # print("userid = " + userid)
                # print(disabled_sec)
                # print(abled_sec)
                # print(disabled_num_visits)
                # print(abled_num_visits)
                # print(disabled_sec / disabled_num_visits)
                # print(abled_sec / abled_num_visits)

            # if (avg_abled_sec < avg_disabled_sec):
            #     success += 1
            # else:
            #     fail += 1

    # print(success)
    # print(fail)
    dd = test_data
    diabled = [i['avg_disabled_sec'] for i in dd]
    abled = [i['avg_abled_sec'] for i in dd]
    result_string += (w + '\n')
    result_string += (str(np.average(diabled)) + '\n')
    result_string += (str(np.average(abled)) + '\n')
    result_string += (str(stats.ttest_rel(diabled, abled)) + '\n')
    # print(w)
    # print(np.average(diabled))
    # print(np.average(abled))
    # print(stats.ttest_rel(diabled, abled))

print(result_string)