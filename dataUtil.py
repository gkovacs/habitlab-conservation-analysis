import json
from urllib.request import urlopen
import tldextract
import numpy as np
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


def is_habitlab_on(timestamp, logs):
    '''
            given a timestamp, and a collection of the user goal_enabled logs, determine
            if the habit lab is on at that timestamp. Assuming that log has been
            sorted according to the timestamp.
    '''
    timestamp_list = [x["timestamp_local"] for x in logs]
    index = bisection(timestamp_list,
                      timestamp)  # [x["timestamp"] for x in log]the index of which the timestamp just falls after
    # print(str(index) + " " + str(timestamp_list[index]) + " " + str(timestamp))

    # for prehistoric time no one enables HabitLab
    if index == -1:
        return False

    if logs[index]["type"] == "goal_enabled":
        return True
    elif logs[index]["type"] == "goal_disabled":
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

    for i in range(len(parsed_raw)):
        if "goal_list" in parsed_raw[i]:
            parsed_raw[i]["prev_enabled_goals"] = []


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

def calculate_user_sec_on_goal_per_day(user):
    '''
    Calculates the median time per day spent on goal website for a user.
    :param user:
    :return:
    '''

    logs = parse_goal_log_for_user(user)
    link = "http://localhost:5000/printcollection?collection=" + user + "_synced:seconds_on_domain_per_day"
    session_log = parse_url_as_json(link)

    website_to_goal = dict()
    website_to_sessions = dict()
    for line in logs:
        website = line["goal_name"].split('/')[0]
        if website in website_to_goal:
            website_to_goal[website].append(line)
        else:
            website_to_goal[website] = [line]

    for website in website_to_goal:
        website_to_goal[website] = sorted(website_to_goal[website], key=lambda x: x["timestamp_local"])

    for line in session_log:
        website = tldextract.extract(line["key"]).domain
        if website in website_to_sessions:
            website_to_sessions[website].append(line)
        else:
            website_to_sessions[website] = [line]

    website_to_active_session = dict()
    for website in website_to_sessions:
        website_to_sessions[website] = clean_session_log(website_to_sessions[website])
        if website in website_to_goal:
            website_to_active_session[website] = [x for x in website_to_sessions[website]
                                                  if is_habitlab_on(x["timestamp"], website_to_goal[website])]

    website_to_median_time_spent = {x: np.nanmedian([y["timestamp"] for y in website_to_active_session[x]])
                                    for x in website_to_active_session}

    total = np.nansum(list(website_to_median_time_spent.values()))

    return total

