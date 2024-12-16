import os
import os
import configparser
config = configparser.ConfigParser()
file_dir=os.path.dirname(__file__)
config.read(os.path.join(file_dir,'cache.ini'))
os.environ["HF_HOME"] =config['settings']['HF_HOME']
os.environ["HF_ENDPOINT"] =config['settings']['HF_ENDPOINT']
def embedding(text_list,tokenizer,engine):
    """
    输入文本列表，返回对应的embedding列表 
    """
    import pycuda.driver as cuda
    import pycuda.autoinit
    import numpy as np
    context=engine.create_execution_context()
    inputs = tokenizer(text_list, padding=True, truncation=True, max_length=520, return_tensors="pt")
    inputs_np = {k: v.detach().numpy() for k, v in inputs.items()}
    batch_size,seq_len=inputs_np['input_ids'].shape
    context.set_input_shape('attention_mask', (batch_size,seq_len))
    context.set_input_shape('input_ids', (batch_size,seq_len))
    last_hidden_state=np.empty((batch_size,seq_len,768),dtype=np.float32)
    pooler_output=np.empty((batch_size,768),dtype=np.float32)
    d_input_ids=cuda.mem_alloc(inputs_np['input_ids'].nbytes)
    d_input_mask=cuda.mem_alloc(inputs_np['attention_mask'].nbytes)
    d_last_hidden_state=cuda.mem_alloc(last_hidden_state.nbytes)
    d_pooler_output=cuda.mem_alloc(pooler_output.nbytes)
    stream=cuda.Stream()
    cuda.memcpy_htod_async(d_input_ids,inputs_np['input_ids'],stream)
    cuda.memcpy_htod_async(d_input_mask,inputs_np['attention_mask'],stream)
    context.set_tensor_address('input_ids', int(d_input_ids))
    context.set_tensor_address('attention_mask',int(d_input_mask))
    context.set_tensor_address('last_hidden_state', int(d_last_hidden_state))
    context.set_tensor_address('pooler_output', int(d_pooler_output))
    bindings = [int(d_input_ids),int(d_input_mask),int(d_last_hidden_state),int(d_pooler_output)]
    context.execute_v2(bindings)
    cuda.memcpy_dtoh(last_hidden_state,d_last_hidden_state)
    stream.synchronize()
    embeddings=last_hidden_state[:,0]
    return embeddings.tolist()

class BCEembedding:
    def __init__(self):
        import   torch
        #读取tensorrt引擎
        import tensorrt as trt
        logger=trt.Logger(trt.Logger.INFO)
        runtime=trt.Runtime(logger)
        trt.init_libnvinfer_plugins(logger,'')
        from transformers import AutoTokenizer
        #file_path=os.path.join(os.path.dirname(__file__),'engine/BCEembedding_engine')
        cache_dir=config['settings']['HF_HOME']
        print(cache_dir)
        self.tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-embedding-base_v1',cache_dir=cache_dir)
        with open('/root/autodl-tmp/tensorrt/BCEembedding_engine','rb') as f:
             serialized_engine=f.read()
        self.engine=runtime.deserialize_cuda_engine(serialized_engine)
        self.device='cuda' if torch.cuda.is_available() else 'cpu'
        import asyncio
        self.dim=768
        self.name='BCEembedding'
    def __call__(self,text_list):
        return embedding(text_list,self.tokenizer,self.engine)

if __name__ == '__main__':
    text_list=['你好，我是RAG。']
    bce=BCEembedding()
    embeddings=bce(text_list)
    print(embeddings)
