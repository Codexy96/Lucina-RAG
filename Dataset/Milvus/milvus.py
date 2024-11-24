import os
import sys
from dotenv import load_dotenv
# 获取父目录并添加到系统路径
parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)

# 加载上一级文件夹中的 .env 文件
dotenv_path = os.path.join(parent_dir, '.env')
load_dotenv(dotenv_path)
from pymilvus import MilvusClient,DataType
""" 
输入参数：
collection_name: 集合名称
fields: 字段列表，默认值为 ["source", "vector","content","timestamp"]
dim: 向量维度，默认值为 512
向量字段使用FLOAT_VECTOR类型，字符串字段使用VARCHAR类型，默认最大长度为250


向量字段默认索引建立方式：
IVF_FLAT
COSINE
分簇：256
drop_ratio_bulid=0.2
drop_ratio_search=0.2

插入数据是jsonlene格式，字段名和类型必须与定义的字段一致
"""
class MilvusDataset:
    def __init__(self,collection_name,fields=None,dim=512,max_length=250):
        char_len=3*max_length
        self.client=MilvusClient(uri=os.getenv("MILVUS_URI"))
        self.collection_name = collection_name  # 设置集合名称
        self.dim = dim  # 设置向量维度
        if fields:
            self.fields = fields  # 设置字段
        else:
            self.fields = {"source": DataType.VARCHAR, "vector": DataType.FLOAT_VECTOR, "content": DataType.STRING, "timestamp": DataType.VARCHAR}  # 默认字段
        # 定义集合的 Schema
        self.schema =MilvusClient.create_schema(
    auto_id=True,
    enable_dynamic_fields=True,
)
        #设计索引用于检索
        self.index_params=self.client.prepare_index_params()
        
        for field_name, field_type in self.fields.items():
            if field_type == DataType.FLOAT_VECTOR:
                self.schema.add_field(field_name=field_name, field_type=field_type, dim=self.dim)
                self.index_params.add_index(field_name=field_name,index_type="IVF_FLAT",drop_ratio_bulid=0.2,drop_ratio_search=0.2,metric_type="COSINE",params={"nlist": 256})
            else:
                self.schema.add_field(field_name=field_name, field_type=field_type, max_length=char_len)
                self.index_params.add_index(field_name=field_name)
        
        


        # 创建集合
        self.create()
    def create(self):
        """创建集合（如果已存在，先删除再创建）"""
        try:
            #先卸载
            self.client.drop_collection(self.collection_name)  # 删除之前的集合
            print(f"集合 '{self.collection_name}' 已被删除。")
        except Exception as e:
            print(f"删除集合时出现错误: {e}")

        # 创建新的集合
        self.client.create_collection(collection_name=self.collection_name, schema=self.schema)
        print(f"集合 '{self.collection_name}' 创建成功。")

    def insert(self, insert_data):
        """向集合插入数据"""
        if not insert_data:
            print("插入数据不能为空。")
            return
        try:
            res = self.client.insert(collection_name=self.collection_name, data=insert_data)
            print(f"成功插入 {len(res)} 条数据到 '{self.collection_name}' 集合中。")
        except Exception as e:
            print(f"插入数据时发生错误: {e}")

    def delete_collection(self):
        """删除集合"""
        try:
            self.client.drop_collection(self.collection_name)
            print(f"集合 '{self.collection_name}' 已删除。")
        except Exception as e:
            print(f"删除集合时出现错误: {e}")

    def list_collections(self):
        """列出所有集合"""
        collections = self.client.list_collections()
        return collections

# 示例用法
if __name__ == '__main__':
    dataset = MilvusDataset(collection_name='law')

    # 插入示例数据
    insert_data = [
        {"FULL_TEXT_HASH": "hash_1", "summary_vector": [0.1] * 512},
        {"FULL_TEXT_HASH": "hash_2", "summary_vector": [0.2] * 512}
    ]
    dataset.insert(insert_data)

    # 列出所有集合
    all_collections = dataset.list_collections()
    print("当前集合名称:", all_collections)

    # 删除集合
    dataset.delete_collection()

