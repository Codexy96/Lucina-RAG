import os
file_dir=os.path.dirname(__file__)
config_path=os.path.join(file_dir,"../../Setup/config.yaml")
class Milvus:
    """ 
    实现连接milvus,创建collection,插入数据,删除collection,搜索数据等功能。
    """
    def __init__(self):
        import yaml
        with open(config_path,"r",encoding="utf-8") as f:
            config=yaml.load(f,Loader=yaml.FullLoader)
        from pymilvus import MilvusClient,Collection
        #连接milvus
        uri=config['milvus']['uri']
        client=Milvus(uri=uri)
        self.client=client
        print("Milvus connected successfully")
    def create(self,name:str,fields:list,core_dict:dict=None):
        """
        参数：
         --name: 集合名称
         --core_dict: 向量搜索引擎设置，确定使用搜索方式和存储维度，存储维度与向量模型保持一致。例如：{'method': 'ivf_sq8','dim':768}
         method列表：
            --IVF_FLAT:高速查询，相对高召回率
            -- IVF_SQ8: 高速查询，适合有限的内存资源
            -- IVF_PQ: 极高的查询速度，极低的内存资源
            -- HNSW: 召回性能最好的方法，但需要大量内存
         --dim: 向量维度，任意，根据所选的向量模型而定
         --fileds: 字段列表，用于创建集合的字段，必须包括以下基本字段：slice_id、vector。其余字段可选，类型为char，最大长度不超过1024。
        """
        if core_dict is None:
            core_dict={'method': 'IVF_FLAT','dim':768}
        if not isinstance(core_dict,dict):
            print("core_dict only support dict type,please transform the core_dict to dict type")
            return
        self.core_dict=core_dict
        res=Collection(self.client,name,core_dict,fields).flag
        if res:
             print("collection created successfully,")
        else:
             print("please recheck the parameters and try again")
    #查看当前集合列表
    def show(self):
        collections=self.client.list_collections()
        return collections
    #插入数据
    def insert(self,name:str,data:list):
         """
         参数：
         --name: 集合名称
         -- data: 由键值对数据构成的列表，一条数据是一条记录。其中键为字段名，值是你要插入的内容，请确保格式正确，且一一对应。  
         """
         #检查数据
         sample=data[0]
         if "slice_id" not in sample or "vector" not in sample:
             print("data format error, please check the data format")
         if not isinstance(sample['vector'],list):
             print("the vector only support list type,please transform the vector to list type")
         if len(sample["vector"])!=self.core_dict['dim']:
             print("vector dimension error, please check the vector dimension")
         #插入数据
         res=self.client.insert(
             collection_name=name,
             data=data,
         )
         print(f"insert {len(data)} vectors into collection {name} successfully")
    #删除集合
    def delete(self,name:str):
        """
        删除集合
        """
        res=self.client.drop_collection(collection_name=name)
        return res
    def search(self,name:str,query_vectors:list,top_k:int):
        """
        参数：
         --name: 集合名称
         --query_vectors: 待搜索的向量列表
         --top_k: 返回结果的数量
        """
       
        #获取向量索引描述
        res=self.client.describe_index(collection_name=name,index_name="vector")
        index_type=res['index_type']
        print(res)
        if index_type=="IVF_FLAT" or index_type=="IVF_SQ8":
            nlist=res['nlist']
            self.client.get_load_state(collection_name=name)
            res=self.client.search(
            collection_name=name,
            data=query_vectors,
            limit=top_k,
            search_params={"metric_type":"COSINE","params":{"nprobe":nlist}}
        )
        elif index_type=="IVF_PQ":
            nlist=res['nlist']
            m=res['m']
            nbits=res['nbits']
            self.client.get_load_state(collection_name=name)
            res=self.client.search(
            collection_name=name,
            data=query_vectors,
            limit=top_k,
            search_params={"metric_type":"COSINE","params":{"nprobe":nlist,"m":m,"nbits":nbits}}
        )
        elif index_type=="HNSW":
            M=res['M']
            ef=res['efConstruction']
            res=self.client.search(
            collection_name=name,
            data=query_vectors,
            limit=top_k,
            search_params={"metric_type":"COSINE","params":{"ef":ef,"M":M}}
        )
        else:
            print("unsupported index type")
        return res







class Collection:
    """
    Collection class:
    milvus使用collection来存储数据，一个collection就是一张表。
    支持：
    1、一键初始化集合

    2、插入数据

    3、清空集合

    """
    def __init__(self,client,name:str,core_dict:dict,fields:list):
        """
        参数：
         --name: 集合名称
         --core_dict: 向量搜索引擎设置，确定使用搜索方式和存储维度，存储维度与向量模型保持一致。例如：{'method': 'ivf_sq8','dim':768}
         method列表：
            --IVF_FLAT:高速查询，相对高召回率
            -- IVF_SQ8: 高速查询，适合有限的内存资源
            -- IVF_PQ: 极高的查询速度，极低的内存资源
            -- HNSW: 召回性能最好的方法，但需要大量内存
         --dim: 向量维度，任意，根据所选的向量模型而定
         --fileds: 字段列表，用于创建集合的字段，必须包括以下基本字段：slice_id、vector。其余字段可选，类型为char，最大长度不超过1024。
        """
        from pymilvus import MilvusClient,DataType
        self.client=client
        #先查看是否有同名的集合
        collections=client.list_collections()
        if name in collections:
            print("collection already exists.Make sure you exactly want this collection.")
            self.flag=True
            return
        self.core_dict=core_dict
        self.name=name
        #创建纲要和索引
        index_core=core_dict['method']
        schema=MilvusClient.create_schema(
            auto_id=False,  #一定要关闭自动生成
            enable_dynamic_field=True,  #允许因为新数据集增加了字段而更新表字典 
            )
        index_params=client.prepare_index_params()
        try:
            for field in fields:
                if field=="slice_id":
                    schema.add_field(field_name="slice_id", datatype=DataType.VARCHAR, max_length=64, is_primary= True)
                    index_params.add_index(
                        field_name="slice_id")
                elif field=="vector":
                     schema.add_field(field_name="vector",datatype=DataType.FLOAT_VECTOR,dim=core_dict['dim'])
                     if index_core=="IVF_FLAT":
                          index_params.add_index(field_name="vector",index_type=index_core,params={"nlist":1024},metric_type="COSINE")
                     elif index_core=="IVF_SQ8":
                          index_params.add_index(field_name="vector",index_type=index_core,params={"nlist":1024},metric_type="COSINE")
                     elif index_core=="IVF_PQ":
                          index_params.add_index(field_name="vector",index_type=index_core,params={"nlist":1024,"m":8,"nbits":8},metric_type="COSINE")
                     elif index_core=="HNSW":
                          index_params.add_index(field_name="vector",index_type=index_core,params={"M":48,"efConstruction":500},metric_type="COSINE")
                else:
                    schema.add_field(field_name=field,datatype=DataType.VARCHAR,max_length=4096)
                    index_params.add_index(field_name=field)
            #创建集合
            print("Milvus Creating collection...")
            print(f"collection name: {name}, fields: {fields}, index_type: {index_core}, index_params: {index_params}")
            res=client.create_collection(
                collection_name=name,
                schema=schema,
                index_params=index_params
                )
            self.flag=True 
            print("Milvus collection created successfully.")
        except Exception as e:
            self.flag=False
            print("collection creation failed:",e)

    
