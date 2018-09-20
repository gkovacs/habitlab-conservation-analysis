# process data
#from collections import Counter

#import matplotlib.pyplot as plt
from dataUtil import *
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
import random
#from urllib.parse import urlparse
import pickle
import tensorflow as tf
from tensorflow import keras
from sklearn.utils import class_weight
from tensorflow.keras import backend as K

#from data_visulization_util import chisquare, print_acceptance_rate, linear, plot_dictionary, time_period, \
#    select_timestamp
# define example
def sensitivity(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    return true_positives / (possible_positives + K.epsilon())

def specificity(y_true, y_pred):
    true_negatives = K.sum(K.round(K.clip((1-y_true) * (1-y_pred), 0, 1)))
    possible_negatives = K.sum(K.round(K.clip(1-y_true, 0, 1)))
    return true_negatives / (possible_negatives + K.epsilon())

def one_hot_encode_data(data):
    values = np.array(data)
    print(values)
    # integer encode
    label_encoder = LabelEncoder()
    integer_encoded = label_encoder.fit_transform(values)
    print(integer_encoded)
    # binary encode
    onehot_encoder = OneHotEncoder(sparse=False)
    integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
    onehot_encoded = onehot_encoder.fit_transform(integer_encoded)
    print(onehot_encoded)
    # invert first example
    #inverted = label_encoder.inverse_transform([np.argmax(onehot_encoded[0, :])])
    return onehot_encoded

class DataBatcher:
    def __init__(self, x_data, y_data, k):
        # training data
        self.data_dimention = len(x_data[0])

        self.test_x = x_data[:len(x_data) // k]
        self.test_y = y_data[:len(y_data) // k]
        self.training_x = x_data[len(x_data)//k:]
        self.training_y = y_data[len(y_data)//k:]

        self.data_unbatched_training = list(range(len(self.training_x)))
        self.data_unbatched_test = list(range(len(self.test_x)))
    def next_batch_training(self, batch_size):

        x = np.array([])
        y = np.array([])
        for i in range(batch_size):
            if self.data_unbatched_training == []:
                self.data_unbatched_training = list(range(len(self.training_x)))

            idx = random.choice(self.data_unbatched_training)
            self.data_unbatched_training.remove(idx)
            x = np.append(x, (np.array([int(float(xi)) for xi in self.training_x[idx]])))
            y = np.append(y, self.training_y[idx])

        return {'x': np.reshape(x, [batch_size, self.data_dimention]),
                'y': y}

    def next_batch_testing(self, batch_size):
        x = np.array([])
        y = np.array([])
        for i in range(batch_size):
            if self.data_unbatched_test == []:
                self.data_unbatched_test = list(range(len(self.test_x)))

            idx = random.choice(self.data_unbatched_test)
            self.data_unbatched_test.remove(idx)
            x = np.append([x], (np.array([int(float(xi)) for xi in self.test_x[idx]])))
            y = np.append([y], self.test_y[idx])

        return {'x': np.reshape(x, [batch_size, self.data_dimention]),
                'y': y}

with open("user_took_action.json", 'rb') as lc:
    raw = json.load(lc)

with open("domain_to_productivity.json", 'rb') as lc:
    d2productivity = json.load(lc)

with open("interventionDifficulty", 'rb') as lc:
    intervention_to_difficulty = json.load(lc)

user_to_installtime = parse_url_as_json("http://localhost:5000/get_user_to_all_install_times")
user_to_installtime = {k: min(user_to_installtime[k]) for k in user_to_installtime}

with open("log_data\\user_to_difficulty", 'rb') as lc:
    user_to_difficulty = json.load(lc)

# seperate -- users to suggestions.
# then find the last time see an intervention suggestion.
# then find the last time see an intervention. (?)
# last session spent. (?)

user_to_suggestions = dict()
for line in raw:
    user = line["userid"]
    if user not in user_to_suggestions:
        user_to_suggestions[user] = [line]
    else:
        #print(user)
        user_to_suggestions[user].append(line)

# historical time spent on websites
with open("domain_to_time_per_day", "rb") as f:
    user_to_domain_to_time_per_day = pickle.load(f)

day_to_cate = set()
website_to_cate = set()
intervention_to_cate = set()
period_of_day_to_cate = set()
for user in user_to_suggestions:
    user_to_suggestions[user] = sorted(user_to_suggestions[user], key = lambda x: x["timestamp_local"])

    timestamps = [x["timestamp_local"] for x in user_to_suggestions[user]]
    actions = [x["accepted"] for x in user_to_suggestions[user]]
    last_action = np.roll(actions, 1)
    last_action[0] = 0

    timedifference = timestamps - np.roll(timestamps, 1)
    timedifference[0] = -1
    is_start = [0] * len(timestamps)
    is_start[0] = 1
    diff = user_to_difficulty.get(user, "nothing")
    for i, log in enumerate(user_to_suggestions[user]):
        #log["website"] = log["intervention"].split("/")[0]
        log["unique_intervention"] = log["intervention"].split("/")[1]


        log["is_start"] = is_start[i]
        log["last_time_seen"] = timedifference[i]
        log["last_action"] = last_action[i]
        log["day"] = log["localtime"].split(" ")[0]
        log["onboard_diff"] = diff
        if user in user_to_installtime:
            log["since_install"] = log["timestamp_local"] - user_to_installtime[user]
            log["has_install"] = 1
        else:
            log["since_install"] = -1
            log["has_install"] = 0
        if user in user_to_domain_to_time_per_day:
            if log["intervention"].split("/")[0] in user_to_domain_to_time_per_day:
                log["has_baseline"] = 1
                log["baseline"] = user_to_domain_to_time_per_day[user][log["intervention"].split("/")[0]]
            else:
                log["has_baseline"] = 0
                log["baseline"] = -1
        else:
            log["has_baseline"] = 0
            log["baseline"] = -1

        time = log["localtime"].split(" ")[4].split(":")[0]
        if 0 < int(time) <= 6:
            log["period_of_day"] = "midnight"
        elif 6 < int(time) <= 12:
            log["period_of_day"] = "morning"
        elif 12 < int(time) <= 18:
            log["period_of_day"] = "afternoon"
        else:
            log["period_of_day"] = "evening"

        day_to_cate.add(log["day"])

        #website_to_cate.add(log["website"])
        intervention_to_cate.add(log["unique_intervention"])
        period_of_day_to_cate.add(log["period_of_day"])

day_to_cate = list(day_to_cate)
#website_to_cate = list(website_to_cate)
#intervention_to_cate = list(intervention_to_cate)
period_of_day_to_cate = list(period_of_day_to_cate)
day_onehot = tf.one_hot(list(range(len(day_to_cate))), len(day_to_cate))
period_of_day_onehot = tf.one_hot(list(range(len(period_of_day_to_cate))), len(period_of_day_to_cate))
difficulty_levels = ("nothing", "easy", "medium", "hard")
diff_onehot = tf.one_hot(list(range(len(difficulty_levels))), len(difficulty_levels))
# convert back to data
x_data_str = []
y_data = []
data = []

for line in user_to_suggestions.values():
    for x in line:
        data.append(x)


last_time_seen_avg = np.mean([x["last_time_seen"] for x in data if x["last_time_seen"] != -1])
since_install_avg = np.mean([x["since_install"] for x in data if x["since_install"] != -1])
baseline_avg = np.mean([x["baseline"] for x in data if x["baseline"] != -1])

x_data_str = np.array([])
for x in data:
    if x["last_time_seen"] == -1:
        x["last_time_seen"] = last_time_seen_avg

    if x["since_install"] == -1:
        x["since_install"] = since_install_avg

    if x["baseline"] == -1:
        x["baseline"] = since_install_avg

    x_data_str = np.append(x_data_str,
              np.array([x["day"], x['last_time_seen'], x['period_of_day'], x["onboard_diff"],
                         x['unique_intervention'],
                        x["since_install"], x["baseline"], x["has_baseline"],
                        x["is_start"], x['last_action']]))
x_data_str = np.reshape(x_data_str, [-1, 10])
one_hot_data = one_hot_encode_data(x_data_str[..., 0])
x_data_str = np.append(x_data_str, one_hot_data, axis = 1)
one_hot_data = one_hot_encode_data(x_data_str[..., 2])
x_data_str = np.append(x_data_str, one_hot_data, axis = 1)
one_hot_data = one_hot_encode_data(x_data_str[..., 3])
x_data_str = np.append(x_data_str, one_hot_data, axis = 1)
one_hot_data = one_hot_encode_data(x_data_str[..., 4])

x_data_str = np.append(x_data_str, one_hot_data, axis = 1)
mask = np.ones(len(x_data_str[0]), dtype=bool)
mask[[0,2, 3, 4]] = False
x_data = x_data_str[...,mask]
for line in data:
    if line["accepted"] == 'true':
        y_data.append(1)
    else:
        y_data.append(0)
#x_data[..., 1] = (x_data[..., 1] - np.mean(x_data[..., 1]))/ np.var(x_data)
#x_data[..., 2] = (x_data[..., 2] - np.mean(x_data[..., 2]))/ np.var(x_data)

# dump csv data


# print(user_to_suggestions)

# y_data =

# train

learning_rate = 0.1
batch_size = 128
n_epochs = 25
for i in range(len(x_data)):
    x_data[i] = np.array(x_data[i], dtype='f')
x_data = np.array(x_data)
y_data = np.array([float(i) for i in y_data])


#data_batcher = DataBatcher(x_data, y_data, 10)


model = keras.Sequential([
    keras.layers.Flatten(),
    keras.layers.Dense(80, activation=tf.nn.relu),
    keras.layers.Dense(60, activation=tf.nn.relu),
#    keras.layers.Dense(40, activation=tf.nn.relu),
#    keras.layers.Dense(20, activation=tf.nn.relu),
    tf.keras.layers.Dropout(0.5),
    keras.layers.Dense(1, activation=tf.nn.softmax)
])
model.compile(
    loss='binary_crossentropy',
    optimizer=tf.train.AdamOptimizer(),
    metrics=[sensitivity, specificity]
)
'''
model.compile(optimizer=tf.train.AdamOptimizer(),
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])
'''

#data = data_batcher.next_batch_training(len(x_data) // 10 *9)
class_weights = class_weight.compute_class_weight('balanced',
                                                 np.unique(y_data),
                                              y_data)

model.fit(x_data[:len(y_data)//10 * 9], y_data[:len(y_data)//10 * 9], epochs=10, class_weight = class_weights)
#test_data = data_batcher.next_batch_testing(len(x_data) // 10)
test_loss, test_acc = model.evaluate(x_data[len(y_data)//10 * 9:], y_data[len(y_data)//10 * 9:])
print(test_acc)
'''
X = tf.placeholder(tf.float32, [batch_size, len(x_data[0])])
Y = tf.placeholder(tf.float32, [batch_size, 2])
w = tf.Variable(tf.random_normal(shape=[len(x_data[0]), 2], stddev=0.01), name="weights")
b = tf.Variable(tf.zeros([1, 2]), name="bias")
logits = tf.matmul(X, w) + b
entropy = tf.nn.softmax_cross_entropy_with_logits(labels = Y, logits = logits)
loss = tf.reduce_mean(entropy) # computes the mean over examples in the batch
optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate).minimize(loss)
init = tf.global_variables_initializer()



with tf.Session() as sess:
    sess.run(init)
    n_batches = int(len(x_data)/batch_size)
    for i in range(n_epochs): # train the model n_epochs times
        for _ in range(n_batches):
            batch = data_batcher.next_batch_training(batch_size)
            X_batch, Y_batch = batch["x"], batch['y']

            sess.run([optimizer, loss], feed_dict={X: X_batch, Y:Y_batch})
        # test the model
        n = int(len(data_batcher.test_x)/batch_size)
        total_correct_preds = 0
        for i in range(n):
            batch = data_batcher.next_batch_testing(batch_size)
            X_batch, Y_batch = batch["x"], batch['y']
            loss_batch, logits_batch = sess.run([loss, logits],
            feed_dict={X: X_batch, Y:Y_batch})
            preds = tf.nn.softmax(logits_batch)
            correct_preds = tf.equal(tf.argmax(preds, 1), tf.argmax(Y_batch, 1))
            accuracy = tf.reduce_sum(tf.cast(correct_preds, tf.float32)) # similar to numpy.count_nonzero(boolarray) :(
            total_correct_preds += sess.run(accuracy)
            #print(logits_batch)
        print("Accuracy {0}".format(total_correct_preds/len(data_batcher.test_x)))

'''

# evaluate
