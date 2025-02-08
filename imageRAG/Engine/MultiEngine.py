#---------------------------------

##############多模态向量检索引擎#############

#---------------------------------
import os
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from RAG.Engine.Dataset.milvus import Milvus,Partition
from script.ImageRAG.Engine.MultiEmbedding import AsyncEmbedding as Embedding
model=Embedding()
class Engine:
    def __init__(self,model=model,root_path=None,dataset_name=None):
        self.model=model  #多模态向量模型
        if root_path is None:
            root_path=""
        self.root_path=root_path  #图片根目录路径
        self.dataset_name=dataset_name  #向量库名
        self.model_name=self.model.name 
        self.vector_database=Partition(client=Milvus().client,collection_name=self.dataset_name)
        self.mode="COSINE" #即时搜索图片时所使用的计算方式
    async def search4image(self,text,partition_name,top_k=10,output_fields=["vector","path"]):
        """
        --text: 搜索query
        --partition_name: 分片名称，如何只有根目录一级目录，dataset_name=partition_name=root_name
        --top_k: 返回的最佳匹配个数
        --result: 返回path:vector的字典
        --output_fields: 输出字段，默认为["vector","path"]
        """
        import os
        query_vectors=await self.model.encode_text(text)
        #partition返回的结果为字典列表，其中的键包括：vector为向量，path为图片路径
        result=self.vector_database.search(partition_name=partition_name,query_vectors=query_vectors,top_k=top_k,output_fields=output_fields)
        #提取vector和图片路径path构成字典，返回字典列表
        #[{'path': 'xxx.jpg','vector': [0.1,0.2,0.3,0.4]}]
        return_result={item['entity'][output_fields[1]]:item['entity'][output_fields[0]] for res in result  for  item in res   }
        return return_result
    async def match4image(self,text,images_kv=None,top_k=1,threshold=0.5):
        """
        --text: 待匹配的文本
        --images_kv: 开始候选列中的images_kv，格式为{image_vector:image_path}
        --top_k: 返回的最佳匹配个数
        --threshold: 阈值，按照距离进行过滤。
        --path_result: 返回图片链接list
        #目前仅支持单批次
        """
        import numpy as np
        import numpy as np
        if images_kv is None or images_kv=={}:
            return []
        query_vectors=await self.model.encode_text(text)
        #直接在缓存中进行向量搜索
        image_vectors=list(images_kv.values())
        image_paths=list(images_kv.keys())
        image_vectors=np.array(image_vectors)
        #计算余弦距离
        dists=np.dot((query_vectors/np.linalg.norm(query_vectors,axis=1,keepdims=True)),(image_vectors/np.linalg.norm(image_vectors,axis=1,keepdims=True)).T)
        #形状[1,top_search_k]
        #根据距离降序排序，取top_k个,这里只取一个批次
        dists=dists[0]
        indices=np.argsort(dists)[::-1]
        print(indices)
        #根据阈值过滤
        path_result=[]
        for i in indices:
            if dists[i]<threshold or len(path_result)==top_k:
                break
            path_result.append(image_paths[i])
        return path_result
        



