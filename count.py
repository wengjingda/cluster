# coding=utf-8

import Inverted_index
import tool
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report
from sklearn import tree
from pandas import DataFrame
import jieba
import remove_duplicate
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn import preprocessing
import math

__author__ = 'david'


class FeatureCluster:
    def __init__(self, feature_cut):
        self.feature_cut_array = []
        self.append_new_feature_cut(feature_cut)

    def append_new_feature_cut(self, feature_cut):
        self.feature_cut_array.append(feature_cut)

    def __str__(self):
        return "@@".join(["".join(y) for y in self.feature_cut_array])


def calculate_integrity(dictionary, word):
    word_freq = dictionary.word_freq_dic[dictionary.word_index_dic[word]]
    f_word_freq = dictionary.word_freq_dic.get(dictionary.word_index_dic.get(word[:-1], ""), 1)
    return float(word_freq) / f_word_freq


def calculate_stability(dictionary, word):
    word_freq = dictionary.word_freq_dic[dictionary.word_index_dic[word]]
    f_word_freq = dictionary.word_freq_dic.get(dictionary.word_index_dic.get(word[:-1], ""), 1)
    l_word_freq = dictionary.word_freq_dic.get(dictionary.word_index_dic.get(word[1:], ""), 1)
    return float(word_freq) / (f_word_freq + l_word_freq - word_freq + 1)


def calculate_independence_by_freq(dictionary, word):
    set_i, dict_i = dictionary.transform_term_info(word)
    f_word_set = set([])
    l_word_set = set([])
    for doc_id in set_i:
        for location_id in dict_i[doc_id].location_ids:
            if location_id > 0:
                f_word_set.add(dictionary.doc_dic[doc_id].words[location_id - 1])
            if location_id < len(dictionary.doc_dic[doc_id].words) - 1:
                l_word_set.add(dictionary.doc_dic[doc_id].words[location_id + 1])
    return [float(len(f_word_set)) / (dictionary.word_freq_dic[dictionary.word_index_dic[word]] + 1),
            float(len(l_word_set)) / (dictionary.word_freq_dic[dictionary.word_index_dic[word]] + 1)]


def calculate_independence(dictionary, word):
    set_i, dict_i = dictionary.transform_term_info(word)
    f_word_set = set([])
    l_word_set = set([])
    for doc_id in set_i:
        for location_id in dict_i[doc_id].location_ids:
            if location_id > 0:
                f_word_set.add(dictionary.doc_dic[doc_id].words[location_id - 1])
            if location_id < len(dictionary.doc_dic[doc_id].words) - 1:
                l_word_set.add(dictionary.doc_dic[doc_id].words[location_id + 1])
    return [1 - float(1) / (len(f_word_set) + 1), 1 - float(1) / (1 + len(l_word_set))]


def get_co_name():
    i_dic = Inverted_index.InvertDic()
    i_dic.init_all_dic()
    candidate_list = i_dic.word_index_dic.keys()
    limit_dic = {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}
    ids_dic = {}
    # result_dic = {}
    tool.write_file("./dict/word_co.txt", [], "w")
    for k in range(10):
        result_dic = {}
        for i in range(len(candidate_list)):
            for j in range(len(candidate_list)):
                if i == j:
                    continue
                if i_dic.add_term_bound(candidate_list[i], candidate_list[j]):
                    ids, locations = i_dic.get_co_occurrence_info(candidate_list[i], candidate_list[j])
                    if len(ids) > limit_dic.get(len(candidate_list[i]), 2):
                        i_dic.add_new_term(candidate_list[i], candidate_list[j])
                        new_word = candidate_list[i] + i_dic.index_word_dic[i_dic.word_comb_word_dic[
                            i_dic.word_index_dic[candidate_list[j]]][-1]]
                        result_dic[new_word] = len(ids)
                        ids_dic[new_word] = ids

        result_list = sorted(result_dic.items(), key=lambda x: x[1])
        lines = []
        for temp in result_list:
            try:
                lines.append(temp[0] + "@@" + str(temp[1]) + "@@" + str(
                    round(calculate_integrity(i_dic, temp[0]), 4)) + "@@" + str(
                    round(calculate_stability(i_dic, temp[0]), 4)) + "@@" + "##".join(
                    [str(round(x, 4)) for x in calculate_independence(i_dic, temp[0])]) + "@@" + "##".join(
                    [str(round(x, 4)) for x in calculate_independence_by_freq(i_dic, temp[0])]) + "@@" + "##".join(
                    [str(x) for x in ids_dic[temp[0]]]))
            except KeyError:
                print temp[0]
                continue
        tool.write_file("./dict/word_co.txt", lines, "a")
        try:
            del result_dic[u"新闻"]
            del result_dic[u"搜狐"]
        except:
            pass
        candidate_list = result_dic.keys()