ANDROID = "android"
BROWSER = "browser" # habitlab goal, i.e. facebook/spend_less_time or custom/spend_less_time_developers.slashdot.org
BROWSER_DOMAIN = "browser_domain"
SHARED = "shared"
PACKAGES = "packages"
SPEND_LESS_TIME_LENGTH = len("custom/spend_less_time_")
# Associate users with domain name which will function as our key.
# Top-level-domain-names that are not pertinent to the application.
TLDs = ['www', 'aaa', 'abb', 'abc', 'ac', 'aco', 'ad', 'ads', 'ae', 'aeg', 'af', 'afl', 'ag', 'ai', 'aig', 'al', 'am', 'anz', 'ao', 'aol', 'app', 'aq', 'ar', 'art', 'as', 'at', 'au', 'aw', 'aws', 'ax', 'axa', 'az', 'ba', 'bar', 'bb', 'bbc', 'bbt', 'bcg', 'bcn', 'bd', 'be', 'bet', 'bf', 'bg', 'bh', 'bi', 'bid', 'bio', 'biz', 'bj', 'bm', 'bms', 'bmw', 'bn', 'bnl', 'bo', 'bom', 'boo', 'bot', 'box', 'br', 'bs', 'bt', 'buy', 'bv', 'bw', 'by', 'bz', 'bzh', 'ca', 'cab', 'cal', 'cam', 'car', 'cat', 'cba', 'cbn', 'cbs', 'cc', 'cd', 'ceb', 'ceo', 'cf', 'cfa', 'cfd', 'cg', 'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'com', 'cr', 'crs', 'csc', 'cu', 'cv', 'cw', 'cx', 'cy', 'cz', 'dad', 'day', 'dds', 'de', 'dev', 'dhl', 'diy', 'dj', 'dk', 'dm', 'dnp', 'do', 'dog', 'dot', 'dtv', 'dvr', 'dz', 'eat', 'ec', 'eco', 'edu', 'ee', 'eg', 'er', 'es', 'esq', 'et', 'eu', 'eus', 'fan', 'fi', 'fit', 'fj', 'fk', 'fly', 'fm', 'fo', 'foo', 'fox', 'fr', 'frl', 'ftr', 'fun', 'fyi', 'ga', 'gal', 'gap', 'gb', 'gd', 'gdn', 'ge', 'gea', 'gf', 'gg', 'gh', 'gi', 'gl', 'gle', 'gm', 'gmo', 'gmx', 'gn', 'goo', 'gop', 'got', 'gov', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hbo', 'hiv', 'hk', 'hkt', 'hm', 'hn', 'hot', 'how', 'hr', 'ht', 'hu', 'ibm', 'ice', 'icu', 'id', 'ie', 'ifm', 'il', 'im', 'in', 'inc', 'ing', 'ink', 'int', 'io', 'iq', 'ir', 'is', 'ist', 'it', 'itv', 'jcb', 'jcp', 'je', 'jio', 'jlc', 'jll', 'jm', 'jmp', 'jnj', 'jo', 'jot', 'joy', 'jp', 'ke', 'kfh', 'kg', 'kh', 'ki', 'kia', 'kim', 'km', 'kn', 'kp', 'kpn', 'kr', 'krd', 'kw', 'ky', 'kz', 'la', 'lat', 'law', 'lb', 'lc', 'lds', 'li', 'lk', 'llc', 'lol', 'lpl', 'lr', 'ls', 'lt', 'ltd', 'lu', 'lv', 'ly', 'ma', 'man', 'map', 'mba', 'mc', 'md', 'me', 'med', 'men', 'mg', 'mh', 'mil', 'mit', 'mk', 'ml', 'mlb', 'mls', 'mm', 'mma', 'mn', 'mo', 'moe', 'moi', 'mom', 'mov', 'mp', 'mq', 'mr', 'ms', 'msd', 'mt', 'mtn', 'mtr', 'mu', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'nab', 'nba', 'nc', 'ne', 'nec', 'net', 'new', 'nf', 'nfl', 'ng', 'ngo', 'nhk', 'ni', 'nl', 'no', 'now', 'np', 'nr', 'nra', 'nrw', 'ntt', 'nu', 'nyc', 'nz', 'obi', 'off', 'om', 'one', 'ong', 'onl', 'ooo', 'org', 'ott', 'ovh', 'pa', 'pay', 'pe', 'pet', 'pf', 'pg', 'ph', 'phd', 'pid', 'pin', 'pk', 'pl', 'pm', 'pn', 'pnc', 'pr', 'pro', 'pru', 'ps', 'pt', 'pub', 'pw', 'pwc', 'py', 'qa', 'qvc', 're', 'red', 'ren', 'ril', 'rio', 'rip', 'ro', 'rs', 'ru', 'run', 'rw', 'rwe', 'sa', 'sap', 'sas', 'sb', 'sbi', 'sbs', 'sc', 'sca', 'scb', 'sd', 'se', 'ses', 'sew', 'sex', 'sfr', 'sg', 'sh', 'si', 'sj', 'sk', 'ski', 'sky', 'sl', 'sm', 'sn', 'so', 'soy', 'sr', 'srl', 'srt', 'st', 'stc', 'su', 'sv', 'sx', 'sy', 'sz', 'tab', 'tax', 'tc', 'tci', 'td', 'tdk', 'tel', 'tf', 'tg', 'th', 'thd', 'tj', 'tjx', 'tk', 'tl', 'tm', 'tn', 'to', 'top', 'tr', 'trv', 'tt', 'tui', 'tv', 'tvs', 'tw', 'tz', 'ua', 'ubs', 'ug', 'uk', 'uno', 'uol', 'ups', 'us', 'uy', 'uz', 'va', 'vc', 've', 'vet', 'vg', 'vi', 'vig', 'vin', 'vip', 'vn', 'vu', 'wed', 'wf', 'win', 'wme', 'wow', 'ws', 'wtc', 'wtf', 'xin', 'xxx', 'xyz', 'ye', 'you', 'yt', 'yun', 'za', 'zip', 'zm', 'zw']
def get_name(name, device):
    """
    @param name: goal name (package name for Android)
    @param device: "android" or "browser" or "browser_domain"
    @return name of goal with subdomains removed and goal annotation removed (i.e. spend_less_time)
    """
    if device == ANDROID  and name =="com.google.android.gm" or device == BROWSER and "gmail" in name:
        return "gmail"
    name = name.lower()
    if "custom" in name and device == BROWSER:
        # strip off the "custom/spend_less_time_"
        name = name[SPEND_LESS_TIME_LENGTH:]
    elif device == BROWSER:
        return name.split('/spend')[0]
    # Now we have to get juicy part of domain.
    subs = list(filter(lambda x: x != "android" and x != "google" and x != "apps" and x not in TLDs, name.split('.')))
    if device == ANDROID: 
        if len(subs) > 0:
            return subs[0]
        return name
    else:
        if len(subs) > 0:
            return subs[len(subs) - 1]    
        
def organize_stats(shared_goals, stats, device, counts, user_id):
    """
    Organizes that stats object into shared_goals for device.
    @param shared_goals: dictionary
    @param stats:  stats object returned from freq_stats
    @param device: ANDROID or BROWSER
    """
    for iso in stats:
        for freq in stats[iso]:
            for goal in stats[iso][freq]:
                name = get_name(goal, device)
                if name not in shared_goals:
                    shared_goals[name] = {ANDROID: {PACKAGES:[]} , BROWSER: {PACKAGES:[]} }
                if goal not in shared_goals[name][device][PACKAGES]:
                    shared_goals[name][device][PACKAGES].append(goal)
                    shared_goals[name][device][goal] = {}
                if iso not in shared_goals[name][device][goal]:
                    shared_goals[name][device][goal][iso] = freq
                    if device == BROWSER:
                        counts[freq] += 1
                # Before I submitted the update, some apps under the same name wouldn't have the same freq setting.
                elif shared_goals[name][device][goal][iso] != freq:
                    shared_goals[name][device][goal][iso] = "both"
                    counts["both"] += 1
                if len(shared_goals[name][ANDROID][PACKAGES]) > 0 and len(shared_goals[name][BROWSER][PACKAGES]) > 0:
                    shared_goals[SHARED].add(name)


