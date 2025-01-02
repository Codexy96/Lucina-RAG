import os
import yaml
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']= 'python'
file_dir=os.path.dirname(__file__)
config_path=os.path.join(file_dir,'../config.yaml')
with open(config_path, 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
os.environ['HF_ENDPOINT']=config['HF_SET']['HF_ENDPOINT']
os.environ['HF_HOME']=config['HF_SET']['HF_HOME']
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import time
model_name='BAAI/bge-m3'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    device_map=device,
    torch_dtype=torch.float16,
)
#清空缓存
if torch.cuda.is_available():
    torch.cuda.empty_cache()