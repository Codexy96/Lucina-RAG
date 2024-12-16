import hashlib
import re
import os
#from langchain.docstore.document import Document
file_dir=os.path.dirname(__file__)



#通用切分器：spliter(data,block_size=512),支持中英文，支持块重叠切分
def common_spliter(data : list,block_size=512,use_overlap=False,overlap_number=3):
    """
参数：
- data: 待切分的文档列表,每个文档将自动分配一个哈希ID。如果要自定义文本id,请在data列表中传入{id:xxx,text:xxx}的格式。
- block_size: 切分块的大小，默认为512。
- use_overlap: 是否使用块重叠，默认为False。
返回值：
  切分文本片段的列表，每个文本片段包含：- slice_id: 唯一标识符 - source_id: 来源文档的唯一标识符 - text: 文本片段  -index: 切块在原文中的顺序 - metadata: 元数据，此切分规则为空



切分逻辑：以句子为最小单位，切分到不超过block_size个字的块，如果加上当前句子会超过block_size,则拼接到下一个块中。

如果一个句子的长度超过block_size，则强制拆分成两个或多个块，每个块的大小为block_size//2。

"""
    sentences_list=[]
    block_list=[]
    for sample in data:
        if isinstance(sample,str):
            id=generate_hash_id(sample)
            text=sample
        elif isinstance(sample,dict):
             if 'text' not in sample:
                 raise ValueError("text not in sample,please check the format")
             if 'id' not in sample:
                 id=generate_hash_id(sample['text'])
                 text=sample['text']
                 metadata={  k:v   for k,v in sample.items() if k!='text'}
             else:
                  id=sample['id']
                  text=sample['text']
                  metadata={  k:v   for k,v in sample.items() if k!='text' and k!='id'}
        #分句
        #text=stop_words(text)
        sentences_list = split_sentences(text) # 强制使用正则表达式来匹配多个符号,切分规则可自行调整
    #按句子切块，每块block_size个字，则该句子拼接到下一块当中
        block=""
        index=0
        for i,sentence in enumerate(sentences_list):
            #sentence=stop_words(sentence)
            if len(block)+len(sentence)<=block_size:
                block+=sentence
            else:
                 if len(block)>block_size:
                     #强制拆分
                     block_forward=""
                     for j in range(0,len(block),block_size//2):
                          block_list.append(
                              {
                                  "slice_id":generate_hash_id(block_forward+block[j:j+block_size//2]),
                                  "source_id":id,
                                  "content":block_forward+block[j:j+block_size//2],
                                  "place":index,
                                  **metadata
                              }
                          )
                          if use_overlap:
                                 sentence_temp=split_sentences(block[j:j+block_size//2])
                                 block_forward="".join(sentence_temp[max(0,len(sentence_temp)-overlap_number):])
                          else:
                                 block_forward=""
                          index+=1
                 else:
                      block_list.append(
                     {
                          "slice_id":generate_hash_id(block),
                          "source_id":id,
                          "content":block,
                          "place":index,
                          **metadata
                     })
                      index+=1
                 if use_overlap:
                      block="".join(sentences_list[max(0,i-overlap_number):max(i,0)])+sentence
                 else:
                      block=sentence
        if len(block)>block_size:
             #强制拆分
             block_forward=""
             for j in range(0,len(block),block_size//2):
                  block_list.append(
                      {
                          "slice_id":generate_hash_id(block_forward+block[j:j+block_size//2]),
                          "source_id":id,
                          "content":block_forward+block[j:j+block_size//2],
                          "place":index,
                          **metadata
                      }
                  )
                  if use_overlap:
                         sentence_temp=split_sentences(block[j:j+block_size//2])
                         block_forward="".join(sentence_temp[max(0,len(sentence_temp)-overlap_number):])
                  else:
                         block_forward=""
                         
                  index+=1
            
        else:
             block_list.append(
             {
                  "slice_id":generate_hash_id(block),
                  "source_id":id,
                  "content":block,
                  "place":index,
                  **metadata
             }
             

        )
             index+=1
    return block_list

   


#生成唯一文档哈希ID
def generate_hash_id(text):
    hasher=hashlib.sha256()
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()


#默认不启用文本清洗，仅切片
def stop_words(text):
    import jieba
    import os
    words = jieba.lcut(text)
    file_dir=os.path.dirname(__file__)
    stopwords_path=os.path.join(file_dir,'resources/stopwords.txt')
    stopwords = set(open(stopwords_path,encoding='utf-8').read().splitlines())
    words=[word.replace('\u3000'," ").replace("\t"," ").replace('\xa0'," ").replace('    ',' ').replace('   ',' ').replace('  ',' ') for word in words if word not in stopwords ]
    return "".join(words) 

def split_sentences(text,pattern=None):
    if pattern is None:
         pattern = r'[^。！？！；，。,.?!;]+[。！？！；，。,.?!;]?'
    else:
         pattern =pattern   
    sentences_list = re.findall(pattern, text)
    return sentences_list

#参考用例
if __name__ == '__main__' :
       data=["""
字节跳动的职级一共10级，从1-1到5-2，每一个大职级下分有1~2个小职级，1-1是初级工程师，1-2是研发工程师，2-1和2-1为资深研发，3-1和3-2为team领导层，4-1和4-2是部门领导层，5-1和5-2是公司领导层。

1-1和1-2主要由刚毕业或工作经验尚浅的员工组成，校招应届生目前一般是 1-2级，作为项目组成员；平均月薪24k，年终奖大概为3个月，比其他互联网大公司入门级别的月薪20k左右要高出20%左右。

而2-2可对标阿里P7、腾讯9、10级，将会有股票激励。关于期权，回购价格为市场价 8 折，已归属的期权员工可以带走。3-1和3-2就是公司的中层了。""",
           """ByteDance was founded in 2012 by a team led by Yiming Zhang and Rubo Liang, who saw opportunities in the then-nascent mobile internet market, and aspired to build platforms that could enrich people's lives. The company launched Toutiao, one of its flagship products, in August 2012. It followed that success with the launch of Douyin in September 2016. Approximately a year later, ByteDance accelerated globalization with the launch of its global short video product, TikTok. It quickly took off in markets like Southeast Asia, signaling a new opportunity for the company. ByteDance acquired Musical.ly in November 2017 and subsequently merged it with TikTok. Today, the TikTok platform, which is available outside of China, has become the leading destination for short-form mobile videos worldwide.

In support of its mission to Inspire Creativity and Enrich Life, ByteDance has made it easy and fun for people to connect with, create and consume content. People are also able to discover and transact with a suite of more than a dozen products and services such as TikTok, CapCut, TikTok Shop, Lark, Pico and Mobile Legends: Bang Bang, as well as products and services specific to the China market, including Toutiao, Douyin, Fanqie, Xigua, Feishu and Douyin E-commerce.

ByteDance has over 150,000 employees based out of nearly 120 cities globally, including Austin, Barcelona, Beijing, Berlin, Dubai, Dublin, Hong Kong, Jakarta, London, Los Angeles, New York, Paris, Seattle, Seoul, Shanghai, Shenzhen, Singapore, and Tokyo.""",
           """　出国留学网英语栏目的小编给大家带来中英双语美文欣赏：做最好的自己才能更好爱人，以下是详细内容，希望大家喜欢!

　　I used to believe that love meant putting everyone else and their needs first, before my own. While I do think there is some truth to that, in the sense that being a giving person is one of the ultimate acts of being a loving person, I came to realize that I must give to and love myself first and foremost.

　　以前，我相信爱就意味着要把他人和他人的需求放在自己的需求之前。现在我仍然认为这种观点有一定的道理，因为作一个“施爱者”的最高境界之一就是作一个“给予者”。但是，我渐渐意识到，给予自己、爱自己才是最重要的。

　　Here's why:

　　原因如下：""",
           ]
       block_list=common_spliter(data,block_size=300,use_overlap=True)
       for block in block_list: 
            print(block['text'])
            print("-----------")