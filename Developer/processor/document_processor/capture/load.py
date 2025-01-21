import os
file_dir=os.path.dirname(__file__)
import fitz  # PyMuPDF,用于提取PDF中的图像和文本
import os  
import tempfile #用于创建临时目录存储生成的image，load后清空
import shutil   #用于删除临时目录
from paddleocr import PaddleOCR #ocr轻量识别
from docx import Document
class pdfLoader:
    """
    这是一个将pdf转化为document对象的类，可以提取pdf中的文本、图像，以及图像ocr识别结果。
    初始化传递两个参数，pdf_path为pdf文件路径，enable_ocr为是否开启ocr识别，默认为True。
    调用load方法可以返回一个列表，每个对象包含pdf中一页的文本与图像ocr识别结果（enable_ocr=True）。
    """
    def __init__(self, pdf_path,enable_ocr=True):
        ocr=PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=True,rec_model_dir=os.path.join(file_dir,'tools/paddleocr/rec/'),
                                 cls_model_dir=os.path.join(file_dir,'tools/paddleocr/cls/'),
                                 det_model_dir=os.path.join(file_dir,'tools/paddleocr/det/'))
        if enable_ocr:
            #模型加载路径
            self.ocr =ocr
        else:
            self.ocr = None
        self.pdf_path = pdf_path
        try:
            self.pdf_reader = fitz.open(pdf_path)
        except:
            raise ValueError("Invalid PDF file path")
        self.page_count = self.pdf_reader.page_count
        self.page_list = []
        self.image_data = []
        self.enable_ocr = enable_ocr
        self.temp_dir = tempfile.mkdtemp()  # 创建临时目录

        for i in range(self.page_count):
            self.page_list.append(self.pdf_reader.load_page(i))

    def get_text(self):
        result = []
        for i, page in enumerate(self.page_list):
            text = page.get_text()
            result.append({"page_num": i + 1, "text": text})
        return result

    def get_images(self):
        # 打断点检查代码
        # pdb.set_trace()
        self.image_data = []
        for i, page in enumerate(self.page_list):
            images = page.get_images(full=True)
            if images == []:
                continue
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = self.pdf_reader.extract_image(xref)
                img_bytes = base_image['image']
                img_name = os.path.join(self.temp_dir, f"page_{i + 1}_img_{img_index}.png")
                with open(img_name, "wb") as f:
                    f.write(img_bytes)
                #为每张图片记录一个元数据，包括page_num、x、y、w、h、image_bytes、image_path
                # Assuming image extraction coordinate when available
                self.image_data.append({
                    "page_num": i + 1,
                    "x": base_image['xres'],
                    "y": base_image['yres'],
                    "w": img[1],
                    "h": img[2],
                    "image_bytes": img_bytes,
                    "image_path": img_name
                })
        return self.image_data
    #只记录有文字识别的图片，其他没有文字的图片忽略，并记录所在页数和位置坐标
    def get_ocr(self):
        if not self.image_data:
            # pdb.set_trace()
            self.get_images()
        ocr_results = []
        for img in self.image_data:
            img_path = img['image_path']
            ocr_result = self.ocr.ocr(img_path, cls=True)
            try:
                ocr_result="\n".join([group[1][0] for group in  ocr_result[0][:]])
            except:
                continue
            text = "**text from image: "+ocr_result+"  **"
            ocr_results.append({
                "page_num": img['page_num'],
                "x": img['x'],
                "y": img['y'],
                "w": img['w'],
                "h": img['h'],
                "text": text
            })       
        return ocr_results

    def load(self):
        if self.enable_ocr:
            ocr_results = self.get_ocr()
        else:
            ocr_results = []

        final_document_text = []  # To store the final results
        #print(f"Total pages: {self.page_count}")
        for page_index in range(self.page_count):
            page = self.page_list[page_index]
            text = page.get_text("text")
            final_page_text = {
                "page_num": page_index + 1,
                "text": text,
                "ocr_texts": []
            }
            for ocr_result in ocr_results:
                if ocr_result['page_num'] == (page_index + 1):
                    # Insert OCR text into page's text
                    final_page_text["ocr_texts"].append({
                        "pos": (ocr_result['x'], ocr_result['y']),
                        "text": ocr_result['text']
                    })
            final_document_text.append(final_page_text)

        # Convert to Document objects
        documents = []
        for index,page_text in enumerate(final_document_text):
            metadata = {
                'source': self.pdf_path,
                'page': page_text['page_num'] - 1
            }
            page_content =page_text['text'] + "".join([i['text'] for i in page_text["ocr_texts"]])
            documents.append({"text": page_content, "metadata": metadata})

        # 清空临时目录
        shutil.rmtree(self.temp_dir)
        return documents
    def save(self,documents,save_dir):
        if save_dir is None:
            save_dir=os.path.dirname(self.pdf_path)
        file_path=os.path.basename(self.pdf_path)
        file_path=file_path.replace('.pdf','.json')
        import json
        with open(os.path.join(save_dir,file_path), 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=4)
        print("save success")

