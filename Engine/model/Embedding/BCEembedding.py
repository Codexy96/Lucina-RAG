import os
import configparser
file_dir=os.path.dirname(__file__)
config = configparser.ConfigParser()
config.read(os.path.join(file_dir,'cache.ini'))
os.environ["HF_DATASETS_CACHE"] =config['settings']['HF_DATASETS_CACHE']
os.environ["HF_HOME"] =  config['settings']['HF_HOME']
os.environ["HUGGINGFACE_HUB_CACHE"] =  config['settings']['HUGGINGFACE_HUB_CACHE']
os.environ["TRANSFORMERS_CACHE"] =config['settings']['TRANSFORMERS_CACHE']
os.environ["HF_ENDPOINT"] =config['settings']['HF_ENDPOINT']
os.environ["XDG_CACHE_HOME"] =config['settings']['XDG_CACHE_HOME']
from transformers import AutoModel, AutoTokenizer
# list of sentences
#sentences = ['sentence_0', 'sentence_1', ...]

# init model and tokenizer
import torch
device = "cuda" if torch.cuda.is_available() else "cpu" # if no GPU, set "cpu"
tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-embedding-base_v1',cache_dir=config['settings']['TRANSFORMERS_CACHE'])
model = AutoModel.from_pretrained('maidalun1020/bce-embedding-base_v1',torch_dtype=torch.float16,device_map=device,cache_dir= config['settings']['TRANSFORMERS_CACHE'])

def embedding(sentences):
    inputs=tokenizer(sentences, padding=True, truncation=True, max_length=512, return_tensors="pt")
    inputs_on_device = {k: v.to(device) for k, v in inputs.items()}
    outputs = model(**inputs_on_device, return_dict=True)
    embeddings = outputs.last_hidden_state[:, 0]  # cls pooler
    embeddings = embeddings
    return embeddings.tolist()



class BCEembedding:
    def __init__(self):
        self.dim=768
        self.name='BCEembedding pytorch'
    def __call__(self,text_list):
        return embedding(text_list)