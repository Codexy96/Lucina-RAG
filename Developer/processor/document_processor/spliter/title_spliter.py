from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from typing import List, Optional
import hashlib
import re
import copy



#标题切分器，支持自动识别标题，并将标题记入到metadata当中
def  title_spliter(data:List[str],block_size:int=512,overlap:int=2):
    """ 
    参数：
        data：输入的文本数据，列表形式
        block_size：切分块的大小
        overlap：切分块的重叠度，多少个句子，0则为不重叠，默认启用为2
    返回：
        slice_id：切分块hash值
        source_id:原始文档的hash值
        index：切分块的索引
        text：切分块的文本
        metadata：切分块的元数据，包括标题
    """
    processor = TitleStructuredTextProcessor(block_size=block_size, overlap=overlap)
    documents = processor.create_documents(data)
    output=[ {
        "slice_id": generate_hash_id(doc.page_content),
        "source_id":doc.metadata.get("source_id"),
        "index": doc.metadata.get("index"),
        "content": doc.page_content,
        "metadata":{"title": doc.metadata.get("title")}} for doc in documents]
    return output

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




def generate_hash_id(text):
    hasher=hashlib.sha256()
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()



def under_non_alpha_ratio(text: str, threshold: float = 0.5) -> bool:
    if len(text) == 0:
        return False

    alpha_count = len([char for char in text if char.strip() and char.isalpha()])
    total_count = len([char for char in text if char.strip()])
    try:
        ratio = alpha_count / total_count
        return ratio < threshold
    except ZeroDivisionError:
        return False
""" 
标题检测逻辑
1、标题的长度不能超过15个字
2、标题的末尾不能是标点符号
5、标题的开头不能是阿拉伯数字
6、如果开头是一、二、三、四.....等中文数字，则大概率是标题
7、如果开头是fst.、snd.、trd....等英文序号缩写，则大概率是标题
8、如果开头是#、##、###、####等，则大概率是标题
9、确定好是标题后，如果文字是英文，则大概率是英文标题
10、确定好是标题后，如果文字是中文，则大概率是中文标题
11、检查前五个字符，若无数字则视为标题
"""
import re

def is_possible_title(text: str, title_max_word_length: int = 15, non_alpha_threshold: float = 0.5) -> bool:
    text = "".join(text.split())  # 去除所有空格
    if len(text) == 0:
        return False

    ENDS_IN_PUNCT_PATTERN = r"[^\w\s]\Z"
    ENDS_IN_PUNCT_RE = re.compile(ENDS_IN_PUNCT_PATTERN)
    if  ENDS_IN_PUNCT_RE.search(text):  # 检查是否以非字母、非数字和非空格字符结尾
        #print("以非字母、非数字和非空格字符结尾")
        return False

    if len(text) > title_max_word_length:  # 检查长度
        #print("标题长度过长")
        return False

    if under_non_alpha_ratio(text, threshold=non_alpha_threshold):  # 检查非字母字符比例
        #print("非字母字符比例过高")
        return False

    # 检查开头字符
    if text[0].isdigit():  # 以阿拉伯数字开头
        #print("以阿拉伯数字开头")
        return False

    # 中文数字判断
    if re.match(r'^[一二三四五六七八九十]+', text):
        return True

    # 检查英文序号缩写
    if re.match(r'^(fst\.|snd\.|trd\.)', text):
        return True

    # 检查 Markdown 风格
    if text.startswith("#"):  # 判断是否以# 开头
        return True

    # 最后，检查是否是全数字
    if text.isnumeric():
        #print("全数字")
        return False

    # 如果字数大于10个，则检查后5个字符是否包含数字，若无则视为标题
    if len(text) > 10:
        text_5 = text[-5:]
        alpha_in_text_5 = sum(map(str.isnumeric, text_5))
        if alpha_in_text_5:
            return False
    return True
    

