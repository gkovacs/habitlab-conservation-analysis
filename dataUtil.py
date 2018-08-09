import json
from urllib.request import urlopen

def parse_url_as_json(link):
    f = urlopen(link).read()
    return json.loads(f.decode('utf-8'))


def bisection(array, value):
    '''Given an ``array`` , and given a ``value`` , returns an index j such that ``value`` is between array[j]
        and array[j+1]. ``array`` must be monotonic increasing. j=-1 or j=len(array) is returned
        to indicate that ``value`` is out of range below and above respectively.'''
    n = len(array)
    if (value < array[0]):
        return -1
    elif (value > array[n - 1]):
        return n - 1
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


def is_habitlab_on(timestamp, log):
    '''
            given a timestamp, and a log of the user goal_enabled log, determine
            if the habit lab is on at that timestamp. Assuming that log has been
            sorted according to the timestamp.
    '''
    timestamp_list = [x["timestamp_local"] for x in log]
    index = bisection(timestamp_list,
                      timestamp)  # [x["timestamp"] for x in log]the index of which the timestamp just falls after
    # print(str(index) + " " + str(timestamp_list[index]) + " " + str(timestamp))

    # for prehistoric time no one enables HabitLab
    if index == -1:
        return False

    if log[index]["type"] == "goal_enabled":
        return True
    elif log[index]["type"] == "goal_disabled":
        return False

    return


def get_time_stamp(item):
    return item["timestamp_local"]


def calculate_goal_ungoal_time_for(log, last_visit, earliest_install):
    """
    Calculates the total amount of time a user's goal/ungoal time. If the time gap
    between goal switch is under a day, discard it, and record this information in
    is_under_a_day. And return this information along with the total time.

    :param earliest_install:
    :param log:

    :param last_visit: the last time this user visits a particular cite.
    :return:
    """
    ONEDAY = 8.64e+7  # one day in ms.
    is_under_a_day = []
    # timestamp_list = [x["timestamp"] for x in log]
    is_goal_on = False
    goal_time = 0
    ungoal_time = 0

    """
    
    
    """
    previous_time = earliest_install
    for line in log:

        time_gap = line["timestamp_local"] - previous_time
        if line["type"] == "goal_enabled" and not is_goal_on:
            if time_gap > ONEDAY:
                ungoal_time += time_gap
                is_under_a_day.append(False)
            else:
                is_under_a_day.append(True)
            is_goal_on = not is_goal_on
        elif line["type"] == "goal_disabled" and is_goal_on:
            if time_gap > ONEDAY:
                goal_time += time_gap
                is_under_a_day.append(False)
            else:
                is_under_a_day.append(True)
            is_goal_on = not is_goal_on

        # does not switch if the goal is not switched.....
        elif line["type"] == "goal_disabled" and not is_goal_on:
            if time_gap > ONEDAY:
                goal_time += time_gap
                is_under_a_day.append(False)
            else:
                is_under_a_day.append(True)
        elif line["type"] == "goal_enabled" and is_goal_on:
            if time_gap > ONEDAY:
                goal_time += time_gap
                is_under_a_day.append(False)
            else:
                is_under_a_day.append(True)

        previous_time = line['timestamp_local']

    '''
        Calculate the last part of the time after the last goal switch.
    '''
    last_time_gap = last_visit - log[-1]["timestamp_local"]
    if log[-1]["type"] == "goal_enabled":
        if last_visit > ONEDAY:
            goal_time += last_time_gap
            is_under_a_day.append(False)
        else:
            is_under_a_day.append(True)
    elif log[-1]["type"] == "goal_disabled":
        if last_visit > ONEDAY:
            ungoal_time += last_time_gap
            is_under_a_day.append(False)
        else:
            is_under_a_day.append(True)

    return goal_time, ungoal_time, is_under_a_day


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def is_not_to_keep(is_under_a_day, index):
    """
    Return if we should keep this based on if the duration is less than a day.

    :param is_under_a_day:
    :param index:
    :return: to keep or not
    """
    index += 1

    return not is_under_a_day[index]


def parse_goal_log_for_user(userid, is_breaking_goal_list = True):
    '''
    Parse goal log for user with userid.
    This function breaks goal lists into goals,
    clean the log that does not have goal names
    or does not have local timestamp.
    If a log does not have local timestamp then
    it is replaced by timestamp.
    :param userid:
    :return: goal log
    '''
    # user log
    # http://localhost:5000/printcollection?collection=e98febf6f84d010a469e9d0f_logs:goals
    link = "http://localhost:5000/printcollection?collection=" + userid + "_logs:goals"
    # print(link)
    # print("retrieving log for userid = " + userid)
    f = urlopen(link).read()
    parsed_raw = json.loads(f.decode('utf-8'))
    # f.close()
    '''
        raw = ""
        with open("data.txt",encoding='utf-8', mode = 'r') as f:
            raw = f.read()
        parsed_raw = json.loads(raw)
        '''


    if is_breaking_goal_list:
        # parse goal_list into seperate goals.
        dummy_logs = parsed_raw.copy()
        for index in range(len(parsed_raw))[::-1]:
            line = parsed_raw[index]

            # parse goal_lists into goals and put them back to the log
            if "goal_list" in line:
                new_log_entries = []
                goals = line["goal_list"]
                type = line['type']
                for g in goals:
                    new_log_entry = line.copy()
                    new_log_entry["goal_name"] = g
                    if type == "goals_enabled":
                        new_log_entry['type'] = "goal_enabled"
                    else:
                        new_log_entry['type'] = 'goal_disabled'
                    del new_log_entry["goal_list"]
                    new_log_entries.append(new_log_entry)
                dummy_logs.pop(index)
                dummy_logs += new_log_entries
        parsed_raw = dummy_logs.copy()
    # some logs don't have goal_names
    parsed_raw = [i for i in parsed_raw if ("goal_name" in i or "goal_list" in i)]
    for i in range(len(parsed_raw)):
        if "timestamp_local" not in parsed_raw[i]:
            parsed_raw[i]['timestamp_local'] = parsed_raw[i]['timestamp']
    return parsed_raw


def clean_session_log(visits_on_w_per_day):
    # get the largest value on the same days with the same 'key' and 'key2'
    largest = dict()
    pop_list = []
    for i, line in enumerate(visits_on_w_per_day):
        try:
            if largest[line["key2"]][1] > line["val"]:
                pop_list.append(i)
            else:
                pop_list.append(largest[line["key2"]][0])
                largest[line["key2"]] = (i, line["val"])
        except KeyError:
            largest[line["key2"]] = (i, line["val"])
    # pop all
    pop_list = sorted(pop_list, reverse=True)
    for p in pop_list:
        visits_on_w_per_day.pop(p)

    return visits_on_w_per_day