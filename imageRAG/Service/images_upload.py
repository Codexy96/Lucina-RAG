"""
该脚本用于创建图片向量数据库
指定图片存储的根目录自动将图片转换为向量并导入数据库

支持：
直接将文件夹命令作为集合
当前根目录下出现多个文件夹时，可以选择是否为每个文件夹创建集合（这将包括递归得到的全部子目录）

默认使用IVF_FLAT索引，向量维度为1024，请根据实际情况调整参数

默认使用root_path作为集合名称，如果该文件夹下存在图片，则会自动创建分片名：default 

含有图片的子文件夹将同样作为分片存储。


"""
#---------------------------------

root_path='./images' # 图片根目录

#--------------------------------


#-------------------------------------

#############注意事项#################

#注意事项：哈希值由图片内容生成，尽可能减少重复图片的导入。
#或者将embedding作为primary键导入，将有效避免重复导入。

#本脚本暂时采取第一种方案。

#-----------------------------------


import os
import argparse
from RAG.Engine.Dataset.milvus import Milvus, Collection, Partition
from script.ImageRAG.Engine.MultiEmbedding import Embedding
import hashlib

def run(root_path):
    model = Embedding()
    dataset = Milvus()
    image_loader = get_image_loader(root_path)
    root_name = os.path.basename(root_path)

    # 创建集合
    dataset.create(name=root_name, fields=["slice_id", "vector", "path"], core_dict={"method": "IVF_FLAT", 'dim': 1024})
    # 获取partition类
    partition = Partition(client=dataset.client, collection_name=root_name)

    # 迭代图片
    for partition_name, count, loader in image_loader:
        try:
            # 创建分片
            if partition_name not in partition.partitions:
                partition.create(partition_name)
            # 导入向量
            embed_list =model.encode_images(loader)
            # 获取去除根目录路径之后的图片路径和slice_id，组合成插入数据的最终格式,embed需要转化为list
            #这里经过实践，应该将图片编码作为slice_id，防止插入重复图片
            data_list = [{"slice_id": generate_image_hash(path), "vector": embed_list[i], "path": os.path.relpath(path, root_path)} #计算path相对于root_path的相对路径
                         for i, path in enumerate(loader) if embed_list[i] is not None ]  #or embed_list[i]!=[]
            #print(len(data_list))
            # 插入数据
            partition.insert(partition_name=partition_name, data=data_list)
            print(f"向{root_name}集合导入{len(data_list)}张图片，所属分片：{partition_name},无效图片：{count-len(loader)}张")
        except Exception as e:
            print(f"{partition_name}文件下图片导入失败，请检查图片格式或路径是否正确之后重新运行脚本")
            raise e


def generate_hash(text):
    hash_object = hashlib.sha256()
    hash_object.update(text.encode('utf-8'))
    return hash_object.hexdigest()

def generate_image_hash(image_path):
    from PIL import Image
    import imagehash
    with Image.open(image_path) as img:
        #生成平均哈希
        avg_hash=imagehash.average_hash(img)
    return str(avg_hash)

def get_image_loader(root_path):
    # 根据root_path迭代文件夹内所有的图片，包括子文件夹以及当前文件夹子文件夹下的图片
    # 图片仅支持：jpg、jpeg、png格式
    subs = os.listdir(root_path)
    loader = []
    dataset_name = os.path.basename(root_path)
    for sub in subs:
        sub_path = os.path.join(root_path, sub)
        if os.path.isdir(sub_path):
            yield from get_image_loader(sub_path)
        elif sub.endswith(('.jpg', '.jpeg', '.png')):
            # 添加至loader队列
            loader.append(sub_path)
            if len(loader) == 10:
                # 返回：集合名称、队列数量和loader队列
                yield dataset_name, len(loader), loader
                loader = []

    # 返回最后一批数据
    if loader:
        yield dataset_name, len(loader), loader


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='图片导入脚本')
    parser.add_argument('--root_path', type=str, help='图片根目录路径',required=True)
    args = parser.parse_args()

    run(args.root_path)
"""
milvus插入主键不可重复
"""
#python images_upload.py --root_path ./images     
