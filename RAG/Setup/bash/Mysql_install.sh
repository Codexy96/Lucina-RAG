#!/bin/bash

# 更新软件包列表
echo "更新软件包列表..."
sudo apt-get update

# 安装 MySQL
echo "安装 MySQL..."
sudo apt-get install -y mysql-server

# 检查 MySQL 服务状态
echo "检查 MySQL 服务是否正在运行..."
sudo service mysql status

# 启动 MySQL 服务（如果未运行）
echo "启动 MySQL 服务..."
sudo service mysql start

# 设置 MySQL 安全性
#echo "设置 MySQL 安全性..."
#sudo mysql_secure_installation

# 提示安装成功
echo "MySQL 安装成功！"
# 将 root 用户的身份验证方法设置为 mysql_native_password，并设置默认密码
echo "设置 root 用户密码..."
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'zhiyeAI';"
# 创建数据库 RAG
echo "预先创建数据库 RAG...您可以根据需要创建其他数据库。"
sudo mysql -u root -p'zhiyeAI' -e "CREATE DATABASE RAG;"
# 提供连接信息
echo "您可以使用以下命令连接到 MySQL："
echo "mysql -u root -p"
echo "密码：zhiyeAI"
