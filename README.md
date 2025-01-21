框架图：

KnowledgeBase:知识库抽象，连接milvus、mysql、ES，支持创建库、导入数据、删除库等操作，自动同步到全部数据库。

SERVER_API: 服务端API，提供问答。

DEVELOP_API:开发者API，提供知识库管理、插件启用、工作流搭建等功能。


WEB_UI: 前端UI，提供用户交互界面。


12.13日开发任务：

1、迅速还原之前数据的那一套RAG搜索系统

2、将tensorrt引擎复现，将API服务写好

3、添加流式图表生成逻辑

4、整理开发文档，更新版本


下载完模型后tensorrt化，检查BCE_embedding.py和BCE_rerank是否正常运行

处理dataset，去重，并构建数据库