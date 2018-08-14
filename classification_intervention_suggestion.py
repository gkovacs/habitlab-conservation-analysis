#import tensorflow as tf
#import matplotlib.pyplot as plt
import numpy as np
import pickle
from sklearn import datasets
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import statsmodels.api as sm
import pandas as pd
import seaborn as sb

enc = OneHotEncoder(handle_unknown='ignore')
colums = ["Productivity", "day", "day_of_the_week", "time_of_the_day"]#'timestamp', "day_of_the_week", "time_of_the_day",
          #"timestamp_local"]
with open("x_input", 'rb') as f:
    x_input = pickle.load(f)
all = x_input.copy()
y_output = [[i.pop(0)] for i in x_input]
#print
x_input = np.array(x_input)
y_output = np.array(y_output)

label = LabelEncoder()
x_input[:, 2] = label.fit_transform(x_input[:, 2])
x_input[:, 3] = label.fit_transform(x_input[:, 3])
ohe = OneHotEncoder(categorical_features = [2, 3], sparse=False)
x_input = ohe.fit_transform(x_input)
x_input = pd.DataFrame(data = x_input, index = range(len(x_input)))
y_output = pd.DataFrame(data = y_output, index = range(len(y_output)))
sb.heatmap(x_input.corr())

logreg = LogisticRegression()
rfe = RFE(logreg, 5)
rfe = rfe.fit(x_input, y_output )
print(rfe.support_)
print(rfe.ranking_)

logit_model=sm.Logit(y_output, x_input)
result=logit_model.fit()
print(result.summary())