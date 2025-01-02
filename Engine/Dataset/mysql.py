import os
file_dir=os.path.dirname(__file__)
config_path=os.path.join(file_dir,"../../Setup/config.yaml")
import json
class Mysql:

    def __init__(self):
         # 读取配置文件
        import yaml
        import mysql.connector
        with open(config_path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.connection = mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            password=config['mysql']['password'],
            port=config['mysql'].get('port', 3306),
         
        )
        self.cursor = self.connection.cursor()
        print("Connected to MySQL database")
        self.log_file = os.path.join(file_dir, "kb_operations_log.json")
        # 读取已有的日志记录
        self.load_log()

    def create_kb(self, name, description):
        db_name = f"kb_{name}"
        self.cursor.execute(f"CREATE DATABASE {db_name};")
        self.cursor.execute(f"USE {db_name};")
        # 创建相应的表结构
        self.cursor.execute("CREATE TABLE IF NOT EXISTS records (id INT AUTO_INCREMENT PRIMARY KEY, content TEXT);")
        self.connection.commit()
        self.log_operation("create", name, description)
        print(f"知识库 {name} 创建成功！")

    def delete_kb(self, name):
        db_name = f"kb_{name}"
        self.cursor.execute(f"DROP DATABASE {db_name};")
        self.connection.commit()
        self.log_operation("delete", name)
        print(f"知识库 {name} 删除成功！")

    def log_operation(self, operation, kb_name, description=None):
        log_entry = {
            "operation": operation,
            "kb_name": kb_name,
            "description": description,
        }
        self.operations_log.append(log_entry)
        # 将日志写入文件
        with open(self.log_file, 'w') as f:
            json.dump(self.operations_log, f, ensure_ascii=False, indent=4)

    def load_log(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                self.operations_log = json.load(f)
        else:
            self.operations_log = []

    def exists_kb(self, name):
        db_name = f"kb_{name}"
        self.cursor.execute("SHOW DATABASES;")
        databases = [db[0] for db in self.cursor.fetchall()]
        return db_name in databases

    def get_all_kb(self):
        self.cursor.execute("SHOW DATABASES;")
        databases = [db[0] for db in self.cursor.fetchall()]
        # 过滤出以 kb_ 开头的数据库
        kb_databases = [db for db in databases if db.startswith("kb_")]
        return kb_databases

    
        

        
    


        