import os
import yaml
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']= 'python'
file_dir=os.path.dirname(__file__)
config_path=os.path.join(file_dir,'../config.yaml')
with open(config_path, 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
os.environ['HF_ENDPOINT']=config['HF_SET']['HF_ENDPOINT']
os.environ['HF_HOME']=config['HF_SET']['HF_HOME']
from transformers import AutoModel, AutoTokenizer
import torch
tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-embedding-base_v1')
model = AutoModel.from_pretrained('maidalun1020/bce-embedding-base_v1',torch_dtype=torch.float16)
print("model and tokenizer loaded successfully")

