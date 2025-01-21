import yaml
from elasticsearch import AsyncElasticsearch, exceptions
from elasticsearch.exceptions import ConnectionError, NotFoundError
import time
import logging
import os
import asyncio

# 加载YAML配置
file_dir = os.path.dirname(__file__)
config_file = os.path.join(file_dir, 'config.yml')

def load_config(config_file=config_file):
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

# 加载配置并返回
config = load_config()
ES_URL = config['ELASTICSEARCH']['url']
ES_INDEX = config['ELASTICSEARCH']['index']

# 创建Elasticsearch客户端，增加重连设置
es = AsyncElasticsearch(
    [ES_URL],
    max_retries=5,                # 最大重试次数
    retry_on_timeout=True,        # 超时重试
    request_timeout=10,           # 请求超时（秒）
)

async def search_in_es(index_name, query, size=3):
    search_query = {
        "query": {
            "match": {
                "content": query
            }
        },
    }
    
    try:
        response = await es.search(index=index_name, body=search_query, size=size)
        results = []
        for hit in response['hits']['hits']:
            results.append(hit['_source'])
        return results

    except (ConnectionError, NotFoundError) as e:
        logging.error(f"连接出现问题: {e}")
        return []

async def search_in_es_with_threshold(index_name, query, threshold=1.0, size=10):
    search_query = {
        "query": {
            "bool": {
                "must": {
                    "match": {
                        "content": query
                    }
                },
            }
        },
        'size': size
    }

    max_retries = 3  # 最大重试次数
    for attempt in range(max_retries):
        try:
            response = await es.search(index=index_name, body=search_query)
            results = []
            for hit in response['hits']['hits']:
                if hit['_score'] >= threshold:
                    results.append(hit['_source'])
            return results
        
        except (ConnectionError, NotFoundError) as e:
            logging.error(f"连接出现问题: {e},尝试第{attempt+1}次重试...")
            await asyncio.sleep(0.1)  # 使用异步睡眠

    return "重试次数已用完，无法连接到Elasticsearch服务。"

async def search(index_name, query, top_k=3, threshold=10):
    results = await search_in_es_with_threshold(index_name, query, threshold=threshold, size=top_k)
    if results:
        for result in results:
            publishtime = result.get('publish_time', '未知')
            effectivetime = result.get('effective_time', '未知')
            source = result.get('source', '未知')
            publish_unit = result.get('publish_unit', '未知')
            content = result.get('content', '无内容')
            content += f"\n<llmlingua,compress=False>发布时间：{publishtime}\t生效时间：{effectivetime}\t发布单位：{publish_unit}\t信息来源：{source}</llmlingua>"
            result['content'] = content
        return results
    else:
        return "No results found"

# 如果需要在脚本中直接运行，则使用asyncio.run
if __name__ == '__main__':
    async def main():
        query = "中国对外的外交政策一个中国立场，指的是什么？"
        top_k = 3
        threshold = 1  # 设定合理的阈值
        results = await search(ES_INDEX, query, top_k, threshold)
        print(results)

    asyncio.run(main())
