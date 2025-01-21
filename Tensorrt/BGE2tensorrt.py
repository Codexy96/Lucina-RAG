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
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-large')
model = AutoModelForSequenceClassification.from_pretrained(
    'BAAI/bge-reranker-large',
    device_map=device,
    torch_dtype=torch.float16,
)
model.eval()
#将pytorch模型转化为onnx引擎
#1、定义输入张量的形状信息
input_id_=torch.randint(2,1000,(1,512)).to('cuda')
attention_mask_=torch.ones(1,512).long().to('cuda')
#转化模型
import torch
torch.onnx.export(
    model, #原模型
    (input_id_.to(torch.int64),attention_mask_.to(torch.int64)), #输入张量，接受一个张量或者元组
    "./BGE-4.onnx",
    export_params=True, #是否保存模型的权重信息
    opset_version=17, #17支持INormalizationLayer，防止溢出
    do_constant_folding=True,  #是否执行常量折叠优化
    input_names=['input_ids','attention_mask'], #输入的名字
    output_names=['output'],
    dynamic_axes={
        'input_ids':{0:'batch_size',1:'sequence_length'},
        'attention_mask':{0:'batch_size',1:'sequence_length'},
        'output':{0:'batch_size'}
    }          #可变长度，在NLP中批次和序列长度都是可变长度
    
)
import tensorrt as trt
logger=trt.Logger(trt.Logger.WARNING)
trt.init_libnvinfer_plugins(logger,namespace='')
builder=trt.Builder(logger)
config=builder.create_builder_config()
config.set_flag(trt.BuilderFlag.FP16)
profile = builder.create_optimization_profile()
profile.set_shape("input_ids", (1, 512),(8, 512),(16, 512))  # 输入的最小、默认批量大小、最大批次
profile.set_shape("attention_mask",(1,512),(8,512),(16,512))
config.add_optimization_profile(profile)
config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE,1<<30)
network=builder.create_network(1<<int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
parser=trt.OnnxParser(network,logger)
success=parser.parse_from_file('autodl-tmp/BGE-4.onnx')
if not success:
    print('ERROR: Failed to parse the ONNX file.')
    exit(1)

serialized_engine=builder.build_serialized_network(network,config)
with open('./bge_engine','wb') as f:
          f.write(serialized_engine)



