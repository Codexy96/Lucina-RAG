# Lucina-RAG

## 项目概述(演示视频：[点击这里观看演示视频](https://images-for-zhiye.oss-cn-beijing.aliyuncs.com/demo.mp4?Expires=1734322688&OSSAccessKeyId=TMP.3KdEjSMbZFjEU8DuXNRTGB9QfZ7dyqA8X7w6goNwihw8ju9cy791dbD2fkJ8dSDGAumD5n3JM7CBAJ7q5edVYYh5G9mjjE&Signature=fbyVkLbo7ZaZRAMbsXT6QpbALlk%3D))

Lucina项目旨在建立一个高效的RAG（Retrieval-Augmented Generation）系统，融合多种检索和生成技术，以便为用户提供多模态的问答服务。

## 技术选型如下：

- 向量搜索：
  - milvus
- 向量模型：
  - bce-embedding-v3
- 全文检索：
  - Elasticsearch
- 联网检索：
  - ducksearch
- 生成模型：
  - deepseek-chat
- 重排序：
  - bce-reranker-large
- 即时压缩：
  - Lingua2
- 接口开发：
  - fastapi
- 历史对话存储：
  - mysql
- 评估管道：
  - ragas
- 模型加速
  - tensorrt

## 工作流程：
"""确保你已经得到了LLM文件夹下的config的deeekseekAI的的key-value，否则无法提供服务"""

1、使用安装脚本安装开发环境，包括milvus、ES、mysql和tensorrt

2、使用download文件下的脚本下载BCE_embedding和BCE_rerank模型

3、使用抽象类knowledgebase创建知识库，导入数据，数据必须先使用process下的document_process的切片流程获得切片数据，详情请查看脚本说明

4、插入数据后，使用knowledgebas_for_search导入类进行搜索，可以控制BM25的阈值、top_k,向量搜索的top_k

5、使用API下的模块组建服务端，目前只测试过chart_html_api.py，如果要使用，要同时启动chart_api负责图片的发送

6、如果要加速模型推理速度，使用tensorrt文件夹下的脚本自动转化即可，使用之前，确保onnx产生的引擎文件路径正确。

7、访问浏览器，查看效果。

## 模块描述：

- **API**：负责服务端的流程构建，包括图表的定向和网页端的text输出。
- **Developer**：负责后端的数据处理管道。
- **Engine**：负责管理数据库和模型的交互操作。
- **Other**：开发过程中要用到的资源，包括中文字体和duckgo远程服务器部署脚本。
- **Setup**：环境安装脚本，负责搭建milvus、ES、mysql、tensorrt。
- **Tensorrt**：提供引擎化脚本和模型推理API。
- **Test**：用于测试各个模块的可用性。
- **Web**：前端页面，将作为系统前端页面的开发，暂未启用。



## 1.0.1测试版更新日志

### 1、新增功能
- **1.1** 新增图表代码模块，支持大模型生成Python代码以生成图表并加载图片。
- **1.2** 支持开发环境脚本一键安装，包括TensorRT引擎化脚本。抽象API `knowledgebase` 和 `knowledgebase_for_search` 现在支持创建知识库、自动向量插入数据、删除知识库、搜索等操作，操作简单易用。
- **1.3** 新增文本处理管道，针对PDF、docx、json文件制定了相应的文本预处理策略。

### 2、逻辑优化
- **2.1** 网页搜索流程由之前的`searxng_search`扩展为网页内容抓取。考虑到`searxng`返回的内容仅包含网页简介，新的流程是从`searxng`检索到相关页面，然后通过`langchain`抓取页面内容。调整后使用`duckgo`搜索支持，并通过`langchain`抓取页面内容，所有操作在远程服务器完成。
- **2.2** 调整本地服务端API的文本处理逻辑。实际测试中发现网页搜索时间通常在4秒到10秒之间，而向量搜索和关键词查找不超过1秒。因此，向量搜索将被优先处理并异步进行重排序和文本压缩，与网页搜索并行处理。网页搜索结束后，不再额外重排序，直接进行文本压缩并与混合搜索结果合并，以获得最终结果。

### 3、架构优化
- **3.1** 删除了第一版中MySQL承担的Milvus向量搜索后的文本查找工作，改为使用ElasticSearch（ES）。混合搜索模块现在变为Milvus和ES，减少了重复存储。
- **3.2** 支持Milvus的其他索引创建功能，如PQ、SQ8索引等，这些将在虚拟机中被考虑。当前，抽象类`knowledgebase`已支持上述索引创建。
- **3.3** 使用TensorRT加速重排序模型和向量模型。模型转化为TensorRT引擎后，推理速度明显提升。在第一版测试环境中，响应时间从原来的7秒压缩到4秒，主要是重排序模型的推理时间压缩带来的效果。然而，由于联网搜索流程的改动，整体响应时间又延长了3到4秒左右。在实际测试过程中，为了保证图表代码生成的效果，使用了`deepseek`的coder模型，尽管响应时间和token生成速度相比`glm`的`glm-airx`有所下降，但这不是目前优先考虑的问题。

### 其他
- 1GB的文本数据大约需要8GB的向量数据空间，目前磁盘空间占用11GB，虚拟机30GB，理论上还可以增加2GB的文本数据。后续优化将考虑在文本组织长度限制和使用占用空间更少的向量索引的方向上进行。
- 4090 24GB显卡仍有很大的显存空间，可以通过部署多个实例来调度模型，进一步提高并行处理能力。
- 目前的联网搜索已经使用了一系列机制防止卡死，但稳定性尚不高，后续需要重写相关逻辑。
- 当前为测试版本，主要API和脚本已进行测试，一键安装脚本在同一平台的新虚拟机上测试通过，但不同虚拟机环境可能存在差异。如果无法正常运行，需依照脚本命令自行安装。



### 正式版开发计划
- **1** 优化联网搜索流程，提高速度和稳定性。
- **2** 提升图表展示的美观性和模型代码生成能力。
- **3** 完善以知识库为核心的抽象API的开发。
- **4** 启动图片RAG搜索的接入和开发。
- **5** 优化联网搜索的query改写，尽量减少问答内容，获取更高质量的官方数据以支持图表和分析。
