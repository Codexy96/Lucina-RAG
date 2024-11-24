from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
 # 加载模型和分词器
model_name="jiangchengchengNLP/qwen_0.5B_instruct_law_summarize"
model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
    )
tokenizer = AutoTokenizer.from_pretrained(model_name)
def generate_summary(content):
    # 准备消息格式
    messages = [
        {"role": "system", "content": "你是法律小助手，你的任务是将用户输入的内容整理成一份摘要"},
        {"role": "user", "content": content}
    ]
    
    # 应用聊天模板
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # 生成模型输入
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    # 生成摘要
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512
    )
    
    # 解码生成的id
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return response


