import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel
results_to_uninstall_ungoal_goal = dict()
with open("website_to_user_to_website_average_time", 'rb') as f:
    website_to_user_to_website_average_time = pickle.load(f)

with open("domain_to_time_per_day", 'rb') as f:
    user_to_domain_to_time_per_day = pickle.load(f)
website_to_result= dict()
for website in website_to_user_to_website_average_time:

    for user in website_to_user_to_website_average_time[website]:
        if user in user_to_domain_to_time_per_day:
            if website in user_to_domain_to_time_per_day[user]:
                results_to_uninstall_ungoal_goal[user] = [user_to_domain_to_time_per_day[user][website] * 1.66667e-5] \
                                                         + [x * 1000 * 1.66667e-5 for x in website_to_user_to_website_average_time[website][user]]
    website_to_result[website] = results_to_uninstall_ungoal_goal
    result_list = np.asarray(list(results_to_uninstall_ungoal_goal.values()))
    data = result_list[..., 1]
    data[data == 0] = np.nan
    result_list[..., 1] = data
    median = np.nanmedian(result_list, axis=0)
    average = np.nanmean(result_list, axis=0)
    ttest = ttest_rel(np.transpose(result_list)[0],
                      np.transpose(result_list)[2])
    print(website)
    print(average)
    print(ttest)
