import sys
sys.path.append('e:\RAG框架\SECOND')
import os
import yaml
import mysql.connector
from concurrent.futures import ThreadPoolExecutor
from tensorrt_engine.BCE_embedding import embeddings 
from pymilvus import MilvusClient

# 加载YAML配置
def load_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

# 加载配置
config_file = os.path.join(os.path.dirname(__file__), 'config.yml')
config = load_config(config_file)

client = MilvusClient(config['MILVUS']['url'])

# 连接 MySQL 数据库
documents = mysql.connector.connect(
    host=config['MYSQL']['host'],
    user=config['MYSQL']['user'],
    password=config['MYSQL']['password'],
    database=config['MYSQL']['database']
)
cursor = documents.cursor()

embedding_model = embeddings

# 异步调用用的线程池
executor = ThreadPoolExecutor()

def searchDoc_by_query(query, embedding_model=embedding_model, limit=10):
    query = [query] if not isinstance(query, list) else query
    embedding_list = embedding_model(query)
    
    # 向量相似度搜索
    res = client.search(
        collection_name="law",
        data=embedding_list,
        limit=limit,
        search_params={"metric_type": "COSINE", "params": {}}
    )
    return res, embedding_list

def searchSlice_by_query(id_list, embedding_list, limit=10):
    res = client.search(
        collection_name="law_slice",
        data=embedding_list,
        limit=limit,
        search_params={"metric_type": "COSINE", "params": {}},
        output_fields=["SLICE_HASH"],
        filter=f"FULL_TEXT_HASH in {id_list}",
    )
    return res

def search_sql(hash_list):
    global documents
    global cursor
    meta_text = "\n<llmlingua,compress=False>信息来源:{}\t发布时间：{}\t发布单位：{}\t类别：{}\t生效时间：{}</llmlingua>"
    placeholders = ', '.join(['%s'] * len(hash_list))  # 用于 SQL 查询中的占位符
    query = f"SELECT * FROM document WHERE hash IN ({placeholders})"

    try:
        cursor.execute(query, hash_list)  # 执行查询
        results = cursor.fetchall()  # 获取所有结果
        # 根据对应字段名，将结果转化为可理解的文本
        res = []
        columns = [desc[0] for desc in cursor.description]  # 获取列名
        for result in results:
            entry = {}
            for i in range(len(columns)):
                if columns[i] != 'content':
                    entry[columns[i]] = result[i]
                else:
                    entry['content'] = result[i] + meta_text.format(*result[i+1:])  # 处理 metadata
            res.append(entry)
        return res
        
    except mysql.connector.Error as error:
        #如果是丢失了连接，则重新连接
        if error.errno == 2006 or error.errno == 2013:
            documents = mysql.connector.connect(
                host=config['MYSQL']['host'],
                user=config['MYSQL']['user'],
                password=config['MYSQL']['password'],
                database=config['MYSQL']['database']
            )
            cursor = documents.cursor()
            return search_sql(hash_list)
        print(f"查询失败: {error}")
        return "查询失败"


# 搜索函数装入线程池
def search(query, embedding_model=embedding_model, doc_limit=10, slice_limit=10, threshold=0.5, final_return=10):
    output, embedding_list = searchDoc_by_query(query, embedding_model, limit=doc_limit)
    id_list = [[i['id'] for i in item] for item in output]
    results = []

    for index, id_ in enumerate(id_list):
        search_res = searchSlice_by_query(id_, [embedding_list[index]], limit=slice_limit)
        SLICE_HASH = [i['entity']['SLICE_HASH'] for i in search_res[0] if i['distance'] > threshold][:final_return]  
        if SLICE_HASH == []:
            res = "抱歉，没有找到符合要求的内容"
        else:
            res = search_sql(SLICE_HASH)
        results.append(res)
    
    return results

if __name__ == "__main__":
    query = "宠物保护法"
    with executor:
        future = executor.submit(search, query)
        res = future.result()
        print(res)
