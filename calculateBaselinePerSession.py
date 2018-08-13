from dataUtil import *
import tldextract
from collections import Counter
import pickle
# http://localhost:5000/printcollection?collection=8916c882cdc10370b3f3d205_synced:baseline_time_on_domains
link = "http://localhost:5000/get_user_to_is_logging_enabled"
userIDs = set(parse_url_as_json(link))
domain_to_time_per_day = dict()

idx = 0

link = "http://localhost:5000/get_installs"
raw = parse_url_as_json(link)
user_to_install_version = dict()
for log in raw:
    try:
        user_to_install_version[log["user_id"]] = log["version"]
    except KeyError:
        print(log)

for user in userIDs:

    if idx % 100 == 0: print(str(idx) + '/' + str(len(userIDs)))
    idx += 1

    if user_to_install_version.get(user, "0.0.0") >= "1.0.231": continue

    domain_to_time_per_day[user] = Counter()
    link = "http://localhost:5000/printcollection?collection=" + user + "_synced:baseline_time_on_domains"
    raw = parse_url_as_json(link)
    for line in raw:
        domain = tldextract.extract(line["key"]).domain
        time = line['val']
        domain_to_time_per_day[user][domain] += time

with open("domain_to_time_per_day", "wb") as f:
    pickle.dump(domain_to_time_per_day, f)