class TitleStructuredTextProcessor(CharacterTextSplitter):

    def __init__(self, block_size: int = 100, overlap: int = 2, **kwargs):
        super().__init__(**kwargs)
        self.block_size = block_size  # 块的宽松限制长度
        self.context_overlap = overlap  # 重叠的句子个数

    """ 
    拆分文本，按照逗号、句号、换行符进行拆分，并保留符号
    """
    def create_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[Document]:
        """拆分文本，检测并处理标题层级结构"""
        _metadatas = metadatas or [{}] * len(texts)
        documents = []
        title = None

        for i, text in enumerate(texts):
            #text=stop_words(text)
            # 拆分文本并保留符号
            chunks = self.split_text(text)  # 使用新的拆分方法
            source_id = generate_hash_id(text)
            temp_content = ""  # 用于临时存储当前块内容
            #print(chunks)
            _metadatas[i]['source_id']=source_id
            id=0
            for index,chunk in enumerate(chunks):
                # 判断是否为标题
                if is_possible_title(chunk):
                    if title and temp_content:
                        # 如果有标题且已有内容则将上一部分的文本输出

                        self._add_document(documents, temp_content, _metadatas[i], title,id,next_sentence=chunks[index+1:index+self.context_overlap+1] if index+self.context_overlap+1<len(chunks) else chunks[index+1:])
                        id+=1
                        temp_content =""  
                        title=None  # 重置标题
                    # 更新当前标题和内容
                    title = chunk
                else:
                    temp_content += chunk + " "  # 拼接非标题内容

                # 检查当前内容是否达到句子宽松限制
                if len(temp_content) >= self.block_size:
                    self._add_document(documents, temp_content, _metadatas[i], title,id,next_sentence=chunks[index+1:index+self.context_overlap+1] if index+self.context_overlap+1<len(chunks) else chunks[index+1:])
                    temp_content="" 
                    id+=1


            # 处理完当前文本后，检查是否还有需要保存的内容
            if title and temp_content:
                self._add_document(documents, temp_content, _metadatas[i], title,id,next_sentence=chunks[index+1:index+self.context_overlap+1] if index+self.context_overlap+1<len(chunks) else chunks[index+1:])
                id+=1
                


        return documents
    #分段逻辑
    def split_text(self, text: str) -> List[str]:
        # 按照逗号、句号、换行符、感叹号、问号进行拆分，并保留符号
        chunks = [chunk.strip() + (m if m in [',', '。', '!', '?','，','. ','！'] else '') for chunk, m in re.findall(r'([^。!？\n.？！]+)([。.\n？!！])?', text) if chunk]
        
        return chunks



    def _add_document(self, documents: List[Document], combined_content: str, metadata: dict, title: str,id:int,next_sentence:str=None):
        """添加文档,并处理后缀重叠逻辑"""
        combined_content=combined_content.strip()   
        if combined_content:
            metadata['category']='cn_Title'
            if title:
                metadata['title']=title
            else:
                metadata['title']=''
            if id:
                metadata['index']=id   
            else:
                metadata['index']=0

            new_document=Document(page_content=combined_content,metadata=metadata)
            if next_sentence:
                new_document.page_content=new_document.page_content+"".join(next_sentence)
            documents.append(new_document)

if __name__ == '__main__':
    sample_texts = [
       """反分裂国家法
（2005年3月14日第十届全国人民代表大会第三次会议通过）
　　第一条　为了反对和遏制“台独”分裂势力分裂国家，促进祖国和平统一，维护台湾海峡地区和平稳定，维护国家主权和领土完整，维护中华民族的根本利益，根据宪法，制定本法。
　　第二条　世界上只有一个中国，大陆和台湾同属一个中国，中国的主权和领土完整不容分割。维护国家主权和领土完整是包括台湾同胞在内的全中国人民的共同义务。
　　台湾是中国的一部分。国家绝不允许“台独”分裂势力以任何名义、任何方式把台湾从中国分裂出去。
　　第三条　台湾问题是中国内战的遗留问题。
　　解决台湾问题，实现祖国统一，是中国的内部事务，不受任何外国势力的干涉。
　　第四条　完成统一祖国的大业是包括台湾同胞在内的全中国人民的神圣职责。
慈善法第一章总则
第一条 为了发展慈善事业，弘扬慈善文化，规范慈善活动，保护慈善组织、捐赠人、志愿者、受益人等慈善活动参与者的合法权益，促进社会进步，共享发展成果，制定本法。
第二条 自然人、法人和非法人组织开展慈善活动以及与慈善有关的活动，适用本法。其他法律有特别规定的，依照其规定。
第三条 本法所称慈善活动，是指自然人、法人和非法人组织以捐赠财产或者提供服务等方式，自愿开展的下列公益活动：
（一）扶贫、济困；
（二）扶老、救孤、恤病、助残、优抚；
（三）救助自然灾害、事故灾难和公共卫生事件等突发事件造成的损害；
（四）促进教育、科学、文化、卫生、体育等事业的发展；
（五）防治污染和其他公害，保护和改善生态环境；
（六）符合本法规定的其他公益活动。
第四条 慈善工作坚持中国共产党的领导。开展慈善 活 动，应 当 遵 循 合 法、自 愿、诚信、非营利的原则，不得违背社会公德，不得危害国家安全、损害社会公共利益和他人合法权益。
    """
    ]
    output=title_spliter(sample_texts,100,1)
    for item in output:
        print(item)




