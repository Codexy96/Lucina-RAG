import os
file_dir=os.path.dirname(__file__)
class Mysql:

    def __init__(self):
        import mysql.connector
        import configparser
        config=configparser.ConfigParser()
        config.read(os.path.join(file_dir,"config.ini"))
        self.connection=mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            password=config['mysql']['password'],
            database=config['mysql']['database']
        )
        print("Connected to MySQL database")
    def create(self, name, fields):
        """
        创建表
        参数：
        name: 表名
        fields: 字段列表，格式为[字段1,字段2,...]，必须包含slice_id和content字段，其中slice_id将作为主键
        """
        # 检查是否包含必须的字段
        if 'slice_id' not in fields or 'content' not in fields:
            raise ValueError("字段列表必须包含'slice_id'和'content'字段")

        sql = "CREATE TABLE IF NOT EXISTS `" + name + "` ("
        for field in fields:
            if field == 'slice_id':
                sql += "`" + field + "` CHAR(64),"
            elif field == 'content':
                sql += "`" + field + "` TEXT,"
            else:
                sql += "`" + field + "` TEXT,"
        sql = sql[:-1] + ", PRIMARY KEY (`slice_id`))"
        print(sql)
        try:
            cursor=self.connection.cursor()
            cursor.execute(sql)
            self.connection.commit()
            print("Table "+name+" created")
        except Exception as e:
            print(f"创建表时出错：{e}")
            



    def insert(self,name,data):
        from mysql.connector import Error
        """
        插入数据
        参数：
            name: 表名
            data: 数据列表，一条数据是字段名和值的键值对字典，格式为[{字段名1:值1,字段名2:值2},...]
        """
        if not data:
            print("No data to insert")
            return
        columns=','.join(data[0].keys())
        values=','.join(['%s']*len(data[0]))
        sql="INSERT INTO "+name+" ("+columns+") VALUES ("+values+")"
        cursor=self.connection.cursor()
        try:
            #执行批量插入，使用executemany()方法
            cursor.executemany(sql,[tuple(d.values()) for d in data])
            self.connection.commit()
            print("Data inserted into table "+name)
        except Error as e:
            print("Error inserting data into table "+name+": "+str(e))
    def delete(self,name):
        """
        删除表操作
        """
        sql="DROP TABLE IF EXISTS "+name
        cursor=self.connection.cursor()
        cursor.execute(sql)
        self.connection.commit()
        print("Table "+name+" deleted")

    def search(self,name,fields,where=None):
        """
        查询数据
        参数：
            name: 表名
            fields: 被选取的字段列表，格式为[字段名1,字段名2,...]
            where: 条件，格式为{字段名:值}，默认为空，表示查询所有数据
        返回值：
            一个包含查询结果的列表，每个元素是一条数据，格式为{字段名1:值1,字段名2:值2}
        """
        sql = f"SELECT {', '.join(fields)} FROM {name}"
        if where:
            conditions = ' AND '.join([f"{key} = %s" for key in where.keys()])
            sql += f" WHERE {conditions}"
        cursor=self.connection.cursor()
        cursor.execute(sql, tuple(where.values()) if where else ())
        results =cursor.fetchall()

        # 将结果格式化为字典列表
        return [dict(zip(fields, row)) for row in results]
    def show(self):
        """
        获取所有表名的列表
        """
        cursor=self.connection.cursor()
        cursor.execute("SHOW TABLES")
        results = cursor.fetchall()
        return [row[0] for row in results]
        
        
if __name__=="__main__":
    """依据多个slice_id查询对应的content的示例"""
    slice_ids=[1,2,3,4,5]
    where_condition={"slice_id":slice_ids}
    mysql_instance=Mysql()
    result=mysql_instance.search("test_table",["slice_id","content"],where_condition)
    print(result)
        
    


        