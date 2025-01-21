import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']= 'python'
import configparser
config = configparser.ConfigParser()
config.read('downloadconfig.ini')
file_dir=os.path.dirname(__file__)
os.environ["HF_DATASETS_CACHE"] = os.path.join(file_dir, config['settings']['HF_DATASETS_CACHE'])
os.environ["HF_HOME"] = os.path.join(file_dir, config['settings']['HF_HOME'])
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(file_dir, config['settings']['HUGGINGFACE_HUB_CACHE'])
os.environ["TRANSFORMERS_CACHE"] = os.path.join(file_dir, config['settings']['TRANSFORMERS_CACHE'])
os.environ["HF_ENDPOINT"] =config['settings']['HF_ENDPOINT']
os.environ["XDG_CACHE_HOME"] = os.path.join(file_dir, config['settings']['XDG_CACHE_HOME'])
from transformers import AutoModel, AutoTokenizer
import torch
tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-embedding-base_v1')
model = AutoModel.from_pretrained('maidalun1020/bce-embedding-base_v1',torch_dtype=torch.float16)
print("model and tokenizer loaded successfully")