def var_dump_word_tree(word, words, freq, values, doc_ids, word_index_dic):
    word_index = word_index_dic[word]
    print words[word_index], freq[word_index], values[word_index][0], values[word_index][1], \
        values[word_index][2], values[word_index][3]
    if len(word) > 2:
        return var_dump_word_tree(word[:-1], words, freq, values, doc_ids, word_index_dic), \
               var_dump_word_tree(word[1:], words, freq, values, doc_ids, word_index_dic)


def load_data():
    path = "./dict/word_co.txt"
    lines = tool.get_file_lines(path)
    words = []
    word_index_dic = {}
    values = []
    doc_ids = []
    freq = []
    num = 0
    for line in lines:
        arr = line.split("@@")
        words.append(arr[0].decode("utf8"))
        word_index_dic[arr[0].decode("utf8")] = num
        num += 1
        freq.append(int(arr[1]))
        brr = arr[4].split("##")
        values.append([float(arr[2]), float(arr[3]), float(brr[0]), float(brr[1])])
        doc_ids.append([int(x) for x in arr[6].split("##")])
    return words, freq, values, doc_ids, word_index_dic


def calculate_total_weight(freq, values):
    return freq * 0.1 + values[0] + values[1] + values[2] + values[3]


def remove_non_sense_word(words, freq, values):
    result = {}
    candidate_remove = {}
    for i in range(len(words)):
        if freq[i] > 2:
            if values[i][0] > 0.7 and values[i][1] > 0.52 and values[i][2] > 0.6:
                # print words[i], calculate_total_weight(freq[i], values[i])
                result[words[i]] = calculate_total_weight(freq[i], values[i])
                if words[i][:-1] in result:
                    candidate_remove[words[i][:-1]] = result[words[i][:-1]]
                    # if result[words[i][:-1]] < 4:
                    # del result[words[i][:-1]]
                if words[i][1:] in result:
                    candidate_remove[words[i][1:]] = result[words[i][1:]]
                    # if result[words[i][1:]] < 4:
                    # del result[words[i][1:]]
    result_list = sorted(result.items(), key=lambda x: x[1])  # 排序比较keys
    return result_list


def split_data_set(data, label, num, flag0=0, flag1=0):
    data = np.matrix(data)
    train_X = data[:num]
    train_Y = label[:num]
    if flag0 == 1:
        train_X_1 = train_X[np.where(train_Y == 1)]
        train_X_1 = train_X_1.repeat(2, axis=0)
        train_X_0 = train_X[np.where(train_Y == 0)]
        train_X_0 = train_X_0[:train_X_1.shape[0]]
        train_X = np.concatenate((train_X_0, train_X_1))
        train_Y = np.concatenate(
            (np.zeros(train_X_1.shape[0], dtype=np.int), np.ones(train_X_1.shape[0], dtype=np.int)))

    test_X = data[num:]
    test_Y = label[num:]
    if flag1 == 1:
        test_X_1 = test_X[np.where(test_Y == 1)]
        test_X_1 = test_X_1.repeat(2, axis=0)
        test_X_0 = test_X[np.where(test_Y == 0)]
        test_X_0 = test_X_0[:test_X_1.shape[0]]
        test_X = np.concatenate((test_X_0, test_X_1))
        test_Y = np.concatenate(
            (np.zeros(test_X_0.shape[0], dtype=np.int), np.ones(test_X_1.shape[0], dtype=np.int)))
    print len(train_X), len(train_Y), len(test_X), len(test_Y)
    return train_X, train_Y, test_X, test_Y


def train_clf():
    word_weights = pd.read_csv("./dict/word_weight.txt", header=None, sep=",")
    col_names = ["word_name", "freq", "integrity", "stability",
                 "independence_l", "independence_r", "label"]
    word_weights.columns = col_names
    label = word_weights["label"]
    words_pd = word_weights["word_name"]
    word_weights.drop("label", axis=1, inplace=True)
    word_weights.drop("word_name", axis=1, inplace=True)

    dt_clf = tree.DecisionTreeClassifier(max_depth=5)
    dt_clf.fit(word_weights, label)
    pre_y = dt_clf.predict(word_weights)
    # print classification_report(label, pre_y)
    return words_pd[pre_y == 1].index


def calculate_sim(word_i_doc_ids, word_j_doc_ids):
    word_i_set = set(word_i_doc_ids)
    word_j_set = set(word_j_doc_ids)
    return float(len(word_i_set & word_j_set)) / (np.sqrt(len(word_i_set)) * np.sqrt(len(word_j_set)))


