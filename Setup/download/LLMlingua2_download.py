import os
import yaml
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION']= 'python'
file_dir=os.path.dirname(__file__)
config_path=os.path.join(file_dir,'../config.yaml')
with open(config_path, 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
os.environ['HF_ENDPOINT']=config['HF_SET']['HF_ENDPOINT']
os.environ['HF_HOME']=config['HF_SET']['HF_HOME']
from llmlingua import PromptCompressor
llm_lingua = PromptCompressor(
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    use_llmlingua2=True,
)
import torch 
if torch.cuda.is_available():
    torch.cuda.empty_cache()