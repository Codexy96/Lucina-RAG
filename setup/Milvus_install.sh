#!/bin/bash
# 依赖：go: 1.21 cmake: >=3.18 gcc: 7.5 protobuf: >=3.7

FILE="milvus_2.3.10-1_amd64.deb"

# 检查文件是否存在
if [ -f "$FILE" ]; then
    echo "$FILE 已存在，跳过下载。"
else
    echo "未找到$FILE ，正在下载..."
    wget https://github.com/milvus-io/milvus/releases/download/v2.3.10/$FILE
fi

sudo apt-get update
sudo dpkg -i $FILE
#s设置milvus配置文件路径
export MILVUSCONF=/etc/milvus/configs
PORT=19530
# 检查并清空端口占用
if lsof -i:$PORT; then
    echo "端口 $PORT 被占用，正在终止占用进程..."
    # 找到并终止占用端口的进程
    PID=$(lsof -ti:$PORT)
    kill -9 $PID
    echo "已终止占用端口 $PORT 的进程 $PID。"
else
    echo "端口 $PORT 未被占用。"
fi
> logs/milvus.log # 清空日志文件
nohup milvus run standalone > logs/milvus.log 2>&1 &

echo "Milvus 安装成功，已自动为您后台启动，访问地址为：http://localhost:19530"

echo "运行日志输出到 milvus.log 文件中。"