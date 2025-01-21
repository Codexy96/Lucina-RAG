""" 
rerank api，统一对多个开源rank模型进行接口调用
"""
import sys
import importlib

# 添加模块路径

sys.path.append(r"../../../cores/model/Rerank")
class RerankAPI(object):
    """ 
    可选择的rerank core有：
    - BGE : 支持100种语言，输入长度可达8192
    - BCE : 中英双语，专门为业务场景的RAG适配
    """
    def __init__(self, core):
        core_module = importlib.import_module(f"{core}")
        core_class = getattr(core_module, core.upper())
        self.core = core_class()
    def run(self, input_data:list[ dict[str, str] ], top_k:int=10):
        """
        参数：
         - input_data :输入数据，list[ {key:value} ]，其中，文本键必须使用content标识
        - top_k : 返回的结果数，int，默认10
        返回：
          返回排序过后并top_k筛选后的input_data, 其他保持不变


        """
        # 调用core的rerank方法
        output_data = self.core.rerank(input_data, top_k)
        return output_data
    

if __name__ == "__main__":
    try:
        api = RerankAPI("BCE")  # 测试用例
    except ImportError as e:
        print(f"导入模块失败: {e}")
    except AttributeError as e:
        print(f"获取核心类失败: {e}")