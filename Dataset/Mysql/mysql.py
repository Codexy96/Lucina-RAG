import os
import sys
from dotenv import load_dotenv
# 获取父目录并添加到系统路径
parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)

# 加载上一级文件夹中的 .env 文件
dotenv_path = os.path.join(parent_dir, '.env')
load_dotenv(dotenv_path)
import mysql.connector
from mysql.connector import Error
class MySQLDataset:
    def __init__(self):
        """初始化 MySQL 连接"""
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DATABASE')
            )
            if self.connection.is_connected():
                print("成功连接到 MySQL 数据库")
        except Error as e:
            print(f"连接到 MySQL 数据库时发生错误: {e}")

    def create_table(self, table_name):
        """创建表"""
        try:
            cursor = self.connection.cursor()
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                FULL_TEXT_HASH VARCHAR(64) NOT NULL,
                summary_vector BLOB NOT NULL
            )
            """
            cursor.execute(create_table_query)
            print(f"表 '{table_name}' 创建成功")
        except Error as e:
            print(f"创建表时发生错误: {e}")

    def insert_data(self, table_name, full_text_hash, summary_vector):
        """插入数据"""
        try:
            cursor = self.connection.cursor()
            insert_query = f"INSERT INTO {table_name} (FULL_TEXT_HASH, summary_vector) VALUES (%s, %s)"
            cursor.execute(insert_query, (full_text_hash, summary_vector))
            self.connection.commit()
            print(f"成功插入到表 '{table_name}' 中")
        except Error as e:
            print(f"插入数据时发生错误: {e}")

    def query_data(self, table_name):
        """查询数据"""
        try:
            cursor = self.connection.cursor()
            select_query = f"SELECT * FROM {table_name}"
            cursor.execute(select_query)
            records = cursor.fetchall()
            for row in records:
                print(row)
        except Error as e:
            print(f"查询数据时发生错误: {e}")

    def delete_table(self, table_name):
        """删除表"""
        try:
            cursor = self.connection.cursor()
            delete_table_query = f"DROP TABLE IF EXISTS {table_name}"
            cursor.execute(delete_table_query)
            print(f"表 '{table_name}' 已删除")
        except Error as e:
            print(f"删除表时发生错误: {e}")

    def close_connection(self):
        """关闭数据库连接"""
        if self.connection.is_connected():
            self.connection.close()
            print("数据库连接已关闭")

# 示例用法
if __name__ == '__main__':
    # 初始化 MySQLDataset 类
    db = MySQLDataset(host='localhost', user='your_username', password='your_password', database='your_database')

    # 创建表
    db.create_table('law_data')

    # 插入数据示例
    db.insert_data('law_data', 'hash_1', 'vector_data_1')
    db.insert_data('law_data', 'hash_2', 'vector_data_2')

    # 查询数据
    print("查询数据:")
    db.query_data('law_data')

    # 删除表
    db.delete_table('law_data')

    # 关闭连接
    db.close_connection()
