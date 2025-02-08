import os
import sys
sys.path.append('root/4.0')
from New.Engine.Tensorrt.BCEembedding  import BCEembedding    
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import nest_asyncio
nest_asyncio.apply()
file_dir=os.path.dirname(__file__)
sys.path.append(file_dir)
class SearchEngine:
    def __init__(self, embedding_engine=BCEembedding):
        self.embedding_engine = embedding_engine
        self.embedding=None
        self.mysql = None
        self.es = None
        self.milvus = None
        self.run()
    def run(self):
        asyncio.run(self.initialize())
    async def initialize(self):
        print("正在初始化知识库...")
        # 使用线程池并行初始化embedding，MySQL，Elasticsearch和Milvus
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            # 初始化其他数据库
            tasks = [
                self.init_mysql(),
                self.init_elasticsearch(),
                self.init_milvus()
            ]
            await asyncio.gather(*tasks)  # 同时运行所有初始化任务
            await self.load_kb_dict()
        self.embedding =self.embedding_engine()
        print("知识库初始化成功，使用{}向量引擎。".format(self.embedding.name))
    async def init_mysql(self):
        from ..Dataset.mysql import Mysql
        loop = asyncio.get_event_loop()
        self.mysql = await loop.run_in_executor(None, Mysql)
        print("connect to mysql success")

    async def init_elasticsearch(self):
        from ..Dataset.elasticsearch import ElasticSearch
        loop = asyncio.get_event_loop()
        self.es = await loop.run_in_executor(None, ElasticSearch)
        print("connect to es success!")

    async def init_milvus(self):
        from ..Dataset.milvus import Milvus
        loop = asyncio.get_event_loop()
        self.milvus = await loop.run_in_executor(None, Milvus)
        print("connect to milvus success")

    async def load_kb_dict(self):
        try:
            if self.milvus and self.milvus.show() == []:
                self.kb_dict = {}
            else:
                with open(os.path.join(file_dir, "kb_dict.json"), "r") as f:
                    self.kb_dict = json.load(f)
            print("初始化知识库成功！")
        except Exception as e:
            print(f"Error loading knowledge base dictionary: {e}")
    async def search(self, name, query, keyword_threshold=3, top_k=10,top_e=10):
        embedding_list = self.embedding(query)
        if name not in self.kb_dict:
            print("该知识库不存在！")
            return None
        
        milvus_result = self.milvus.search(name, embedding_list, top_k=top_e)
        es_result = await self.es.search(name, query, threshold=keyword_threshold, top_k=top_k)
        search_ids=[ item['id']  for item in milvus_result[0]]
        milvus_result= await self.es.search_for_ids(name=name,id_list=search_ids)
        #混合搜索结果去重
        result_total=milvus_result+es_result
        norepeat_dict={}
        for item in result_total:
            if item['slice_id'] not in norepeat_dict:
                norepeat_dict[item['slice_id']]=item
        norepeat_result=list(norepeat_dict.values())
        #mysql_result = self.mysql.search(name, milvus_result['slice_id'])
        print("混合搜索完毕。")
        return norepeat_result
