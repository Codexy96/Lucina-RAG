
https://github.com/user-attachments/assets/1aee6ecf-5a9e-418b-9a3b-feab2751a68c


## 2025.2.8更新内容(内容仍在优化，尚未并入主分支)
- **图片召回功能**：本次更新引入了图片召回功能，使用阿里的多模态模型结合Milvus构建图片召回和文本实时匹配系统。
- **测试环境**：该代码在一万张图片上进行了测试，暂未推广到大量图片的生产环境，因此仅作测试使用。

## 技术栈
- **多模态模型**：阿里云提供的多模态向量模型，用于处理文本和图片的向量化，但这不是最佳选择。
- **Milvus**：用于存储和检索向量的高性能向量数据库。
## 注意事项
- **向量化脚本不完善**：
  - **请求效率低下**：由于API速率限制，向量化脚本的请求效率较低。
  - **OCR内容召回效果不佳**：阿里的多模态模型在对OCR内容召回时表现不佳，尤其是在图表和带有文字的报告中，未能达到预期效果。同时，仍无法满足文本和图像多模态融合的需求，使得图片的语义信息丢失严重。
- **管道分离带来的开发负担**：考虑到OCR文字和图片的管道分离会给实际生产环境中的迭代和数据更新带来更多的工作量，因此目前仍采用多模态向量搜索的技术路线。

## 后续工作计划
- **优化向量模型**：对向量模型针对图片RAG任务进行优化，并在大规模图片的搜索任务上进行验证。
- **开发大模型记忆模块**：启动对大模型记忆模块的开发阶段，提高记忆搜索效率和多轮对话的回答性能。
- **云端分离**：将单机开发升级至模型服务、搜索服务、面向客户端服务的三端分离服务架构，用于适配图片RAG的实际生产环境。

## 当前版本
当前代码为测试版本1.1.0，适用于小规模图片和文本的匹配测试。
