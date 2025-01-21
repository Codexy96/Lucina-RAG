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
import torch
tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-embedding-base_v1',cache_dir=config['settings']['TRANSFORMERS_CACHE'])
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = AutoModel.from_pretrained('maidalun1020/bce-embedding-base_v1',cache_dir=config['settings']['TRANSFORMERS_CACHE'],torch_dtype=torch.float16,device_map=device)
model.eval()
# 将 PyTorch 模型转化为 ONNX 引擎
# 1、定义输入张量的形状信息
import numpy as np
import torch

# 创建输入张量
input_id_ = torch.randint(2, 1000, (1, 512),dtype=torch.int64).to(device)  # 在 GPU 上创建 input_ids
attention_mask_ = torch.ones((1, 512), dtype=torch.int64).to(device)  # 正确创建 attention_mask 并转到 GPU

# 转化模型
#检查engine文件夹是否存在
if not os.path.exists('../engine'):
    os.makedirs('../engine')
#检查onnx文件夹是否存在
if not os.path.exists('../engine/onnx'):
      os.makedirs('../engine/onnx')
torch.onnx.export(
    model,  # 原模型
    (input_id_, attention_mask_),  # 输入张量，接受一个张量或者元组
    "../engine/onnx/BCEembedding.onnx",
    export_params=True,  # 是否保存模型的权重信息
    opset_version=17,  # 17支持 INormalizationLayer，防止溢出
    do_constant_folding=True,  # 是否执行常量折叠优化
    input_names=['input_ids', 'attention_mask'],  # 输入的名字
    output_names=['last_hidden_state', 'pooler_output'],  # 输出的名字
    dynamic_axes={
        'input_ids': {0: 'batch_size', 1: 'sequence_length'},
        'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
        'last_hidden_state': {0: 'batch_size', 1: 'sequence_length'},
        'pooler_output': {0: 'batch_size'},
    }  # 可变长度，在 NLP 中批次和序列长度都是可变长度
)
import tensorrt as trt
logger=trt.Logger(trt.Logger.WARNING)
trt.init_libnvinfer_plugins(logger,namespace='')
builder=trt.Builder(logger)
config=builder.create_builder_config()
config.set_flag(trt.BuilderFlag.FP16)
network = builder.create_network()
profile = builder.create_optimization_profile()
profile.set_shape("input_ids", (1, 1),(4, 256),(8, 512))  # 输入的最小、默认批量大小、最大批次
profile.set_shape("attention_mask",(1,1),(4,256),(8,512))
config.add_optimization_profile(profile)
config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE,1<<30)
parser=trt.OnnxParser(network,logger)
success=parser.parse_from_file('../engine/onnx/BCEembedding.onnx')
if not success:
    print("ERROR: Failed to parse the ONNX file")
    exit(1)
serialized_engine=builder.build_serialized_network(network,config)
with open('../engine/BCEembedding_engine','wb') as f:
          f.write(serialized_engine)
