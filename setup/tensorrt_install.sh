#!/bin/bash

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
    echo "请检查cudnn版本，然后手动选择TensorRT版本安装，查看cudnn版本命令：```dpkg -l | grep libcudnn```如果是9开头，则安装9.×.×版本，如果是10开头，则安装10.×.×版本，以此类推。如果显示错误，请先到nvidia官网下载对应版本的cudnn，然后再安装tensorrt。"
    exit 1
fi

# 安装 TensorRT
echo "安装 TensorRT $tensorrt_version..."
pip install tensorrt=="$tensorrt_version" -U --pre --extra-index-url https://pypi.nvidia.com

# 完成
echo "tensorrt库添加成功，请按提示在您的 Python 环境中使用```import tensorrt``` 进行测试，版本号为： $tensorrt_version"
