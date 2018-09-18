import json
from collections import Counter
from data_visulization_util import *
with open("log_data\\effectiveness.json", "r") as f:
    effectiveness = json.load(f)
intervention_to_effectiveness = Counter()
for line in effectiveness:
    for intervention in line['intervention_info_list']:
        intervention_to_effectiveness[intervention[0]] += intervention[2]

with open("log_data\\intervention_to_attrition_rate", "r") as f:
    intervention_to_attrition_rate_colum = json.load(f)
intervention_to_attrition_rate = {x.replace(":", "/"):intervention_to_attrition_rate_colum[x] for x in
                                  intervention_to_attrition_rate_colum}

with open("acc_rate.json", "r") as f:
    acc_rate = json.load(f)

intervention_to_utility = Counter()

for intervention in intervention_to_attrition_rate:
    if (intervention in intervention_to_attrition_rate and
            intervention in acc_rate):
        try:
            intervention_to_utility[intervention] = acc_rate.get(
                intervention) / \
                                                    intervention_to_attrition_rate.get(intervention)
        except ZeroDivisionError:
            intervention_to_utility[intervention] = -1
        except TypeError:
            print(intervention_to_effectiveness.get(intervention))
            print(acc_rate.get(intervention))
            print(intervention_to_attrition_rate.get(intervention))

interventions_of_concern = dict()
for intervention in intervention_to_utility:
    if intervention.split('_')[0] != "generated":
        interventions_of_concern[intervention] = intervention_to_utility[intervention]
    else:
        new_intervention = "generated/" + intervention.split('/')[1]
        if new_intervention not in interventions_of_concern:
            interventions_of_concern["generated/" + intervention.split('/')[1]] = intervention_to_utility[intervention]
        else:
            interventions_of_concern["generated/" + intervention.split('/')[1]] += intervention_to_utility[intervention]
website_to_intervention = dict()
for line in interventions_of_concern:
    website = line.split("/")[0]
    website_to_intervention[website] = dict()
for line in interventions_of_concern:
    website = line.split("/")[0]
    website_to_intervention[website][line] = interventions_of_concern[line]

for website in website_to_intervention:
    sorted_keys = sorted(website_to_intervention[website].keys())

    plt.figure()
    plt.barh(range(len(website_to_intervention[website])),
             list([website_to_intervention[website][x] for x in sorted_keys]), align='center')
    plt.yticks(range(len(website_to_intervention[website])), sorted_keys)

for website in website_to_intervention:
    website_to_intervention[website] = sorted(website_to_intervention[website].items(), key = lambda x: x[1])

for website in website_to_intervention:
    with open("websites_to_utility\\" + website + '.json', 'w') as f:
        json.dump(dict(website_to_intervention[website]), f)

