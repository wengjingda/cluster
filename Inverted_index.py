# coding=utf-8

__author__ = 'david'
from datetime import datetime
import doc_proccess
import tool

time_format = "%Y-%m-%d %H:%M:%S"


class Term:
    """ 倒排索引条目，每个实体保留一个单词在一篇文档的信息

    如果单词在文档中出现过，创建Term类保留信息

            文章1     文章2     文章3
    单词1   Term
    单词2             Term
    单词3                       Term

    """

    def __init__(self, word_id, doc_id, tf):
        """

        :param word_id: 单词编号
        :param doc_id: 文档标号
        :param tf: 单词在文档中出现的次数
        :attribute location_ids: 数组，表示词在文章中出现的下标，ex.[1,3,7]
        """
        self.word_id = word_id
        self.doc_id = doc_id
        self.tf = tf
        self.location_ids = []

    def append_location(self, ids):
        """ 添加单词在文档中出现的位置信息

        :param ids:
        :return:
        """
        self.location_ids += ids

    def __str__(self):
        return str(self.word_id) + "@@@@" + str(self.doc_id) + "@@@@" + str(self.tf) + "@@@@" \
               + "##".join([str(x) for x in self.location_ids])


class InvertDic:
    """ 倒排索引词典

    """

    def __init__(self):
        """

        :attribute word_comb_word_dic: 词典，记录单词的组合形式，eq.{组合词编号:[单词1编号，单词2编号]}
        :attribute word_index_dic: 词典，记录单词编号，eq.{单词:单词编号}
        :attribute word_freq_dic: 词典，记录单词总词频，eq.{单词编号:单词总词频}
        :attribute word_term_dic: 词典，存储倒排索引条目信息，eq.{单词编号:[Term1，Term2]}
                                  Term类保存了一个单词在一篇文档中的信息
        :attribute word_df_dic: 词典，记录单词的文档频率，eq.{单词编号:单词文档频率}
        :attribute doc_dic: 词典，eq.{文档编号:文档标题##文档正文}
        :attribute doc_len: 整数，表示现有文档数量
        :attribute word_num: 整数，表示现有单词数量
        """

        self.index_word_dic = {}
        self.word_comb_word_dic = {}
        self.word_index_dic = {}
        self.word_freq_dic = {}
        self.word_term_dic = {}
        self.word_df_dic = {}
        self.doc_dic = {}
        self.doc_len = doc_proccess.Doc.get_lasted_doc_id() + 1
        self.word_num = 0
        # self.init_all_dic()

    def init_all_dic(self):
        self.get_doc_dic()
        self.get_word_df_dic()
        self.get_word_freq_dic()
        self.get_word_index_dic()
        self.get_word_term_dic()

    def save_word_df_dic(self):
        lines = []
        for it in self.word_df_dic.items():
            lines.append(str(it[0]) + "\t" + str(it[1]))
        tool.write_file("./dict/word_df_dic.txt", lines, "w")

    def save_word_index_dic(self):
        lines = []
        for it in self.word_index_dic.items():
            lines.append(it[0] + "@@@@" +
                         str(it[1]) + "@@@@" + "##".join([str(x) for x in self.word_comb_word_dic[it[1]]]))
        tool.write_file("./dict/word_index_dic.txt", lines, "w")

    def save_word_freq_dic(self):
        lines = []
        for it in self.word_freq_dic.items():
            lines.append(str(it[0]) + "\t" + str(it[1]))
        tool.write_file("./dict/word_freq_dic.txt", lines, "w")

    def save_word_term_dic(self):
        lines = []
        for it in self.word_term_dic.items():
            for t in it[1]:
                lines.append(t.__str__())
        tool.write_file("./dict/word_term_dic.txt", lines, "w")

    def get_doc_dic(self):
        lines = tool.get_file_lines("./dict/doc.txt")
        for line in lines:
            temp = line.split("@@@@")
            info = temp[1].split("##", 3)
            self.doc_dic[int(temp[0])] = doc_proccess.Doc(info[0], info[3], info[1], datetime.strptime(
                info[2], time_format), int(temp[0]))

    def get_word_df_dic(self):
        lines = tool.get_file_lines("./dict/word_df_dic.txt")
        for line in lines:
            temp = line.split("\t")
            self.word_df_dic[int(temp[0])] = int(temp[1])

    def get_word_index_dic(self):
        lines = tool.get_file_lines("./dict/word_index_dic.txt")
        for line in lines:
            temp = line.split("@@@@")
            try:
                self.index_word_dic[int(temp[1])] = temp[0].decode("utf-8")
                self.word_index_dic[temp[0].decode("utf-8")] = int(temp[1])
                self.word_num += 1
                self.word_comb_word_dic[int(temp[1])] = [int(x) for x in temp[2].split("##")]
            except UnicodeError:
                print "error"
                continue

    def get_word_freq_dic(self):
        lines = tool.get_file_lines("./dict/word_freq_dic.txt")
        for line in lines:
            temp = line.split("\t")
            self.word_freq_dic[int(temp[0])] = int(temp[1])

    def get_word_term_dic(self):
        lines = tool.get_file_lines("./dict/word_term_dic.txt")
        for line in lines:
            temp = line.split("@@@@")
            t = Term(int(temp[0]), int(temp[1]), int(temp[2]))
            t.append_location([int(x) for x in temp[3].split("##")])
            self.word_term_dic[int(temp[0])] = self.word_term_dic.get(int(temp[0]), []) + [t]

    def update_df_dic(self, words):
        """ 更新文档频率

        :param words:
        :return:
        """
        for word in set(words):
            self.word_df_dic[self.word_index_dic[word]] = self.word_df_dic.get(self.word_index_dic[word], 0) + 1

    def update_invert_index(self, doc):
        """ 更新倒排索引词典，可以将新的文章添加到倒排索引词典内

        :param doc: Doc类
        :return:
        """
        word_id = len(self.word_index_dic)
        self.doc_len += 1
        n_set = set()
        for word in doc.words:
            if word not in self.word_index_dic:
                self.word_index_dic[word] = word_id
                self.word_comb_word_dic[word_id] = [word_id]
                self.word_freq_dic[self.word_index_dic[word]] = 1
                word_id += 1
            else:
                self.word_freq_dic[self.word_index_dic[word]] += 1
            if word not in n_set:
                n_set.add(word)
                t = Term(self.word_index_dic[word], doc.doc_id, doc.freq_dic[word])
                t.append_location(doc.location_dic[word])
                self.word_term_dic[self.word_index_dic[word]] = self.word_term_dic.get(self.word_index_dic[word],
                                                                                       []) + [t]
        self.update_df_dic(doc.words)
        self.doc_dic[doc.doc_id] = doc
        # tool.write_file("./dict/doc.txt", [doc.__str__()], "a")

    def get_co_occurrence_info(self, word_i, word_j):
        set_i, dict_i = self.transform_term_info(word_i)
        set_j, dict_j = self.transform_term_info(word_j)
        ids = []
        locations = []
        for k in set_i & set_j:
            temp = []
            list_i = sorted(dict_i[k].location_ids)
            list_j = sorted(dict_j[k].location_ids)
            if list_i[0] > list_j[-1]:
                continue
            for id_i in list_i:
                for id_j in list_j:
                    if id_i == id_j - 1:
                        if k not in ids:
                            ids.append(k)
                        temp.append(id_i)
            if len(temp) > 0:
                locations.append(temp)
        return ids, locations

    def add_term_bound(self, word_i, word_j):
        if word_i + word_j in self.word_index_dic:
            # print "组合词已在词典"
            return False
        if word_i not in self.word_index_dic or word_j not in self.word_index_dic:
            # print "待组合词不在词典"
            return False
        comb_i = self.word_comb_word_dic[self.word_index_dic[word_i]]
        comb_j = self.word_comb_word_dic[self.word_index_dic[word_j]]
        if len(comb_i) == len(comb_j):
            for i in range(1, len(comb_i)):
                if comb_i[i] != comb_j[i - 1]:
                    # print "待组合词不匹配"
                    return False
        else:
            # print "待组合词长度不同"
            return False
        return True

    def add_new_term(self, word_i, word_j):
        if self.add_term_bound(word_i, word_j):
            doc_ids, doc_locations = self.get_co_occurrence_info(word_i, word_j)
            word_k = word_i + self.index_word_dic[self.word_comb_word_dic[self.word_index_dic[word_j]][-1]]
            self.word_index_dic[word_k] = word_k_id = self.word_num
            self.word_num += 1
            self.word_df_dic[word_k_id] = len(doc_ids)
            self.word_comb_word_dic[word_k_id] = self.word_comb_word_dic[self.word_index_dic[word_i]] + \
                                                 self.word_comb_word_dic[self.word_index_dic[word_j]][-1:]
            for i in range(len(doc_ids)):
                self.word_freq_dic[word_k_id] = self.word_freq_dic.get(word_k_id, 0) + len(doc_locations[i])
                t = Term(word_k_id, doc_ids[i], len(doc_locations[i]))
                t.append_location(doc_locations[i])
                self.word_term_dic[word_k_id] = self.word_term_dic.get(word_k_id, []) + [t]
        else:
            print "不满足规范"

    def transform_term_info(self, word):
        word_set = set([])
        word_dict = {}
        for i_term in self.word_term_dic[self.word_index_dic[word]]:
            word_set.add(i_term.doc_id)
            word_dict[i_term.doc_id] = i_term
        return word_set, word_dict


