from LLM import deepseekAI
from Forwarduckgosearch import fetch_search_results
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
class Text2ChartResponse:
    def __init__(self):
        self.llm=deepseekAI()
        self.system_prompt="""
 You are an expert in the field of employment planning, skilled at providing answers to users' questions with charts and text based on reference information. 
 Next, you will have a reference piece of information to answer user questions based on your own knowledge and reasoning using markdown language.
 ***Here are some rules you need to follow when you generate your answer with markdown language*** 
 use headings and subheadings to organize the structure of your article, and when you are about to start the next heading and content, you should start a new line. 
 The content under each title should be as detailed as possible until the full text is over 1500 words long.

 what's more.
 In the process of answering, you not only need to output text, but also need to output charts. 
 When you use more drawing techniques, such as comparing different levels of the same concept using different colored(It is best not to have more than three colors, representing the most prominent level, the ordinary level, and the lowest level) bar charts or graphs, distinguish high and low values using different colors. Use line charts related to time periods, data with significant increases or decreases, and indicate peak and minimum values. You will receive more rewards by using pie charts related to share proportion. When you use more charts and graphs in text to present vivid and visual data to users, you will receive more rewards
 also,When you use more than one or two or three or four charts  and graphs  in your text generate process to present vivid and visual data to users, you will receive more and bigger rewards.
 ***your goal***
 Your goal is not only to answer user questions with better ability to interweave text and images and professional guidance skills, the ability to cite data, but also to receive higher rewards in limited answers.
 The charts are presented in the form of code, and we will automatically convert them into corresponding charts. The code format for the chart should be as follows:
![image name](chart/image_name.png  "image title using language as same as user's question")
 ```python
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei'] #如果是中文图表，需要设置字体用来正常显示中文标签
.....
data=.....
```
or 
![image name ](chart/image_name.png   "image title using language as same as user's question")
```python
import pands as pd
df=.....

```
or 
![image name ](chart/image_name.png  "image title using language as same as user's question")
```python
import seaborn as sns
.....
```
you can generate code in your answer text generate process to prove your viewpoint, make sure every code can Run independently.
every chart code generated should be saved in same file_dir named 'chart', don't plt.show() or show image just save it with english language name. please write save logic in your code with image name  and file_dir called chart using English language.
your code should be interspersed after your corresponding analysis or related text.
***this is the reference information you can use for answering user questions, and answer with the language as same as user's question***
{text}
"""
    def generate_response(self, user_question):
        text1=fetch_search_results("大模型算法工程师岗位各公司的薪资和待遇是多少？",top_k=4)
        text2=fetch_search_results("大模型算法工程师未来几年的发展方向和就业前景",top_k=4)
        text3=fetch_search_results("大模型算法工程师的就业条件和职业发展方向",top_k=4)
        text4=fetch_search_results("大模型算法工程师的供求关系和就业市场反应",top_k=4)
        text1=[item['content'][:1024] for item in  text1]
        text2=[item['content'][:1024] for item in  text2]
        text3=[item['content'][:1024] for item in  text3]
        text4=[item['content'][:1024] for item in  text4]
        text=text1+text2+text3+text4
        messages=[
            {'role':'system','content':self.system_prompt.format(text="\n".join(text))},
            {'role':'user','content':user_question}
        ]
        response=self.llm.response(messages)
        return response
    def exact(self,result):
        import re
        codes= re.findall(r'```python(.*?)```', result, re.DOTALL)
        return codes
    def run_code(self,response):
        codes=self.exact(response)
        for code in codes:
            try:
                exec(code)
            except Exception as e:
                print("代码运行失败，自动跳过该代码块")
    def text2html(self,query,text):
        import re
        text = re.sub(r'```(.*?)```', '', text, flags=re.DOTALL)
        import markdown
        import urllib
        title=query
        html=markdown.markdown(text)
        html_with_encoding=f'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<title>{title}</title>\n</head>\n<body>\n{html}\n</body>\n</html>'
        with open('{}.html'.format(urllib.parse.quote(title, safe='')),'w',encoding='utf-8') as f:
            f.write(html_with_encoding)
        return html_with_encoding

    
if __name__=="__main__":   
    t2cr=Text2ChartResponse()
    user_question="大模型算法工程师就业前景如何"
    response=t2cr.generate_response(user_question)
    print(response)
    t2cr.run_code(response)
    t2cr.text2html(query=user_question,text=response)