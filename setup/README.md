注意事项：

当前硬盘磁盘空间不足时，需要将挂载盘更换

对于ES:
备份数据
sudo tar -czvf elasticsearch_backup.tar.gz /var/lib/elasticsearch
修改配置文件
sudo vim /etc/elasticsearch/elasticsearch.yml
path.data: /mnt/new_disk/elasticsearch

创建新的目录并设置权限
sudo mkdir -p /mnt/new_disk/elasticsearch
sudo chown -R elasticsearch:elasticsearch /mnt/new_disk/elasticsearch

sudo chmod -R 755 /root/autodl-tmp/elasticsearch
移动现有数据到新数据
sudo rsync -av /var/lib/elasticsearch/ /mnt/new_disk/elasticsearch/

#对于mysql
sudo mv /var/lib/mysql /newdisk/mysql
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
修改：
log_error=/root/autodl-tmp/mysql/error.log



对于ES安装，需要先安装jdk

使用  java -version 命令检查

如果报错，sudo apt-get install -y openjdk-11-jdk，运行该命令安装

创建用户组，需要为用户提供主目录

在根目录执行

sudo mkdir /home/elasticsearch
sudo chown elasticsearch:elasticsearch /home/elasticsearch
sudo usermod -d /home/elasticsearch elasticsearch

如果该elasticsearch用户不可用，则重新创建用户尝试