wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/elasticsearch.gpg
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update
sudo apt-get install elasticsearch
sudo useradd -r -s /bin/false elasticsearch
sudo chown -R elasticsearch:elasticsearch /var/lib/elasticsearch
sudo chown -R elasticsearch:elasticsearch /var/log/elasticsearch
echo "xpack.security.enabled: false" | sudo tee -a /etc/elasticsearch/elasticsearch.yml
#如果是单机运行，请取消下方的注释
#echo "discovery.seed_hosts: \"127.0.0.1:9300\"" | sudo tee -a /etc/elasticsearch/elasticsearch.yml
#echo "cluster.initial_master_nodes: [\"node-1\"]" | sudo tee -a /etc/elasticsearch/elasticsearch.yml
#删除discovery.seed_hosts配置项
echo "discovery.seed_hosts: \"\"" | sudo tee -a /etc/elasticsearch/elasticsearch.yml
> logs/elasticsearch.log  # 清空日志文件

sudo  -u elasticsearch nohup /usr/share/elasticsearch/bin/elasticsearch > logs/elasticsearch.log 2>&1 &
echo "Elasticsearch 安装成功并设置为后台运行"
#&> elasticsearch.log &
#echo "Elasticsearch 安装成功并设置为系统服务启动！"
echo "请查看日志文件 elasticsearch.log 确认 Elasticsearch 是否正常运行。"
echo "Elasticsearch 连接地址：http://localhost:9200"