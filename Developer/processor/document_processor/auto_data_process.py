"""
自动文本数据处理管道：

处理过后的数据只包含5个字段：

1、slice_id：切片哈希值，主键
2、content: 切片内容，文本
3、index: 切片顺序，文本形式储存
4、source_id:来源文本哈希ID，文本形式储存
5、metadata:元数据 以文本的形式储存

这些处理过后的数据以json的格式存储到data/commit目录下，用户可使用commit脚本中自动上传知识库
支持文件：
1、txt文件
2、json文件
3、csv文件
4、pdf文件
5、docx文件

处理过程：

一：读取文件列表，批量提取文本内容，转化为json格式列表，{"text":,"metadata":}
"""
#打开data下的source文件夹，读取文件列表




