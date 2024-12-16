如果是镜像启动，最好使用自带的tensorrt镜像。
如果在工作环境中找不到linbvinda.so的文件，可以使用以下命令自查
查找文件是否存在
sudo find / -name "libnvinfer.so.8" 2>/dev/null
创建符号链接，可选
sudo ln -s /root/TensorRT-8.6.1.6/targets/x86_64-linux-gnu/lib/libnvinfer.so.8 /usr/lib/x86_64-linux-gnu/libnvinfer.so.8
配置库路径
echo 'export LD_LIBRARY_PATH=/root/TensorRT-8.6.1.6/targets/x86_64-linux-gnu/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
更新config
echo '/root/TensorRT-8.6.1.6/targets/x86_64-linux-gnu/lib' | sudo tee -a /etc/ld.so.conf
sudo ldconfig
验证安装
python
>>> import tensorrt


tensorrt引擎化时，向量模型需要保持最大精度，建议模型以torch.float32加载，同时使用TF32来生成tensorrt引擎。

重排序模型精度要求可以下降。
