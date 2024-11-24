import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import time

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-large')
model = AutoModelForSequenceClassification.from_pretrained(
    'BAAI/bge-reranker-large',
    device_map=device,
    torch_dtype=torch.float16,
)
model.eval()

def rerank(query, search_json,top_k=10):
    # 初始化分数列表
    scores = []
    pairs = [[query,item['content']] for item in search_json]
    
    try:
        with torch.no_grad():
            output_ids = tokenizer(pairs, padding='max_length', truncation=True, return_tensors='pt', max_length=512)
            input_ids, attention_mask = output_ids['input_ids'], output_ids['attention_mask']
            scores = model(input_ids.to(device), attention_mask.to(device), return_dict=True).logits.view(-1, ).float()
        #根据得分进行重排序
        _, sorted_indices = torch.sort(scores, descending=True)
        sorted_result= [search_json[i] for i in sorted_indices[:top_k]]
        return sorted_result
    except Exception as e:
        print("发生错误:", str(e))
        return None  # 返回None表示发生了错误

# 示例调用
if __name__ == "__main__":
    query = "什么是熊猫？"
    search_json = [
        {"content": "熊猫是一种哺乳动物，体长约1.5米，体重约300千克，是世界上最受欢迎的宠物之一。", "url": "https://baike.baidu.com/item/%E7%86%8A%E7%8C%AB/120279"},
        {"content": "熊猫是一种哺乳动物，体长约1.5米，体重约300千克，是世界上最受欢迎的宠物之一。", "url": "https://baike.baidu.com/item/%E7%86%8A%E7%8C%AB/120279"},
        {"content": "熊猫是一种哺乳动物，体长约1.5米，体重约300千克，是世界上最受欢迎的宠物之一。", "url": "https://baike.baidu.com/item/%E7%86%8A%E7%8C%AB/120279"}
    ]
    
    result = rerank(query, search_json)
    if result is not None:
        print("排序后结果:", result)
    else:
        print("评分失败，检查错误信息。")


