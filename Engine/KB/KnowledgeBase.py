import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
model_dir=sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
#from  Tensorrt.BCE_embedding import BCEembedding 
from ..Tensorrt.BCEembedding import BCEembedding
from ..Dataset.elasticsearch import Elasticsearch
from ..Dataset.mysql import Mysql
from ..Dataset.milvus import Milvus
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import nest_asyncio
nest_asyncio.apply()
file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
#----------------------------------------------------

    ####### KB(knowledge base) 基础类 #######

    #负责统一管理所使用的数据库（milvus、elasticsearch、mysql）的初始化、创建、数据导入、数据搜索功能。

    #创建实例时将自动初始化所需的数据库连接

    #########  mysql:负责管理知识库的生命周期，记录每个知识库的创建信息、改动信息等。

    #########  elasticsearch:存储文档数据

    ######### milvus:存储向量到文档的映射

    ######### 统一接口：
    
    ######### 1、create_kb(name, description): 创建知识库，name为知识库名称，description为描述信息

    ######### 2、inseart_data(name, data): 插入数据，name为知识库名称，data为插入的数据，数据格式为键值对组成的列表，字典的key为字段名，value为字段值，只接受文本数据。

    ######### 3、show_kb(): 展示当前知识库列表

    ######### 4、 delete_kb(name): 删除知识库，name为知识库名称，一旦删除，连同数据永久删除

    ######### 5、milvus不支持回退操作，一旦插入过程终止，需重置知识库重新导入。

    ######### 6、reset_kb() : 重置知识库，将所有数据清空，仅支持已创建的知识库。

#----------------------------------------------------
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
        self.embedding =self.embedding_engine()
        print("知识库初始化成功，使用{}向量引擎。".format(self.embedding.name))
    async def init_mysql(self):
        loop = asyncio.get_event_loop()
        self.mysql = await loop.run_in_executor(None, Mysql)
        if not self.mysql.exists():
            self.mysql.create_database()
        print("connect to mysql success")

    async def init_elasticsearch(self):
        loop = asyncio.get_event_loop()
        self.es = await loop.run_in_executor(None, Elasticsearch)
        print("connect to es success!")

    async def init_milvus(self):
        loop = asyncio.get_event_loop()
        self.milvus = await loop.run_in_executor(None, Milvus)
        print("connect to milvus success")


    def create_kb(self, name, description):
        if name in self.mysql.exists_kb(name):
            print("该知识库已存在！")
            return False
        else:
            self.mysql.create_kb(name, description)
            print("创建知识库成功！")        
            return True

    def insert_data(self, name, data):
        if not self.mysql.exists_kb(name):
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
            if name in self.es.show():
                pass
            else:
                self.es.create(name=name,fields=fields)
            self.es.insert(name=name, data=data)
            self.milvus.insert(name=name, data=milvus_data)
            print("插入数据成功！共向知识库{}插入了{}条数据。".format(name, len(data)))
            return True
    def show_kb(self):
        kb_list=self.mysql.get_all_kb()
        print("当前知识库列表：",kb_list)

    def delete_kb(self, name):
        if not self.mysql.exists_kb(name):
            print("该知识库不存在！")
            return False
        else:
            self.mysql.delete_kb(name)
            self.es.delete(name)
            self.milvus.delete(name)
            print("删除知识库{}成功！".format(name))
            return True
    def reset_kb(self, name):
        if not self.mysql.exists_kb(name):
            print("该知识库不存在！")
            return False
        else:
            self.delete_kb(name)
            self.create_kb(name, "重置后的描述信息")
            print("重置知识库{}成功！".format(name))
            return True

