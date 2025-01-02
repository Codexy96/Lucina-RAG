#----------------支持使用json文件上传数据---------------------#

#------------------------------------------------------------

#将json文件复制到data文件夹下，运行upload_data.py脚本，即可自动化知识库创建

#文件取名应为： 知识库名称-1.json 知识库名称-2.json .........

#--------------------------#

from ..Engine.KB.KnowledgeBase import KnowledgeBase
import os 
import json
file_dir=os.path.dirname(__file__)
data_path=os.path.join(file_dir,'data')
json_flies=os.listdir(data_path)
kb=KnowledgeBase()
for json_file in json_flies:
    if json_file.endswith('.json'):
        with open(os.path.join(data_path,json_file),'r',encoding='utf-8') as f:
            data=json.load(f)
        #检查data 格式是否有效
        if not isinstance(data,list):
            print(f'非法数据：{json_file} 格式错误，应为列表')
            raise ValueError
        if not all(isinstance(item,dict) for item in data):
            print(f'非法数据：{json_file} 列表中存在非字典项')
            raise ValueError
        #data必须包含slice_id 和 content两个字段
        if  not all(key in item for item in data for key in ['slice_id','content']):
            print(f'非法数据：{json_file} 列表中存在缺少字段slice_id 或 content')
            raise ValueError
        kb_name=json_file.split('.')[0].split('-')[0]
        if kb.mysql.exists_kb(kb_name):
            kb.insert_data(name=kb_name,data=data)

        else:
            kb.create_kb(kb_name)
            kb.insert_data(name=kb_name,data=data)
    print(f'{json_file} 数据上传成功')


        
