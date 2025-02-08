#----------------------------------

#逻辑1，输入一段文字，返回topk的向量:图片地址路径键值对，可以选择
#逻辑2，实时匹配，输入文本，从图片候选中选择最接近的图片进行匹配,只会匹配一个


#----------------------------------

from MultiEngine import Engine 
class ImageSearch:
    #初始化
    def __init__(self,root_path=None,dataset_name=None,engine_class=Engine):
        """
        root_path: 图片根目录，如果是云端服务，则为云端路径
        dataset_name:数据集名称，当使用云端服务时，需要指定数据集名称。如果是本地服务可不填，默认为图片根目录最后一级的名称
        """
        import os
        if root_path==None and dataset_name==None:
            raise ValueError("请至少指定root_path")
        if root_path!=None:
            dataset_name=os.path.basename(root_path)
        self.modal_engine=engine_class(root_path=root_path,dataset_name=dataset_name)

    async def search(self,text,partition_name=None,top_k=10,output_fields=["vector","path"]):
        """
        text:输入文本
        partition_name: 切片名称
        top_k:返回topk的向量
        output_fields:返回字段,应包括向量字段和图片地址片段，向量字段在前，图片地址片段在后，如默认的["vector","path"]
        return:向量:path:vector键值对 （list无法成为键）
        目前仅支持单批次文本搜索
        """
        if partition_name==None:
            partition_name=self.modal_engine.dataset_name
        result=await self.modal_engine.search4image(text,partition_name=partition_name,top_k=top_k,output_fields=output_fields)
        self.images_kv=result
        return result
    async def match(self,text,top_k=1,threshold=0.5):
        """
        text:输入文本
        top_k:返回topk的向量
        threshold:阈值 
        return 图片列表
        目前仅支持单批次文本搜索
        在使用match之前，必须先运行search方法，实例将图片地址键值对赋值给self.images_kv属性
        """
        import os
        if self.images_kv==None:
            raise ValueError("请先运行search方法")
        if len(self.images_kv)==0:
            #图片候选列用尽
            return []
        result=await self.modal_engine.match4image(text,images_kv=self.images_kv,top_k=top_k,threshold=threshold)
        for i,item in enumerate(result):
            if isinstance(item,str):
                del self.images_kv[item]
                result[i]=os.path.join(self.modal_engine.root_path,item)

        return result 
    def reset(self):
        """
        重置实例
        """
        self.images_kv=None
    

#测试
if __name__=="__main__":
    """
    文件夹下只有图片时，dataset name与partition name 一致

    """
    import asyncio
    image_search=ImageSearch(root_path="/root/autodl-tmp/images")
    result=asyncio.run(image_search.search(text="书籍",partition_name="images",top_k=10))
    match_result=asyncio.run(image_search.match(text="报纸",top_k=1,threshold=0.2))
    print("return the match result is:",match_result)