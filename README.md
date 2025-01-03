


https://github.com/user-attachments/assets/68863266-43bb-45c2-b9f7-98646afcf947



https://github.com/user-attachments/assets/7afc1d75-b1e7-4d6e-be36-cdf5d362aecd




### Lucina-RAG 2025.01.02更新日志

#### 正式版 1.0.1 更新说明

在本次更新中，我们主要对 Lucina-RAG 项目现有的结构和功能进行了完善与优化，确保各个模块分离明确，便于二次开发。以下是具体更新内容：

1. **项目结构优化**：
   - 精简了项目层级，提供最少的接口以实现核心功能。

2. **API模块**：
   - 简化API编写，将不必要模块移除。

3. **引擎（Engine）改进**：
   - 集成了所有必要组件，支持数据库、模型、联网搜索引擎和 TensorRT 推理加速引擎。
   - LLM 模块现具备统一的接口封装和 prompt 修改入口，便于独立测试和优化提示词。
   - 数据库操作逻辑主要服务于 KB 模块，建议直接使用KB类创建知识库

4. **知识库模块（KB）**：
   - 完善了知识库的服务功能，包括创建知识库、导入数据、查看、删除、重置知识库等操作。
   - 将知识库搜索功能与知识库基础类拆分。方便修改和调试。

5. **联网搜索**：
   - 新增博查API的集成，开发者可以快速进行网页摘要搜索，提升联网信息获取速度。

6. **服务层（Server）接口**：
   - 提供两个最频繁使用的接口：`Search` 和 `upload_data`。
   - `Search` 接口整合各类搜索方式的结果，并进行后处理，返回最终搜索结果。
   - `upload_data` 接口支援一键数据上传，支持 json 格式的数据导入，自动创建知识库。

7. **安装与配置**：
   - `Setup` 模块中提供了组件安装脚本及环境配置，便于用户快速搭建项目环境。
   - 新增 `test.sh` 脚本，用于测试核心类的可用性。

8. **功能增强**：
   - 引入 query 改写功能，提升查询准确性。
   - 使用 MySQL 管理知识库的生命周期，并持久化存储日志，增强操作可溯源。
   - 数据可视化工具从 matplotlib (plt) 转换为 pyecharts，将支持更丰富和交互性更强的图表生成。

#### 总结
我们主要对项目结构进行了精简，对某些不必要的类进行删除，方便开源社区在此基础上调整开发。统一使用KB类管理知识库生命全周期，支持数据导入和搜索。更加美观、互动性更强的图表生成。
