
from elasticsearch import Elasticsearch, exceptions
import hashlib
import random

""" 
elasticsearch数据库管理
"""

""" 
ElasticDataset类：

包含功能如下：

创建索引：create_index

删除索引：delete_index

插入数据：insert_document

删除数据：delete_document

批量插入数据：batch_insert

批量删除数据：batch_delete

验证文档字段的类型和存在性：validate_document

"""

""" 
输入参数：

hosts: Elasticsearch集群的地址

index_name: 索引名称

index_fields: 索引字段及类型，字典类型，键为字段名，值为字段类型,依据你即将要插入的数据为准




"""
"""
ElasticDataset类：
输入index_name, index_fields, settings

如果没有制定settings，则默认设置和index_fields中的字段对齐,暂时只支持str和int类型

str:统一用text类型
int:统一用keyword类型

插入的文档内容必须使用content标识，其他字段可自定义
"""
import os
import sys
from dotenv import load_dotenv
# 获取父目录并添加到系统路径
parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)

# 加载上一级文件夹中的 .env 文件
dotenv_path = os.path.join(parent_dir, '.env')
load_dotenv(dotenv_path)

# Elasticsearch集群地址
ES_HOSTS = os.getenv('ES_HOSTS')

class ElasticDataset:
    def __init__(self, index_name,hosts=ES_HOSTS, index_fields=None,settings=None):
        self.es = Elasticsearch(hosts)
        self.index_name = index_name  # 只维护一个索引名
        if index_fields:
            self.index_fields = index_fields
        else:
            self.index_fields = {
            "source": str,
            "content": str,
            "timestamp": str
        }
        # 当前索引中存在的文档哈希值列表，用于防止重复插入
        self.existing_hashes = set()
        
        # 默认settings设置：
        """ 
        主分片数量：3
        副本数量：1
        字段：
            source：keyword
            content：text
            timestamp：date
        """
        if settings:
            self.settings = settings
        else:
            self.settings = {
            "settings": {
                "number_of_shards": 1,  # 主分片数量
                "number_of_replicas": 0   # 副本数量
            },
            "mappings": {
                "properties": {
                    field: 'text' if field_type == str   else 'keyword'  for field, field_type in self.index_fields.items()            
                }
            }
        }

    def create_index(self):
        """创建索引，设置分片、复制及映射"""
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(index=self.index_name, body=self.settings)
            print(f"索引 '{self.index_name}' 创建成功")
        else:
            print(f"索引 '{self.index_name}' 已存在")

    def delete_index(self):
        """删除索引"""
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
            print(f"索引 '{self.index_name}' 删除成功")
        else:
            print(f"索引 '{self.index_name}' 不存在")

    def validate_document(self, document):
        """验证文档字段的类型和存在性"""
        for field, expected_type in self.index_fields.items():
            if field not in document:
                print(f"字段 '{field}' 是必需的")
                return False
            if not isinstance(document[field], expected_type):
                print(f"字段 '{field}' 的类型应为 '{expected_type.__name__}'")
                return False
        return True

    def generate_hash(self, document):
        """生成文档的哈希值"""
        document_string = document['content']
        return hashlib.md5(document_string.encode('utf-8')).hexdigest()

    def insert(self, doc_id, document):
        """插入数据并进行字段验证"""
        if self.validate_document(document):
            doc_hash = self.generate_hash(document)
            if doc_hash in self.existing_hashes:
                print(f"文档 '{doc_id}' 已存在，防止重复插入")
                return

            self.es.index(index=self.index_name, id=doc_id, body=document)
            self.existing_hashes.add(doc_hash)
            print(f"文档 '{doc_id}' 插入到索引 '{self.index_name}'")
        else:
            print("文档插入失败，字段验证未通过")

    def batch_insert(self, documents):
        """批量插入数据"""
        """
        请在数据中标明doc_id字段, 否则会自动生成doc_id
        """
        actions = []
        for document in documents:
            doc_id = document.get('doc_id') if 'doc_id' in document else random.randint(len(self.existing_hashes), 1000000)
            doc_hash = self.generate_hash(document)
            if doc_hash in self.existing_hashes:
                print(f"文档 '{doc_id}' 已存在，防止重复插入")
                continue

            actions.append({
                "_index": self.index_name,
                "_id": doc_id,
                "_source": document
            })
            self.existing_hashes.add(doc_hash)

        # Execute the bulk insert
        if actions:
            success, _ = self.es.bulk(actions=actions)
            print(f"插入 {len(actions)} 条数据到索引 '{self.index_name}'，成功插入 {success} 条数据")

    def delete(self, doc_id):
        """删除数据"""
        try:
            self.es.delete(index=self.index_name, id=doc_id)
            print(f"文档 '{doc_id}' 从索引 '{self.index_name}' 删除成功")
        except exceptions.NotFoundError as e:
            print(f"删除文档 '{doc_id}' 失败: {e}")  # 返回错误信息

    def batch_delete(self, doc_ids):
        """批量删除数据"""
        actions = []
        for doc_id in doc_ids:
            actions.append({
                "_op_type": "delete",
                "_index": self.index_name,
                "_id": doc_id
            })
        if actions:
            success, failures = self.es.bulk(actions=actions)
            print(f"删除 {len(doc_ids)} 条数据从索引 '{self.index_name}'，成功删除 {success} 条数据")
            if failures:
                print("删除失败的文档 ID:", [f["_id"] for f in failures])

# 示例用法
if __name__ == '__main__':
    es_manager = ElasticDataset(hosts=['http://localhost:9200'], index_name='example_index')

    # 创建索引
    es_manager.create_index()

    # 插入文档 - 正确示例
    es_manager.insert(1, {
        'source': '测试文档',
        'content': '这是一个测试',
        'timestamp': '2023-10-01T12:00:00'  # 日期格式
    })

    # 插入文档 - 错误示例，缺少字段
    es_manager.insert(2, {
        'source': '缺少内容字段',
        'timestamp': '2023-10-01T12:00:00'  # content 字段缺失
    })

    # 插入文档 - 错误示例，字段类型不匹配
    es_manager.insert(3, {
        'title': 123,  # title 应为字符串
        'content': '这是一个测试',
        'timestamp': '2023-10-01T12:00:00'
    })

    # 批量插入文档示例
    es_manager.batch_insert([
        {'doc_id': 4, 'source': '文档4', 'content': '内容4', 'timestamp': '2023-10-02T12:00:00'},
        {'doc_id': 5, 'source': '文档5', 'content': '内容5', 'timestamp': '2023-10-02T13:00:00'},
    ])

    # 删除文档
    es_manager.delete(1)

    # 批量删除文档示例
    es_manager.batch_delete([2, 3])

    # 删除索引
    es_manager.delete_index()
