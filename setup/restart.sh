#!/bin/bash

# 定义服务相关的端口
MILVUS_PORT=19530
ELASTICSEARCH_PORT=9200
MYSQL_PORT=3306
export MILVUSCONF=/etc/milvus/configs

# 清空日志文件
true > logs/milvus.log
true > logs/elasticsearch.log
true > logs/mysql.log  # 清空 MySQL 日志文件

# 检查并重启 Milvus
echo "检查 Milvus 服务状态..."
if lsof -i:$MILVUS_PORT; then
    echo "发现 Milvus 正在运行，正在停止进程..."
    sudo milvus stop standalone  # 使用 sudo 停止 Milvus
    sleep 2  # 等待2秒，给进程时间正常关闭
else
    echo "Milvus 没有在运行。"
fi

# 释放端口（如果需要）
echo "释放 Milvus 端口 $MILVUS_PORT..."
sudo fuser -k $MILVUS_PORT/tcp 2>/dev/null

echo "启动 Milvus 服务..."
nohup milvus run standalone >> logs/milvus.log 2>&1 &
echo "Milvus 已重启，访问地址：http://localhost:$MILVUS_PORT"

# 检查并重启 Elasticsearch
echo "检查 Elasticsearch 服务状态..."
if lsof -i:$ELASTICSEARCH_PORT; then
    echo "发现 Elasticsearch 正在运行，正在停止进程..."
    sudo pkill -f elasticsearch  # 使用 pkill 停止 Elasticsearch
    sleep 2  # 等待2秒，给进程时间正常关闭
else
    echo "Elasticsearch 没有在运行。"
fi

# 清空 Elasticsearch 日志文件
true > logs/elasticsearch.log
echo "启动 Elasticsearch 服务..."
sudo -u elasticsearch nohup /usr/share/elasticsearch/bin/elasticsearch >> logs/elasticsearch.log 2>&1 &
echo "Elasticsearch 已重启，连接地址：http://localhost:$ELASTICSEARCH_PORT"

# 检查并重启 MySQL
echo "检查 MySQL 服务状态..."
if systemctl is-active --quiet mysql; then
    echo "发现 MySQL 正在运行，正在重启..."
    sudo service mysql restart
else
    echo "MySQL 没有在运行，正在启动 MySQL 服务..."
    sudo service mysql start
fi

# 清空 MySQL 错误日志（根据您的日志设置改变相应的路径）
true > /var/log/mysql/mysql_error.log
true > /var/log/mysql/mysql_query.log
true > /var/log/mysql/mysql_slow_query.log

echo "MySQL 服务已重启，连接地址：localhost:$MYSQL_PORT"

# 启动 MySQL 服务，记录日志
echo "启动 MySQL 服务并记录日志..."
sudo service mysql start >> logs/mysql.log 2>&1

echo "数据库服务已重启"
