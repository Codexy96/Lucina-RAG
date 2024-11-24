# -*- coding: utf-8 -*-
#https://github.com/microsoft/LLMLingua/blob/main/DOCUMENT.md
from llmlingua import PromptCompressor

llm_lingua = PromptCompressor(
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    use_llmlingua2=True,
)

async def  compress_content(content,rate=0.7):
    compressed_prompt = llm_lingua.compress_prompt(
        content,
        rate=rate,
        force_tokens=["|", ".", "?", "\n", '。'],
        drop_consecutive=True,
        rank_method="longllmlingua",
    )
    
    return compressed_prompt['compressed_prompt']

async def compress_content_list(search_list,rate=0.5):
    result=""
    for i in range(len(search_list)):
        content = search_list[i]["content"]
        compressed_prompt = await compress_content(content,rate=rate)
        result += compressed_prompt + "\n\n"
        
    return result





"""
context=""
为了加快地方政府债券发行使用进度，保障重点领域重大项目资金需求，发挥政府债券资金对稳投资、扩内需、补短板的重要作用，推动经济运行持续健康发展，第十四届全国人民代表大会常务委员会第六次会议决定：授权国务院在授权期限内，在当年新增地方政府债务限额（包括一般债务限额和专项债务限额）的60%以内，提前下达下一年度新增地方政府债务限额。授权期限为决定公布之日至2027年12月31日。
按照党中央决策部署，根据经济形势和宏观调控需要，国务院在每年第四季度确定并提前下达下一年度部分新增地方政府债务限额的具体额度。提前下达的分省、自治区、直辖市的情况，及时报全国人民代表大会常务委员会备案。
各省、自治区、直辖市人民政府按照国务院批准的提前下达的新增政府债务限额编制预算，经本级人民代表大会批准后执行，并及时向下级人民政府下达新增政府债务限额。下级人民政府依照经批准的限额提出本地区当年政府债务举借和使用计划，列入预算调整方案，报本级人民代表大会常务委员会批准，报省级政府备案并由省级政府代为举借。
在每年国务院提请全国人民代表大会审查批准的预算报告和草案中，应当报告和反映提前下达部分新增地方政府债务限额的规模和分省、自治区、直辖市下达的情况。预算报告和草案经全国人民代表大会批准后，国务院及时将批准的地方政府债务限额下达各省、自治区、直辖市，地方政府新增债务规模应当按照批准的预算执行。
国务院应当进一步健全完善地方政府债务管理制度，采取有效措施，统筹发展和安全，确保地方政府债务余额不得突破批准的限额，防范和化解地方政府债务风险，更好发挥政府债务对经济社会发展的重要作用。国务院地方政府债务主管部门及相关部门要督促地方加强项目储备和前期论证，优化项目申报、审批流程，保证审批质量，提升审批效率，确保地方政府债券发行后，资金及时使用，提高资金使用绩效。
本决定自公布之日起施行。
""

question = "下级政府债务的办理流程是什么？"


# 2000 Compression
compressed_prompt = llm_lingua.compress_prompt(
    context,
    rate=0.33, #压缩率
    force_tokens=["|", ".", "?", "\n",'。'],
    drop_consecutive=True,
)
import json

prompt = "\n\n".join([compressed_prompt["compressed_prompt"], question])
print(prompt)
""" 
async def main():
    context="""为了加快地方政府债券发行使用进度，保障重点领域重大项目资金需求，发挥政府债券资金对稳投资、扩内需、补短板的重要作用，推动经济运行持续健康发展，第十四届全国人民代表大会常务委员会第六次会议决定：授权国务院在授权期限内，在当年新增地方政府债务限额（包括一般债务限额和专项债务限额）的60%以内，提前下达下一年度新增地方政府债务限额。授权期限为决定公布之日至2027年12月31日。
按照党中央决策部署，根据经济形势和宏观调控需要，国务院在每年第四季度确定并提前下达下一年度部分新增地方政府债务限额的具体额度。提前下达的分省、自治区、直辖市的情况，及时报全国人民代表大会常务委员会备案。
各省、自治区、直辖市人民政府按照国务院批准的提前下达的新增政府债务限额编制预算，经本级人民代表大会批准后执行，并及时向下级人民政府下达新增政府债务限额。下级人民政府依照经批准的限额提出本地区当年政府债务举借和使用计划，列入预算调整方案，报本级人民代表大会常务委员会批准，报省级政府备案并由省级政府代为举借。
在每年国务院提请全国人民代表大会审查批准的预算报告和草案中，应当报告和反映提前下达部分新增地方政府债务限额的规模和分省、自治区、直辖市下达的情况。预算报告和草案经全国人民代表大会批准后，国务院及时将批准的地方政府债务限额下达各省、自治区、直辖市，地方政府新增债务规模应当按照批准的预算执行。
国务院应当进一步健全完善地方政府债务管理制度，采取有效措施，统筹发展和安全，确保地方政府债务余额不得突破批准的限额，防范和化解地方政府债务风险，更好发挥政府债务对经济社会发展的重要作用。国务院地方政府债务主管部门及相关部门要督促地方加强项目储备和前期论证，优化项目申报、审批流程，保证审批质量，提升审批效率，确保地方政府债券发行后，资金及时使用，提高资金使用绩效。
本决定自公布之日起施行。
"""
    question = "下级政府债务的办理流程是什么？"
    search_list = [
        {"content":context},
        {"content":"""应当征求国务院野生动物保护主管部门意见涉及地方重点保护野生动物禁止野生动物收容救护为名买卖野生动物制品 第十六条  
国家加强野生动物遗传资源保护,濒危野生动物实施抢救性保护"""}
    ]
    start_time = time.time()
    search_list = await compress_content_list(search_list,rate=0.7)
    end_time = time.time()
    print(json.dumps(search_list,ensure_ascii=False,indent=4))
    print("Time used:", end_time - start_time)
if __name__ == "__main__":
    import time
    import asyncio
    import json
    asyncio.run(main())
    

