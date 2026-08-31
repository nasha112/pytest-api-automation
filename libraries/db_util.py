import pymysql
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 环境变量

class DBClient:
    def __init__(self):
        self.connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor  # 返回字典格式，方便断言
        )
        self.cursor = self.connection.cursor()

    def fetch_one(self, sql, params=None):
        """执行查询并返回一条记录"""
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def execute(self, sql, params=None):
        """执行增删改操作（通常我们只用查询，因为DELETE会由API清理）"""
        self.cursor.execute(sql, params)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()