if __name__ == '__main__':
    # 初始化词典
    i_dic = InvertDic()
    candidate_list = i_dic.word_index_dic.keys()
    candidate_list = list(set(candidate_list) - tool.get_stop_word())
    result_dic = {}
    tool.write_file("./dict/word_co.txt", [], "w")

    for k in range(4):
        result_dic = {}
        for i in range(len(candidate_list)):
            for j in range(len(candidate_list)):
                if i == j:
                    continue
                if i_dic.add_term_bound(candidate_list[i], candidate_list[j]):
                    ids, locations = i_dic.get_co_occurrence_info(candidate_list[i], candidate_list[j])
                    if len(ids) > 6:
                        i_dic.add_new_term(candidate_list[i], candidate_list[j])
                        new_word = candidate_list[i] + i_dic.index_word_dic[i_dic.word_comb_word_dic[
                            i_dic.word_index_dic[candidate_list[j]]][-1]]
                        result_dic[new_word] = len(ids)

        result_list = sorted(result_dic.items(), key=lambda x: x[1])
        lines = []
        for temp in result_list:
            try:
                lines.append(temp[0] + "##" + str(temp[1]) + "##" + str(
                    len(i_dic.word_comb_word_dic[i_dic.word_index_dic[temp[0]]])))
            except KeyError:
                print temp[0]
                continue
        tool.write_file("./dict/word_co.txt", lines, "a")
        candidate_list = result_dic.keys()

        # i_dic.save_word_index_dic()
        # i_dic.save_word_df_dic()
        # i_dic.save_word_freq_dic()
        # i_dic.save_word_term_dic()
