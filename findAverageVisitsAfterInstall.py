'''
 This script finds the average visits/time per day.


'''


# imports
import json
from urllib.request import urlopen


from dataUtil import parse_url_as_json, bisection, is_habitlab_on, get_time_stamp, calculate_goal_ungoal_time_for, \
    printProgressBar, is_not_to_keep, parse_goal_log_for_user, clean_session_log

link = "http://localhost:5000/get_user_to_all_install_times"
user_to_installtime = parse_url_as_json(link)
user_to_installtime = {k: min(user_to_installtime[k]) for k in user_to_installtime}

'''
with open(r"log_data\all_users_in_experiment_by_name") as lc:
    userIDs = set(json.load(lc))
'''
link = "http://localhost:5000/get_user_to_is_logging_enabled"
userIDs = set(parse_url_as_json(link))

# userIDs = [i for i in userIDs if userIDs[i]]
# userIDs = {'64b3c3f8d95b59de6b1dcdc8'}
we = ["facebook", "youtube", "reddit", "twitter", "gmail", "netflix", "amazon"]

result_string = ""
website_to_user_to_average_time = dict()

# test_data = []
# print("processing " + w)
idx = 0
initiallyDisabled = 0
noInstallTime = 0
w_not_in = 0
# traverse thu all users to obtain t/f average time spent on websites per day/ per session reduced after enabling the goals
for w in we:
    website_to_user_to_average_time[w] = dict()
printProgressBar(0, len(userIDs), prefix='Progress:', suffix='Complete', length=50)

for userid in userIDs:
    # if idx % 100 == 0: print(str(idx) + "/" + str(len(userIDs)))
    # os.system('cls')
    printProgressBar(idx, len(userIDs), prefix="Progress: ", suffix='Users Complete', length=50)

    idx += 1
    # num_month = 0

    if userid in user_to_installtime:
        install = user_to_installtime[userid]
    else:
        noInstallTime += 1
        if noInstallTime % 10 == 0:
            print(str(noInstallTime) + "cases that do not have install time. ")
        continue

    # filter users used HabitLab for under certain time
    UNDER_CERTAIN_TIME = 7 * 8.64e+7
    link = "http://localhost:5000/get_last_intervention_seen_and_time?userid=" + userid
    last_time_seen_intervention = parse_url_as_json(link)['time']
    if last_time_seen_intervention == None:
        continue

    if last_time_seen_intervention - install < UNDER_CERTAIN_TIME:
        continue
    parsed_raw = parse_goal_log_for_user(userid)

    # secs on a website per session
    # http://localhost:5000/printcollection?collection=683c1e28dcad53573b3f2c83_synced:seconds_on_domain_per_day
    link = "http://localhost:5000/printcollection?collection=" + userid + "_synced:seconds_on_domain_per_session"
    # print(link)
    # print("retrieving seconds_on_domain_per_day for userid = " + userid)

    f2 = urlopen(link).read()
    seconds_on_domain_per_session = json.loads(f2.decode('utf-8'))
    if seconds_on_domain_per_session == []:
        continue
    # f2.close()
    for i in range(len(seconds_on_domain_per_session)):
        if "timestamp" not in seconds_on_domain_per_session[i]:
            continue
        if "timestamp_local" not in seconds_on_domain_per_session[i]:
            seconds_on_domain_per_session[i]['timestamp_local'] = seconds_on_domain_per_session[i]['timestamp']
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

    # print(line)
    website_vs_raw = {x: [] for x in websites}
    for line in parsed_raw:
        website_vs_raw[line["goal_name"].split("/")[0]].append(line)

    website_vs_sec_on_domain = {x: [] for x in websites}
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

    for w in we:

        if w not in website_vs_sec_on_domain:
            continue

        visits_on_w_per_day = website_vs_sec_on_domain[w]
        raw_for_w = website_vs_raw[w]

        # notuniquekeys = set([line["key2"] for line in sec_on_domain_per_for_w])

        visits_on_w_per_day = clean_session_log(visits_on_w_per_day)

        # test if unique
        # uniquekeys = [line["key2"] for line in sec_on_domain_per_for_w]

        '''
        if len(uniquekeys) > len(set(uniquekeys)):
            print("not unique!!")
        # check if seconds_on_domain_per_sessionpoppsed too much
        if len(uniquekeys) < len(notuniquekeys):
            print("popped too much!!")
        '''
        # sort by timestamp

        raw_for_w = sorted(raw_for_w, key=get_time_stamp)

        visits_on_w_per_day = sorted(visits_on_w_per_day, key=get_time_stamp)

        # disabled_sec = 0
        # abled_sec = 0
        disabled_total_visit_time = 0
        abled_total_vistit_time = 0
        '''
            Calculate total time during different goal activations
        '''
        if visits_on_w_per_day == []:
            # if there is no visit to a website, then
            # do nothing.
            continue

        last_visit = visits_on_w_per_day[-1]["timestamp_local"]
        goal_total_time, ungoal_total_time, is_under_a_day = calculate_goal_ungoal_time_for(raw_for_w, last_visit,
                                                                                            user_to_installtime[userid])
        # if raw_for_w[0]["type"] == 'goal_disabled':
        #     initiallyDisabled += 1
        #     # (userid)
        #     # if initiallyDisabled % 10 == 0:
        #     #    print(str(initiallyDisabled) + " cases where the first goal is disabled.")
        # elif raw_for_w[0]["type"] == 'goal_enabled':
        #    print("goal enabled")

        '''
            Calculate total seconds on website when goals are set/ not set
        '''

        for line in visits_on_w_per_day:

            index_before = bisection([x["timestamp_local"] for x in raw_for_w], line["timestamp_local"])
            if is_not_to_keep(is_under_a_day, index_before):
                try:
                    if is_habitlab_on(line["timestamp_local"], raw_for_w):
                        # abled_sec +=
                        abled_total_vistit_time += line["val"]
                    else:
                        disabled_total_visit_time += line["val"]
                except TypeError:
                    print("type Error")
                    print(line)

        if goal_total_time != 0:
            abled_visits_vs_time = abled_total_vistit_time / (goal_total_time * 1.15741e-8)
        else:
            abled_visits_vs_time = 0

        if ungoal_total_time != 0:
            disabled_visits_vs_time = disabled_total_visit_time / (ungoal_total_time * 1.15741e-8)
        else:
            disabled_visits_vs_time = 0
            # test_data.append(
            #     {"userid": userid, "disabled_total_time": goal_total_time, "abled_total_time": ungoal_total_time,
            #      "disabled_num_visits": disabled_num_visits, "abled_num_visits": abled_num_visits,
            #      "disabled_visits_vs_time": disabled_visits_vs_time, "abled_visits_vs_time": abled_visits_vs_time})

        website_to_user_to_average_time[w][userid] = [disabled_visits_vs_time,
                                                      abled_visits_vs_time]

    '''
    dd = test_data
    diabled = [i['avg_disabled_sec'] for i in dd]
    abled = [i['avg_abled_sec'] for i in dd]
    result_string += (w + '\n')
    result_string += (str(np.average(diabled)) + '\n')
    result_string += (str(np.average(abled)) + '\n')
    result_string += (str(stats.ttest_rel(diabled, abled)) + '\n')
    '''

    # print(w)
    # print(np.average(diabled))
    # print(np.average(abled))
    # print(stats.ttest_rel(diabled, abled))