def calculate_sim_by_cut(word_index_dic, doc_ids, word_i_cut_array, word_j_cut_array):
    word_i_set = set([])
    word_j_set = set([])
    for i in word_i_cut_array:
        if i in word_index_dic:
            word_i_set = word_i_set | set(doc_ids[word_index_dic[i]])
    for j in word_j_cut_array:
        if j in word_index_dic:
            word_j_set = word_j_set | set(doc_ids[word_index_dic[j]])
    # return float(len(word_i_set & word_j_set)) / (min_len * np.sqrt(max_len)), float(
    #     len(word_i_set & word_j_set)) / min(len(word_i_set), len(word_j_set)), float(
    #     len(word_i_set & word_j_set)) / (np.sqrt(min_len) * np.sqrt(max_len))
    return float(len(word_i_set & word_j_set)) / (np.sqrt(len(word_i_set)) * np.sqrt(len(word_j_set)))


def calculate_entropy(doc_ids, doc_word_dic):
    entropy_value = 0
    for doc_id in doc_ids:
        entropy_value += -float(1) / len(doc_word_dic[doc_id]) * math.log10(
            float(1) / len(doc_word_dic[doc_id]))
    return entropy_value


if __name__ == '__main__':

    i_dic = Inverted_index.InvertDic()
    i_dic.init_all_dic()
    # get_co_name()
    words, freq, values, doc_ids, word_index_dic = load_data()

    words_pd = pd.read_csv('./dict/word_info.txt', header=None, sep=',')
    col_names = ["word_name", "freq", "in", "st", "ind_l", "ind_r", "label"]
    words_pd.columns = col_names
    label = words_pd["label"]
    word_name = words_pd["word_name"]

    # 根据层次结构去重，在聚类之后做比较好
    word_set = set([])
    word_remove_set = set([])
    for w in word_name:
        word_set.add(w)
        word_remove_set.add(w[:-1])
        word_remove_set.add(w[1:])
    filter_word_name = word_set - word_remove_set

    # 分词
    word_cut_array = []
    for word in word_name:
        # print word
        if len(word) > 2:
            word_cut_array.append([x for x in jieba.cut(word)])
        else:
            word_cut_array.append([word])

    # 归一化，聚类效果评价
    # min_max_scaler = preprocessing.MinMaxScaler()
    # distance = min_max_scaler.fit_transform([])
    # print metrics.adjusted_rand_score(label, label)

    # 一趟聚类
    feature_array = []
    feature_tag = np.zeros(shape=len(word_cut_array))
    distance = np.zeros(shape=(len(word_cut_array), len(word_cut_array)))
    for i in range(len(word_cut_array) - 1):
        if feature_tag[i] == 0:
            feature_tag[i] = 1
            fc = FeatureCluster(word_cut_array[i])
            feature_array.append(fc)
            for j in range(i + 1, len(word_cut_array)):
                if i == j:
                    continue
                if feature_tag[j] == 0:
                    if remove_duplicate.count_similar([word_cut_array[i]], word_cut_array[j]):
                        pass
                        # print "".join(word_cut_array[i]), "".join(word_cut_array[j])
                    num = 0
                    for word_cut_array_k in fc.feature_cut_array:
                        similar = calculate_sim_by_cut(word_index_dic, doc_ids,
                                                       word_cut_array_k,
                                                       word_cut_array[j])
                        # print "".join(word_cut_array_k), "".join(word_cut_array[j]), similar
                        if similar > 0.7:
                            feature_tag[j] = 1
                            fc.append_new_feature_cut(word_cut_array[j])
                            break

                        if similar > 0.12:
                            num += 1
                            if float(num) / len(fc.feature_cut_array) > 0.2:
                                fc.append_new_feature_cut(word_cut_array[j])
                                feature_tag[j] = 1
                                break

    # 语义去重
    for fc in feature_array:
        new_feature_cut_array = []
        tag = np.zeros(shape=len(fc.feature_cut_array))
        for i in range(len(fc.feature_cut_array)):
            if tag[i] == 0:
                tag[i] = 1
                new_feature_cut_array.append(fc.feature_cut_array[i])
                for j in range(len(fc.feature_cut_array)):
                    if i == j:
                        continue
                    if tag[j] == 0:
                        if remove_duplicate.count_similar([fc.feature_cut_array[i]], fc.feature_cut_array[j]):
                            # print "".join(fc.feature_cut_array[i]), "".join(fc.feature_cut_array[j])
                            tag[j] = 1
        fc.feature_cut_array = new_feature_cut_array
        print fc

    # 将特征文档空间模型转换为文档特征空间模型
    doc_word_dic = {}
    for fc in feature_array:
        for feature_cut_array_k in fc.feature_cut_array:
            word_name = "".join(feature_cut_array_k)
            for doc_id in doc_ids[word_index_dic[word_name]]:
                doc_word_dic[doc_id] = doc_word_dic.get(doc_id, []) + [word_name]

    # 计算事件下每一个话题簇熵重叠度，越小越纯粹
    for fc in feature_array:
        for feature_cut_array_k in fc.feature_cut_array:
            word_name = "".join(feature_cut_array_k)
            print word_name, calculate_entropy(doc_ids[word_index_dic[word_name]], doc_word_dic)

