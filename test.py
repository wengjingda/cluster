# coding=utf-8

import info_init
import tool
import numpy as np
from jieba import posseg as pseg
from datetime import datetime


def count_similar(title_arr_list, title_arr_j):
    """ 利用相同关键词与最大公共子串长度计算事件与新闻的相似度

    对事件新闻列表中的每个新闻news_i:
        计算新闻news_i与新闻news_j的新闻标题分词交集intersection_ij
        对于交集intersection中的每个分词word：
            新闻i与新闻j的相似度similarity_ij+=词表中word的权重
        计算新闻i与新闻j标题中的最大公共子串LCS_ij
        alpha=1+最大公共子串的长度/新闻ij中标题长度的最大值
        相似度阈值limit=基础相似度阈值base_limit+新闻ij中标题长度的最大值/5
        如果similarity_ij*(1+alpha)>limit:
            相似新闻数similar_news_num+=1
    如果(相似新闻数/事件新闻数)>0.6:
        则认为事件与新闻相似，将新闻加入到事件的新闻列表中

    :param title_arr_list:包含多个新闻标题分词数组的二维数组
    :param title_arr_j:新闻标题分词数组
    :return:
    相似则返回True，否则返回False
    """
    similar_news_num = 0
    for title_arr_i in title_arr_list:
        similarity = float(0)
        similar_word_num = 0
        for word in set(title_arr_i) & set(title_arr_j):

            similar_word_num += 1
            similarity += info_init.termdir.get(word, 1)
            if word in info_init.flagdir:
                similarity += info_init.speechdir.get(info_init.flagdir[word], 1)
        if similar_word_num > 3:
            news_lcs = tool.lcs("".join(title_arr_i), "".join(title_arr_j))  # 最大相同子串
            similarity *= (1 + len(news_lcs) / max(len(title_arr_i), len(title_arr_j)))
        limit = info_init.similarity_limit + max(len(title_arr_i), len(title_arr_j)) / 5

        if similarity > limit:
            # print similarity, limit
            # print ".".join(title_arr_i) + "@@@@" + ".".join(title_arr_j)
            # print title_arr_i, title_arr_j
            similar_news_num += 1

    if float(similar_news_num) / len(title_arr_list) > 0.6:  # 投票表决
        return True
    else:
        return False


lines = tool.get_file_lines("./dict/doc.txt")
words_dic = {}
ids = []
time = []
for line in lines:
    arr = line.split("@@@@", 1)
    brr = arr[1].split("##", 3)
    words = [term.word for term in pseg.cut(brr[0])]
    words_dic[int(arr[0])] = words
    ids.append(int(arr[0]))
    # time.append(brr[2])
    time.append(datetime.strptime(brr[2], "%Y-%m-%d %H:%M:%S"))

time = np.array(time)
ids = np.array(ids)
ids = ids[np.argsort(time)]
time = np.sort(time)
filter_set = set([])

flags = np.ones(len(ids))
for i in range(len(ids) - 1):
    if flags[i]:
        flags[i] = 0
        for j in range(i + 1, len(ids)):
            if flags[j]:
                delta = time[i] - time[j]
                if abs(delta.days) < 2:
                    if count_similar([words_dic[ids[i]]], words_dic[ids[j]]):
                        flags[j] = 0
                        filter_set.add(j)
                else:
                    break

result = []
for i in set(ids) - filter_set:
    result.append(lines[i-1])
tool.write_file("./dict/filter_doc.txt", result, "w")
