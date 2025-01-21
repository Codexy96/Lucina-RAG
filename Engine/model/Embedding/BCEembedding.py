import os
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
file_dir=os.path.dirname(__file__)
os.environ["HF_DATASETS_CACHE"] = os.path.join(file_dir, config['settings']['HF_DATASETS_CACHE'])
os.environ["HF_HOME"] = os.path.join(file_dir, config['settings']['HF_HOME'])
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(file_dir, config['settings']['HUGGINGFACE_HUB_CACHE'])
os.environ["TRANSFORMERS_CACHE"] = os.path.join(file_dir, config['settings']['TRANSFORMERS_CACHE'])
os.environ["HF_ENDPOINT"] = os.path.join(file_dir, config['settings']['HF_ENDPOINT'])
os.environ["XDG_CACHE_HOME"] = os.path.join(file_dir, config['settings']['XDG_CACHE_HOME'])
from transformers import AutoModel, AutoTokenizer
# list of sentences
#sentences = ['sentence_0', 'sentence_1', ...]

# init model and tokenizer
import torch
device = "cuda" if torch.cuda.is_available() else "cpu" # if no GPU, set "cpu"
tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-embedding-base_v1',cache_dir=os.path.join(file_dir, config['settings']['TRANSFORMERS_CACHE']))
model = AutoModel.from_pretrained('maidalun1020/bce-embedding-base_v1',torch_dtype=torch.float16,device_map=device,cache_dir=os.path.join(file_dir, config['settings']['TRANSFORMERS_CACHE']))

def embedding(sentences: list[str]):
    inputs=tokenizer(sentences, padding=True, truncation=True, max_length=512, return_tensors="pt")
    inputs_on_device = {k: v.to(device) for k, v in inputs.items()}
    outputs = model(**inputs_on_device, return_dict=True)
    embeddings = outputs.last_hidden_state[:, 0]  # cls pooler
    embeddings = embeddings / embeddings.norm(dim=1, keepdim=True) 
    return embeddings.tolist()
