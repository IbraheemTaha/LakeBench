import heapq
import pickle
import time
import pandas as pd
import networkx as nx
from tqdm import tqdm
from multiprocessing import Process, Queue
import multiprocessing
import os


#读取表格的第一列，假设第一列是主题列
def read_first_column(df):
    # 读取CSV文件，假设第一列是主题列
    # 读取第一列数据并存储在一个Series对象中
    first_column_list = df.iloc[:, 0].tolist()
    return first_column_list

#读取表格的第二列，假设第一列是主题列
def read_sencond_column(df):
    # 读取CSV文件，假设第一列是主题列
    # 读取第一列数据并存储在一个Series对象中
    first_column_list = df.iloc[:, 1].tolist()
    return first_column_list

#计算一对表格的SECover得分
def one_SECover(list1, list2):  #计算一对表的SECover得分
    # 先将列表的重复值去除，转换为集合
    set1 = set(list1)
    set2 = set(list2)

    #计算set1，set2的元素个数
    len1 = len(set1)

    # 求两个集合的交集，即相同的元素
    intersection_set = set1.intersection(set2)

    # 计算元素相同的个数
    SECover = len(intersection_set) / len1
    # print(SECover)
    return SECover

def cal_intersection(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    intersection = set1 & set2  # 交集运算符
    return intersection

# 计算Jaccard相似度的函数
def jaccard_similarity(str1, str2):
    set1 = set(str1)
    set2 = set(str2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

# 计算一个候选表的额外属性
def add_attributes(query_att_list, candidate_att_list):
    # 创建一个无向图
    G = nx.Graph()

    # 将列表1中的元素添加到图的一个集合中
    G.add_nodes_from(query_att_list, bipartite=0)

    # 将列表2中的元素添加到图的另一个集合中
    G.add_nodes_from(candidate_att_list, bipartite=1)

    # 计算并添加边的权重（使用Jaccard相似度）
    for elem1 in query_att_list:
        for elem2 in candidate_att_list:
            weight = jaccard_similarity(elem1, elem2)
            G.add_edge(elem1, elem2, weight=weight)

    # 最大权重匹配
    matching = nx.algorithms.max_weight_matching(G, maxcardinality=True)

    # 输出匹配结果，同时存储相似度值
    matched_pairs = {}
    match_att = []
    for elem1, elem2 in matching:
        similarity = G[elem1][elem2]['weight']
        matched_pairs[(elem1, elem2)] = similarity
        match_att.append(elem2)
    #存储一对一映射的个数，以及list1,list2的元素个数
    # print("映射为",matched_pairs)
    add_attr = [x for x in candidate_att_list if x not in match_att]
    return add_attr

# 计算一个候选表的额外一对一映射
def can_pairs(query_att_list, candidate_att_list):
    # 创建一个无向图
    G = nx.Graph()

    # 将列表1中的元素添加到图的一个集合中
    G.add_nodes_from(query_att_list, bipartite=0)

    # 将列表2中的元素添加到图的另一个集合中
    G.add_nodes_from(candidate_att_list, bipartite=1)

    # 计算并添加边的权重（使用Jaccard相似度）
    for elem1 in query_att_list:
        for elem2 in candidate_att_list:
            weight = jaccard_similarity(elem1, elem2)
            G.add_edge(elem1, elem2, weight=weight)

    # 最大权重匹配
    matching = nx.algorithms.max_weight_matching(G, maxcardinality=True)

    # 输出匹配结果，同时存储相似度值
    matched_pairs = {}
    match_att = []
    max_similarity = -1
    max_att = ''
    for elem1, elem2 in matching:
        similarity = G[elem1][elem2]['weight']
        if similarity > max_similarity:
            max_similarity = similarity
            max_att = elem2

    return max_att

#读取表格第一行,即读取表头
def read_att(mytable_path):
    # 读取CSV文件，假设第一行是表头
    df = pd.read_csv(mytable_path,low_memory=False)

    # 获取表头，并存放在一个列表中
    headers_list = df.columns.tolist()
    return headers_list


def one_SSB(query_att, one_table_add_att, one_att_freq, two_att_freq):
    end_dict = {}
    length = len(query_att)
    for add in one_table_add_att:
        count = 0.0
        for query in query_att:
            mid = []
            mid.append(add)
            mid.append(query)
            t1 = tuple(mid)
            if t1 in two_att_freq:
                mid1 = two_att_freq[t1]
                # print(mid1)
            else:
                mid1 = 0

            if query in one_att_freq:
                # print(query)
                mid2 = one_att_freq[query]

            else:
                mid2 = 0
            # print(mid1, mid2)
            if mid2 == 0:
                mid_result = 0
            else:
                mid_result = mid1 / mid2
            count += mid_result
        end_dict[add] = count / length
    if end_dict:
        max_item = max(end_dict.items(), key=lambda item: item[1])
        result = max_item[1]
    else:
        result = 0
    return result

def find_largest_five(my_dict, max_k):
    files_result = []
    largest_items = heapq.nlargest(max_k, my_dict.items(), key=lambda item: item[1])
    for key, value in largest_items:
        files_result.append(key)
    print(files_result)
    return files_result

def all_schema(fnames, can_label_second_column, query_label_second_column, can_entity_list, query_entity,
               query_attribute, can_all_att, one_att_freq, two_att_freq, max_k):
    count = 0
    result = {}
    for file_name in tqdm(fnames):
        second = can_label_second_column[count]
        inter = cal_intersection(second, query_label_second_column)

        if inter == 0:
            result[file_name] = 0.0
            count += 1
        else:
            SEcover = one_SECover(query_entity, can_entity_list[count])
            add = add_attributes(query_attribute, can_all_att[count])
            SSB = one_SSB(query_attribute, add, one_att_freq, two_att_freq)
            result[file_name] = SEcover * SSB
            count += 1
    # for key, value in result.items():
    #     if value != 0:
    #         print(value)
    end_result = find_largest_five(result, max_k)
    return end_result

def find_join(can_file_path, query_file_path):
    can_att = read_att(can_file_path)
    query_att = read_att(query_file_path)
    max_att = can_pairs(query_att, can_att)
    return max_att
    
def csv_make(save_csv_path, all_join_result):

    with open(save_csv_path, mode='w', newline='') as csv_file:
        # 创建CSV写入对象
        csv_writer = csv.writer(csv_file)
    
        # 遍历列表l中的每个子列表，并将它们写入不同的行
        for join_result in all_join_result:
            csv_writer.writerow(join_result)
    print(f"已将列表写入到 {csv_file_path} 文件中。")
    

def split_list(lst, num_parts):
    avg = len(lst) // num_parts
    remainder = len(lst) % num_parts

    result = []
    start = 0
    for i in range(num_parts):
        if i < remainder:
            end = start + avg + 1
        else:
            end = start + avg
        result.append(lst[start:end])
        start = end

    return result


s = time.time()


#获取文件名
fnames = []
files_names = r'../offline_processing_end/file_names.pkl'
with open(files_names, 'rb') as f:
    fnames = pickle.load(f)


#获取候选表的实体标签
#with open(file='entity_label.pkl',mode='wb') as f:
    # pickle.dump(second_column, f)
can_label_second_column = []
can_entity_label = r'../offline_processing_end/entity_label.pkl'
with open(can_entity_label, 'rb') as f:
    can_label_second_column = pickle.load(f)




#获取候选表所具有的实体
can_entity = r'../offline_processing_end/can_entity_list.pkl'
can_entity_list = []
with open(can_entity, 'rb') as f:
    can_entity_list = pickle.load(f)


#获取候选表的属性总列表
can_all_att = []
with open('../offline_processing_end/candidate_attributes_list.pkl', 'rb') as f:
    can_all_att = pickle.load(f)

#获取属性出现的频数
one_att_freq = []
with open('../offline_processing_end/one_att_freq.pkl', 'rb') as f:
    one_att_freq = pickle.load(f)

two_att_freq = []
with open('../offline_processing_end/two_att_freq.pkl', 'rb') as f:
    two_att_freq = pickle.load(f)

# #获得查询表的实体标签
# query_label_path = r'tar1_label.csv'
# df1 = pd.read_csv(query_label_path)
# query_label_second_column = read_sencond_column(df1)

# #获取查询表的第一列实体
# query_csv_path = r'tar1.csv'
# df2 = pd.read_csv(query_csv_path)
# query_entity = read_first_column(df2)
# #获取查询表的属性，即第一行
# query_attribute = read_att(query_csv_path)



# all_schema(fnames, can_label_second_column, query_label_second_column, can_entity_list, query_entity,
#                query_attribute, can_all_att, one_att_freq, two_att_freq)


query_folder_label_path = r'../webtable_label/label_folder_small_query'
query_folder_path = r'/data_ssd/webtable/large/small_query'
file_list = os.listdir(query_folder_path)

def multi(file_ls,queue,query_result,max_k):
    all_join_result = []
    for filename in file_ls:
        if filename.endswith('.csv'):
            query_path = os.path.join(query_folder_path, filename)
            df2 = pd.read_csv(query_path,low_memory = False)
            query_entity = read_first_column(df2)
            #获取查询表的属性，即第一行
            query_attribute = read_att(query_path)

            query_label_path = os.path.join(query_folder_label_path, filename)
            df1 = pd.read_csv(query_label_path, low_memory=False, lineterminator='\n')
            query_label_second_column = read_sencond_column(df1)

            result = all_schema(fnames, can_label_second_column, query_label_second_column, can_entity_list, query_entity,
                query_attribute, can_all_att, one_att_freq, two_att_freq, max_k)
            
            for value in result.values():
                join = []
                join.append(filename)
                join.append(value)
                can_path = os.path.join(query_folder_path, value)
                att = find_join(query_path, can_path)
                join.append(att)
                all_join_result.append(join)
        queue.put(1)
    query_result.put(all_join_result)
    queue.put((-1, "test-pid"))

split_num = 72
query_result = multiprocessing.Manager().Queue()


sub_file_ls = split_list(file_list, split_num)

process_list = []

#####
# 为每个进程创建一个队列
queues = [multiprocessing.Manager().Queue() for i in range(split_num)]
# queue = Queue()
# 一个用于标识所有进程已结束的数组
finished = [False for i in range(split_num)]

# 为每个进程创建一个进度条
bars = [tqdm(total=len(sub_file_ls[i]), desc=f"bar-{i}", position=i) for i in range(split_num)]
# bar = tqdm(total=len(file_ls[0]), desc=f"process-{i}")
# 用于保存每个进程的返回结果
results = [None for i in range(split_num)]

max_k = 10
for i in range(split_num):
    process = Process(target=multi, args=(sub_file_ls[i], queues[i], query_result, max_k))
    process_list.append(process)
    process.start()

while True:
    for i in range(split_num):
        queue = queues[i]
        bar = bars[i]
        try:
            # 从队列中获取数据
            # 这里需要用非阻塞的get_nowait或get(True)
            # 如果用get()，当某个进程在某一次处理的时候花费较长时间的话，会把后面的进程的进度条阻塞着
            # 一定要try捕捉错误，get_nowait读不到数据时会跑出错误
            res = queue.get_nowait()
            if isinstance(res, tuple) and res[0] == -1:
                # 某个进程已经处理完毕
                finished[i] = True
                results[i] = res[1]
                continue
            bar.update(res)
        except Exception as e:
            continue

            # 所有进程处理完毕
    if all(finished):
        break

for process in process_list:
    process.join()

final_result = []
while not query_result.empty():
    try:
        element = query_result.get_nowait()
        final_result.extend(element)
    except Exception as e:
        continue


save_file = r'./result_opendata' + str(max_k) + '.csv'
csv_make(save_file, final_result)
   

e = time.time()
print(e-s)