#!/bin/bash
# 依赖项检查
# 检查是否安装必要的工具
if ! command -v wget &> /dev/null; then
    echo "wget 未安装，请先安装 wget"
    exit 1
fi

# 创建 env 文件以存储信息
env_file="environment_info.env"
echo "创建环境信息文件 $env_file ..."
echo "MYSQL_ROOT_PASSWORD=zhiyeAI" > "$env_file"

# -----------------------------------------
# 安装 Milvus
# -----------------------------------------
FILE="milvus_2.3.10-1_amd64.deb"

# 检查文件是否存在
if [ -f "$FILE" ]; then
    echo "$FILE 已存在，跳过下载。"
else
    echo "未找到 $FILE，正在下载..."
    wget https://github.com/milvus-io/milvus/releases/download/v2.3.10/$FILE
fi

sudo apt-get update
sudo dpkg -i "$FILE"
export MILVUSCONF=/etc/milvus/configs
PORT=19530

# 清空端口占用
if lsof -i:$PORT; then
    echo "端口 $PORT 被占用，正在终止占用进程..."
    PID=$(lsof -ti:$PORT)
    kill -9 $PID
    echo "已终止占用端口 $PORT 的进程 $PID。"
else
    echo "端口 $PORT 未被占用。"
fi
mkdir -p logs
> logs/milvus.log  # 清空日志文件
nohup milvus run standalone > logs/milvus.log 2>&1 &

echo "Milvus 安装成功并已启动，访问地址为：http://localhost:19530"

# -----------------------------------------
# 安装 MySQL
# -----------------------------------------
echo "安装 MySQL..."
sudo apt-get install -y mysql-server
> logs/mysql.log  # 清空日志文件
# 启动 MySQL 服务
sudo service mysql start > logs/mysql.log 2>&1 &
echo "设置 root 用户密码..."
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'zhiyeAI';"

# 添加 MySQL 信息到 env 文件
echo "MYSQL_HOST=localhost" >> "$env_file"
echo "MYSQL_PORT=3306" >> "$env_file"
echo "MYSQL_ROOT_PASSWORD=zhiyeAI" >> "$env_file"

echo "MySQL 安装成功！您可以使用 mysql -u root -p 连接，密码为 zhiyeAI。"

# -----------------------------------------
# 安装 Elasticsearch
# -----------------------------------------
echo "正在安装 Elasticsearch..."
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/elasticsearch.gpg
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update
sudo apt-get install elasticsearch

sudo useradd -r -s /bin/false elasticsearch
sudo chown -R elasticsearch:elasticsearch /var/lib/elasticsearch
sudo chown -R elasticsearch:elasticsearch /var/log/elasticsearch
echo "xpack.security.enabled: false" | sudo tee -a /etc/elasticsearch/elasticsearch.yml
mkdir -p logs
> logs/elasticsearch.log  # 清空日志文件
sudo -u elasticsearch nohup /usr/share/elasticsearch/bin/elasticsearch > logs/elasticsearch.log 2>&1 &

echo "Elasticsearch 安装成功并已启动，连接地址：http://localhost:9200"

# -----------------------------------------
# 安装 TensorRT
# -----------------------------------------
# 提示用户输入虚拟环境名称
read -p "请输入虚拟环境名称: " env_name

# 创建虚拟环境
python3 -m venv "$env_name"

# 激活虚拟环境
source "$env_name/bin/activate"

# 安装 TensorRT 前的准备
echo "克隆 TensorRT 仓库..."
git clone https://gitee.com/yunfeiliu/TensorRT.git
cd TensorRT || { echo "切换到 TensorRT 目录失败"; exit 1; }

# 安装依赖项
echo "安装依赖项..."
pip install -r requirements.txt

# 检查 CUDA 版本
cuda_version=$(dpkg -l | grep libcudnn | awk -F' ' '{print $3}' | awk -F'+' '{print $1}')  # 获取 CUDA 版本
echo "CUDA 版本: $cuda_version"

# 根据 CUDA 版本选择 TensorRT 版本
if [[ $cuda_version == 8* ]]; then
    tensorrt_version="8.6.0"
elif [[ $cuda_version == 10* ]]; then
    tensorrt_version="10.6.0"
else
    echo "不支持的 CUDA 版本，请手动安装适合的 TensorRT 版本。"
    exit 1
fi

# 安装 TensorRT
echo "安装 TensorRT $tensorrt_version..."
pip install tensorrt=="$tensorrt_version" -U --pre --extra-index-url https://pypi.nvidia.com

# 完成
echo "TensorRT 安装成功，请按提示在您的 Python 环境中使用 'import tensorrt' 进行测试，版本号为：$tensorrt_version"

# 提示用户查看 env 文件
echo "作业信息已写入 $env_file"
