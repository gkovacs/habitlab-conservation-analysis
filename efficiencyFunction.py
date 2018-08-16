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
    if intervention.split('/')[0] in ["facebook", "amazon", "youtube", "twitter", "netflix", "reddit", "gmail"]:
        interventions_of_concern[intervention] = intervention_to_utility[intervention]
sorted_keys = sorted(interventions_of_concern.keys())
plt.barh(range(len(interventions_of_concern)), list([interventions_of_concern[x] for x in sorted_keys]), align='center')
plt.yticks(range(len(interventions_of_concern)), sorted_keys)

plt.show()