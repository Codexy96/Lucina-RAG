@app.post("/ask")
async def ask_query(query: Query):
    #意图识别
    result=zhipullm.response(
        messages=[
            {'role':'system','content':"""
        你现在有一个知识完备的外接知识库
       判断用户输入的问题能否使用你现有的知识进行回答。如果可以，请直接返回"可以"。
       你可以回答的问题有：
             1、闲聊
             2、简单名词的定义描述
        你尽量不要去回答的有：
             1、职业规划的咨询
             2、真实案例的剖析
             3、现实场景中的考公、考研、考证、工作等问题
             4、有关公司、国家、组织的相关问题
       如果不能，请直接返回"抱歉，我无法生成，需要外部知识库协助"
    请不要向用户透露你判断的过程。
      """},
            {'role': 'user', 'content': query.q}
        ],
        stream=True,
    )
    content=""
    for chunk in result:
        content+=chunk
    if '可以' in content:
        response=zhipullm.response(
            messages=[
            {'role': 'system', 'content':"""你是lucina, 擅长16岁到30岁的人们的职业规划，提供行业情形一手资讯和就业、考公、考研建议，和定制化职业规划、个人发展指导服务。
             """},
             {'role': 'user', 'content': query.q}],
             stream=True,
        )
        
        return  StreamingResponse(response, media_type='text/plain')
    try:
        # 执行混合搜索任务
        mix_search_result=await kb.search(name='job',query=query.q,keyword_threshold=5,top_k=20,top_e=20)
        #先将混合搜索结果重排序
        rerank_max_search_result=await rerank(query.q,mix_search_result,top_k=20)
        #压缩内容
        compress_mix_content=await compress_content_list(rerank_max_search_result)
        # 联网搜索
        web_search_result=fetch_search_results(query.q+"数据公开",top_k=40)
        rerank_web_search_result=await rerank(query.q,web_search_result,top_k=20)
        compress_web_content=await compress_content_list(rerank_web_search_result)
        # 合并内容
        total_content=compress_mix_content+compress_web_content
        messages=[
            {'role':'system','content':system_prompt.format(text="\n".join(total_content))},
            {'role':'user','content':query.q}
        ]
        return StreamingResponse(deepseekllm.response_code(messages,stream=True), media_type='text/html')
    except Exception as e:
        print(e)