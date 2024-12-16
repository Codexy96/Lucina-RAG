import os
import sys
model_dir=sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
#from  Tensorrt.BCE_embedding import BCEembedding 
from ..model.Embedding.BCEembedding import BCEembedding
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import nest_asyncio
nest_asyncio.apply()
file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
class KnowledgeBase:
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
        from Mysql.mysql import Mysql
        loop = asyncio.get_event_loop()
        self.mysql = await loop.run_in_executor(None, Mysql)
        print("connect to mysql success")

    async def init_elasticsearch(self):
        from Elasticsearch.ES import ElasticSearch
        loop = asyncio.get_event_loop()
        self.es = await loop.run_in_executor(None, ElasticSearch)
        print("connect to es success!")

    async def init_milvus(self):
        from Milvus.milvus import Milvus
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

    def create_kb(self, name, description):
        if name in self.kb_dict or name in self.es.show() or name in self.mysql.show() or name in self.milvus.show():
            print("该知识库已存在！")
            return False
        else:
            self.kb_dict[name] = description
            print("创建知识库成功！")
            
            # 更新持久化的kb_dict文件
            with open(os.path.join(file_dir, "kb_dict.json"), "w") as f:
                json.dump(self.kb_dict, f, ensure_ascii=False, indent=4)
            
            return True

    def insert_data(self, name, data):
        if name not in self.kb_dict:
            print("该知识库不存在！")
            return False
        else:
            #为milvus创建向量数据，组建新数据
            embedding_list=self.embedding([ item['content'] for item in data])
            
            milvus_data=[ {'slice_id':item['slice_id'],'vector':embedding_list[index]}for index,item in enumerate(data)]
            fields = list(data[0].keys())
            #为milvus创建单独的字段，它只需要包含slice_id和vector两个字段即可
            milvus_fields=['slice_id','vector']
            print("提取的字段名:",fields)
            if name in self.milvus.show():
                pass
            else:
                self.milvus.create(name=name, fields=milvus_fields,core_dict={'method':'IVF_FLAT','dim':self.embedding.dim})
            #if name in self.mysql.show():
                #pass
            #else:
                #self.mysql.create(name=name, fields=fields)
            if name in self.es.show():
                pass
            else:
                self.es.create(name=name,fields=fields)
            
            #self.mysql.insert(name=name, data=data)
            self.es.insert(name=name, data=data)
            self.milvus.insert(name=name, data=milvus_data)
            print("插入数据成功！共向知识库{}插入了{}条数据。".format(name, len(data)))
            return True

    async def search(self, name, query, keyword_threshold=3, top_k=10,top_e=10):
        embedding_list = self.embedding(query)
        if name not in self.kb_dict:
            print("该知识库不存在！")
            return None
        
        milvus_result = self.milvus.search(name, embedding_list, top_k=top_e)
        es_result = await self.es.search(name, query, threshold=keyword_threshold, top_k=top_k)
        search_ids=[ item['id']  for item in milvus_result[0]]
        milvus_result= await self.es.search_for_ids(name=name,id_list=search_ids)
        #mysql_result = self.mysql.search(name, milvus_result['slice_id'])
        print("搜索完毕。")
        return {
            "embedding_search": milvus_result,
            "keyword_search": es_result
        }

