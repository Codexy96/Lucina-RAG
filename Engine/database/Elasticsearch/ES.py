"""
Elasticsearch 的操控封装脚本

实现：
1、连接 Elasticsearch

2、创建表

3、插入数据

4、查询数据

5、查看现有的表

6、删除表

遵循一致的命名规范：

__init__()

search()

delete()

insert()

create()

show()
"""
import os
file_dir=os.path.dirname(__file__)
class ElasticSearch:
    def __init__(self):
        import configparser
        config=configparser.ConfigParser()
        config.read(os.path.join(file_dir,"config.ini"))
        from elasticsearch import Elasticsearch
        self.es=Elasticsearch(config.get("elasticsearch","uri"))
        if not self.es.ping():
            raise Exception("Elasticsearch 连接失败")
        else:
            print("Elasticsearch 连接成功")
    def create(self,name:str,fields:list=None):
        """
        创建索引，即表阶段，采用默认索引创建模式

        参数：
        name:str 索引名称，必填

        fields(选填): 字段列表，必须包含以下基本字段：slice_id、content，其余字段可选，slice_id为keyword类型，content为文本类型，其余默认为文本形式，如果不输入，则默认仅采用slice_id、content字段。

        字段列表示例：
        fields=[slice_id,content,title,url.....]
        """
        if  fields:
            index_fields={  key:{"type":"keyword"}  if key=="slice_id" else  {"type":"text"}  for key in fields}
        else:
            index_fields={
                "slice_id": "keyword",
                "content": "text"

            }
        settings={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings":{
                "properties":index_fields
            }
        }
        if not self.es.indices.exists(index=name):
            self.es.indices.create(index=name,body=settings)
            print(f"创建{name}索引成功")
        else:
            print(f"{name}索引已存在")
        
    async def search(self,name, query, threshold=1.0, top_k=10):
        import asyncio
        from elasticsearch import ConnectionError, NotFoundError
        import logging
        search_query = {
        "query": {
            "bool": {
                "must": {
                    "match": {
                        "content": query
                    }
                },
            }
        },
        'size': top_k
    }
        max_retries = 3  # 最大重试次数
        for attempt in range(max_retries):
            try:
                response=self.es.search(index=name, body=search_query)
                results = []
                for hit in response['hits']['hits']:
                    if hit['_score'] >= threshold:
                        results.append(hit['_source'])
                return results
            except (ConnectionError, NotFoundError) as e:
                logging.error(f"连接出现问题: {e},尝试第{attempt+1}次重试...")
                await asyncio.sleep(0.1)  # 使用异步睡眠
        return "重试次数已用完，无法连接到Elasticsearch服务。"



    def delete(self,name):
        if self.es.indices.exists(index=name):
            self.es.indices.delete(index=name)
            print(f"删除{name}索引成功")
        else:
            print(f"{name}索引不存在")

    def insert(self,name,data):
        """
        插入数据
        参数：
        name:str 索引名称，必填

        data:list 数据列表，必填，每个元素为字典，字典的key必须与索引的字段匹配，value为对应字段的值。每一条数据代表一条记录
        """ 
        actions=[]
        for item in data:
            actions.append({
            "_index":name,
            "_source":item
        })
        from elasticsearch import helpers
        success,error=helpers.bulk(self.es, actions)
        print(f"插入{len(actions)}条数据到索引{name}，成功插入{success}条数据,失败{len(error)}条数据")
    def show(self): 
        """
        获取现有的索引列表
        """
        indices=self.es.indices.get_alias(name="*")
        return list(indices.keys())
    async def search_for_ids(self,name,id_list):
        query = {"query": {
        "terms": {
            "slice_id": id_list
        }
    }
    }
        result=[]
        try:
            response = self.es.search(index=name, body=query,size=len(id_list))
            for hit in response['hits']['hits']:
                result.append(hit['_source'])
            return result
        except:
            print("查询失败请检查连接")
            return result



    def check_connect(self):
        """
        检查连接状态
        """
        if self.es.ping():
            print("Elasticsearch 连接成功")
        else:
            print("Elasticsearch 连接失败")


