#!/bin/bash

# 更新软件包列表
echo "更新软件包列表..."
sudo apt-get update

# 安装 Redis
echo "安装 Redis..."
sudo apt-get install -y redis-server

# 启动 Redis 服务
echo "启动 Redis 服务..."
sudo systemctl start redis.service

# 设置 Redis 服务开机自启
echo "设置 Redis 服务开机自启..."
sudo systemctl enable redis.service

# 检查 Redis 服务状态
echo "检查 Redis 服务是否正在运行..."
sudo systemctl status redis.service

# 提示安装成功
echo "Redis 安装成功！"

# 提供连接测试信息
echo "您可以使用以下命令连接到 Redis："
echo "redis-cli"