class jsonLoader:
    def __init__(self,json_path):
         self.json_path=json_path
         """ 
         读取json文件，键必须包含text，其余的字段统一视为metadata
         接受两种形式：
         1、由列表包裹的字典
         2、没有列表包裹的字典，一行视为一条数据   
         """
         import json
         with open(json_path, 'r', encoding='utf-8') as f:
             #读取第一个非空行，判断是否有列表包裹
             line=f.readline().strip()
             if line.startswith('['):
                 data = json.load(f)
             else:
                 remaining_content=f.read()
                 remaining_data=remaining_content.split('\n')
                 data=[]
                 for line in remaining_data:
                     if line.strip()=='':
                         continue
                     data.append(json.loads(line)) 
             if not isinstance(data,list):
                 raise ValueError("Invalid json file format")
         self.data=data
    def load(self):
        documents=[]
        for item in self.data:
            text=item.get('text')
            if text is None:
                continue
            documents.append({"text":text,"metadata":{
                k:v for k,v in item.items() if k!='text'
            }})
        return documents
    def save(self,documents,save_dir):
        if save_dir is None:
            save_dir=os.path.dirname(self.json_path)
        file_path=os.path.basename(self.json_path)
        file_path=file_path.replace('.json','.json')
        import json
        with open(os.path.join(save_dir,file_path), 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=4)
        print("save success")



class htmlLoader:
    def __init__(self, url):
        self.url = url

    def load(self):
        return get_content(self.url)
    def save(self,documents,save_dir):
        file_path=documents[0]['metadata']['title']
        save_path=file_path+".json"
        if save_dir is None:
            save_dir='./'
        #if  
        import json   
        with open(os.path.join(save_dir,save_path), 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=4)
        
        f.close()        
        print("save success")

class docxLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.doc=Document(file_path)
    def load(self):
        text=""
        for para in self.doc.paragraphs:
            text+=para.text+"\n"
        return [
            {
                "text":text,
                "metadata":{
                    'source':self.file_path
                }

            }
        ]
    def save(self,documents,save_dir):
        import os
        if save_dir is None:
            save_dir=os.path.dirname(self.file_path)
        file_path=os.path.basename(self.file_path)
        file_path=file_path.replace('.docx','.json')
        import json
        with open(os.path.join(save_dir,file_path), 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=4)
        print("save success")





#使用url进行文档爬取的时候需要记录以下几个信息
""" 
1、网站地址
2、页面标题
3、主要内容：新闻、法律、播报、论文主体等
4、元数据：作者、发布时间、来源、标签、所属分类等（通过提取获得）

使用库：beautifulsoup4、requests

执行方式：异步

"""
""" 
async def grap(url,selector):
    async with async_playwright() as playwright:
        #检测页面能否访问
        response = await page.goto(url)
        if response.status != 200:
            raise response.error
        documents=[]
        # 启动浏览器
        browser = await playwright.chromium.launch()  #使用谷歌浏览器
        #创建新页面
        page = await browser.new_page()
        await page.goto(url)
        # 等待页面加载完成
        #await page.wait_for_load_state()
        # 提取页面标题
        title = await page.title()
        # 提取页面主要内容
        content = await page.query_selector(selector)  
        
        # 关闭浏览器
        await browser.close()

"""
headers={'User-Agent':'Mozilla/5.0(Windows NT 6.1;WOW64) Applewebkit/537.36(KHTML,like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
""" 
def get_info(url):
    import asyncio
    import requests
    from bs4 import BeautifulSoup
    wb_data=requests.get(url,headers=headers)
    #设置编码
    wb_data.encoding=wb_data.apparent_encoding
    soup=BeautifulSoup(wb_data.text,'lxml')
    return soup 
""" 

def get_info(url, retries=3):
    import requests
    from bs4 import BeautifulSoup
    import random
    import time
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(1, 3))  # 随机等待
            wb_data = requests.get(url, headers=headers)
            wb_data.encoding = wb_data.apparent_encoding
            if wb_data.status_code == 200:  # 检查请求是否成功
                soup = BeautifulSoup(wb_data.text, 'lxml')
                return soup
            else:
                print(f"Request failed with status code {wb_data.status_code}. Retrying...")
        except requests.RequestException as e:
            print(f"An error occurred: {e}. Retrying...")
    
    raise Exception("Failed to retrieve the content after several attempts.")

def get_content(url):
    import asyncio
    import requests
    from bs4 import BeautifulSoup
    soup=get_info(url)
    soup_text=str(soup)
    import re
    patten=re.compile(r">(.*?)<")
    result=patten.findall(soup_text)
    content_text="".join(result)
    #提取标题
    title=soup.title.string
    meta={
        'title':title,
        'url':url,
    }
    
    return  [{
        'text':content_text,
       'metadata':meta
    }]




