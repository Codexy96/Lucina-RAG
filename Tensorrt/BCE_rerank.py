import os
os.environ['HF_ENDPOINT']='https://hf-mirror.com'
#CUDA_VISIBLE_DEVICES=0
#os.environ['CUDA_VISIBLE_DEVICES']='0'
#读取tensorrt引擎
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import time
file_path ='/root/RAG/Rerank/model'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-reranker-base_v1',cache_dir=file_path)
import tensorrt as trt
file_path=os.path.join(os.path.dirname(__file__),'engine/bce_rerank_100k_8G_engine')
logger=trt.Logger(trt.Logger.INFO)
runtime=trt.Runtime(logger)
trt.init_libnvinfer_plugins(logger,'')
with open(file_path,'rb') as f:
    serialized_engine=f.read()
    engine=runtime.deserialize_cuda_engine(serialized_engine)
import numpy as np
import asyncio


def rerank(query, search_json,top_k=10):
    """
    输入参数：
    query: 输入的query
    search_json:输入的json数据，其中待排序的文本必须使用content字段表示
    top_k:重排序后返回的最前面的结果数
    """
    # 初始化分数列表
    import pycuda.driver as cuda
    import pycuda.autoinit
    context=engine.create_execution_context()
    scores = []
    pairs = [[query,item['content']] for item in search_json]
    inputs= tokenizer(pairs, padding='max_length', truncation=True, return_tensors='pt', max_length=512)
    inputs_np = {k: v.detach().numpy() for k, v in inputs.items()}
    input_ids=inputs_np['input_ids']
    attention_mask=inputs_np['attention_mask']
    batch_size,seq_len=inputs_np['input_ids'].shape
    context.set_input_shape('attention_mask', (batch_size,seq_len))
    context.set_input_shape('input_ids', (batch_size,seq_len))
    output=np.empty((batch_size,1),dtype=np.float32)
    d_input_ids=cuda.mem_alloc(input_ids.nbytes)
    d_input_mask=cuda.mem_alloc(attention_mask.nbytes)
    d_pooler_output=cuda.mem_alloc(output.nbytes)
    context.set_tensor_address('input_ids', int(d_input_ids))
    context.set_tensor_address('attention_mask',int(d_input_mask))
    context.set_tensor_address('output', int(d_pooler_output))
    stream=cuda.Stream()
    cuda.memcpy_htod_async(d_input_ids,input_ids,stream)
    cuda.memcpy_htod_async(d_input_mask,attention_mask,stream)
    bindings = [int(d_input_ids),int(d_input_mask),int(d_pooler_output)]
    context.execute_v2(bindings)
    cuda.memcpy_dtoh(output,d_pooler_output)
    stream.synchronize()
    scores=output.squeeze()
    scores = torch.from_numpy(scores)
    _, sorted_indices = torch.sort(scores, descending=True)
    sorted_result= [search_json[i] for i in sorted_indices[:top_k]]
    return sorted_result


