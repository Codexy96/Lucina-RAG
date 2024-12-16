import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']='python'
import configparser
config = configparser.ConfigParser()
config.read('downloadconfig.ini')
file_dir=os.path.dirname(__file__)
os.environ["HF_DATASETS_CACHE"] = config['settings']['HF_DATASETS_CACHE']
os.environ["HF_HOME"] = config['settings']['HF_HOME']
os.environ["HUGGINGFACE_HUB_CACHE"] = config['settings']['HUGGINGFACE_HUB_CACHE']
os.environ["TRANSFORMERS_CACHE"] = config['settings']['TRANSFORMERS_CACHE']
os.environ["HF_ENDPOINT"] =config['settings']['HF_ENDPOINT']
os.environ["XDG_CACHE_HOME"] =  config['settings']['XDG_CACHE_HOME']
import torch
from transformers import AutoTokenizer,AutoModel
import time
model_name='maidalun1020/bce-reranker-base_v1'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(
    model_name,
    device_map=device,
    torch_dtype=torch.float16,
)
#清空缓存
if torch.cuda.is_available():
    torch.cuda.empty_cache()