import numpy as np
from matplotlib import pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit


def chisquare(dictionary):
    contigency_matrix = [[],[]]

    for line in dictionary:
        acc = 0
        rej = 0
        #print(line)
        for item in dictionary[line]:
            if item["action"] == "accepted":
                acc += 1
            else:
                rej += 1

        contigency_matrix[0].append(acc)
        contigency_matrix[1].append(rej)
    print(contigency_matrix)
    return stats.chi2_contingency(contigency_matrix)


def print_acceptance_rate(dictionary):
    for line in dictionary:
        acc_int = 0
        for item in dictionary[line]:
            if item['action'] == 'accepted': acc_int += 1
        print(line)
        print(acc_int / len(dictionary[line]))


def bin_confidence(p, n):
    print([p, n])
    return 1.96 * np.sqrt(p*(1- p)/n)


def linear(x, a, b):
    return a + np.multiply(x,b)


def plot_dictionary(dictionary, isRegression = False, func = None):
    acc_rate = dict()
    p = []
    n = []
    for line in sorted(dictionary.keys()):
        acc_int = 0
        for item in dictionary[line]:
            if item['action'] == 'accepted': acc_int += 1
        acc_rate[line] = (acc_int / len(dictionary[line]))
        p.append(acc_rate[line])
        n.append(len(dictionary[line]))
    p = np.array(p)
    n = np.array(n)
    plt.figure()
    plt.barh(range(len(acc_rate)), list(acc_rate.values()), align='center', xerr=bin_confidence(p, n))
    plt.yticks(range(len(acc_rate)), list(acc_rate.keys()))
    plt.xlabel("acceptance rate")
    plt.title("intervention suggestion difficulty to acceptance rate")
    plt.show()

    if isRegression and func:
        dellist = []
        for i in range(len(p))[::-1]:
            if p[i] == 0:
                dellist.append(i)
        ydata = np.log(p)
        xdata = np.array(sorted(dictionary.keys()))
        err =  np.log(bin_confidence(p, n))



        ydata = np.delete(ydata, dellist)
        xdata = np.delete(xdata, dellist)
        err = np.delete(err, dellist)

        params, cov = curve_fit(func, xdata, ydata, sigma = err)
        residuals = ydata - func(xdata, float(params[0]), float(params[1]))
        ss_red = np.sum(residuals ** 2)
        ss_tot = np.sum((ydata - np.mean(ydata)) ** 2)
        r_sq = 1 - (ss_red / ss_tot)
        plt.figure()
        plt.title("log regression")
        plt.ylabel("log(acceptance rate)")
        plt.errorbar(xdata, ydata, err)
        plt.plot(xdata, func(xdata, params[0], params[1]), 'r-', label='fit: a=%5.3f, b=%5.3f' % tuple(params))
        print('R^2 = %1.3f' % r_sq)
    return acc_rate


def time_period(hour):
    if 0 <= int(hour) < 6:
        return 'midnight'
    if 6 <= int(hour) <= 12:
        return 'morning'
    if 12 < int(hour) <= 18:
        return 'afternoon'
    if 18 < int(hour) < 24:
        return 'evening'


def select_timestamp(line):
    return line["timestamp"]