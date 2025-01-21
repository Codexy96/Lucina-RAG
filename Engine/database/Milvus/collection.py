import os
file_dir=os.path.dirname(__file__)

class Collection:
    """
    Collection class:
    milvus使用collection来存储数据，一个collection就是一张表。
    支持：
    1、一键初始化集合

    2、插入数据

    3、清空集合

    """
    def __init__(self,name:str,core_dict:dict,fields:list):
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
        import configparser
        config=configparser.ConfigParser()
        config.read(os.path.join(file_dir,"config.ini"))
        client=MilvusClient(uri=config.get("milvus","uri"))
        self.client=client
        self.core_dict=core_dict
        self.name=name
        #创建纲要和索引
        index_core=core_dict['method']
        schema=MilvusClient.Create_schema(
            auto_id=True,  #启用自动生成id
            enable_dynamic_field=True,  #允许因为新数据集增加了字段而更新表字典 
            )
        index_params=client.prepare_index_params()
        for field in fields:
            if field=="slice_id":
              schema.add_field(field_name="slice_id", datatype=DataType.VARCHAR, max_length=64, is_primary= True)
              index_params.add_index(
                  field_name="slice_id"
              )
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
            schema.add_field(field_name=field,dataType=DataType.VARCHAR,max_length=4096)
            index_params.add_index(field_name=field)
        #创建集合
        try:
            client.create_collection(
                collection_name=name,
                schema=schema,
                index_params=index_params
                )
            print("collection created successfully")
        except Exception as e:
            print("collection creation failed:",e)

    

        
        
       

