"""
文本意图识别判断

输入用户问题和意图候选项列表，返回组装的messages消息队列

提示词构成:

说明任务，告知提供的参数，如果存在多个意图识别，返回列表。

最终的输出：列表


"""
def intent_recognition_template(query,intent_list):
    #输入意图识别列表，返回组装的messages消息队列
    messages=[]
    system_message={
        "role":"system",
        "content":"""
        this is a task about intent_recognition, you should infer the user's query to complete
        the intent_list one or more.
        please return only the intent in the intent_list.
        if there are more then one intent, return them with space split.
        intent_list:
        {}
        """.format(intent_list)
    }
    user_message={
        "role":"user",
        "content":query
    }
    messages.append(system_message)
    messages.append(user_message)
    return messages

""" 
信息抽取，输入文档和所要提取的信息列表，返回一个信息提取json,字段名来源于列表

提示词采用任务说明、分类方法按句子归属分类，最后汇总不同的信息到相同的字段。

few-shot以简历信息抽取为例。

最终的输出：json

"""
#信息抽取
def NER_template(query,target_list):
    messages=[]
    system_message={
        "role":"system",
        "content":f"""
        this is a NER task for target informations extracting.
        you need to read the article given with user and the target_information_list I given.
        your task is find the sentences from article complete which the target_information need and
        integrate the sentences grouping with correct target.
        your output is a json format message,which is as far as possible aligning with below few assistant response case:
        ***
        target_list=["学校","电话","姓名",{{"实习经历":{{"工作时间","工作单位","工作内容"}}}}]
        assistant:{{
        "学校":"华夏大学",
        "电话":"1232445456",
        "姓名":"王老七",
        "实习经历":[{{
        "工作时间":"2018年9月-2019年9月",
        "工作单位":"好好学习天天向上公司",
        "工作内容":"负责大模型的prompt构建"
        }},{{}}
        ],
        ......
        }}
        ***
        please be careful that the sentences you put in json is take out from article but not you own generate.if there is no related information,please make it space.
        there may be one or more content complete with the target, so if nessary, you should give the list of different place、time or more in the same target.
        finally,make your work will, and response with json and ban on use of '\n'
        this is the real target_list:
        {target_list}
        """
    }
    user_message={
        "role":"user",
        "content":query

    }
    messages.append(system_message)
    messages.append(user_message)
    return messages

""" 
相关问题生成。

输入一个原问题，生成多个近似问题，并返回问题列表

"""

def  multiquery_template(query,generate_num):
    messages=[]
    system_message={
        "role":"system",
        "content":"""
        this is a task for query generation.
        you need to generate{} similar queries for the user's original query.
        you can extend this question from different angles,including:
        ***other knowledge in the same field***
        ***new problems you may encounter after solving this problem***
        ***continue to ask in-depth questions at a certain point in the question that you think is important.***

        please return the generated queries with a format like:
        [query1,query2,query3,query4,query5]
        """.format(generate_num)
    }
    user_message={
        "role":"user",
        "content":query
    }
    messages.append(system_message)
    messages.append(user_message)
    return messages

""" 
有毒提示注入检测。

负责检测文章中的有毒片段，并进行识别标注，给出可能的有毒类型

"""

def toxic_detection_template(query):
    messages=[]
    system_message={
        "role":"system",
        "content":"""
        this is a task for toxic detection.
        you need to detect the toxic sentence in the article and classify them into different types.
        is the  sentence is malicious or not?
        there are some methods to detect toxic sentences, including:
        *** 
        1、Focus on concepts related to reality, such as entities and actions, and whether they involve dangerous areas such as security, discrimination, attacks, and causing verbal harm.
        2、Language has a certain degree of guidance and deception, it intends to guide you to output unsafe, inappropriate, and physically or mentally harmful speech.
        3、Its information is false, fabricated, or contrary to the laws of reality.
        4、If the language contains strong personal subjective emotions and prejudices, please be careful that it will be poisonous.
        5、It is necessary to understand the semantics. Like some satirical novels, some words may insinuate some sensitive topics.
        ***
        if you find the sentence is malicious, please output the sentence and the type of malicious.
        like this:
        [{
        "type": "暴力",
        "malicious_sentence": "我要打死你"
        },
        {
        "type": "色情",
        "malicious_sentence": "一男三女开房"}
        ......
        ]
        if there is no malicious sentence, please output:
        [{
        "type": "正常"
        "malicious_sentence":""
        }]

        please be careful that the sentence you put in json is take out from article but not you own generate.if there is no related information,please make it space and not use '\n'.

        Before giving the final result, please make sure to consider the methods I provided sentence by sentence for troubleshooting.

        """
    }
    user_message={
        "role":"user",
        "content":query
    }
    messages.append(system_message)
    messages.append(user_message)
    return messages




