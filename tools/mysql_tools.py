# 数据库工具
# 1. list_sql_tables: 列出数据库中所有可用的表，这是了解数据库结构的第一步。
# 2. get_table_data: 读取指定表的前100行数据，用于快速预览数据内容。
# 3. execute_sql_query: 执行自定义SQL查询。当需要复杂的筛选、联接或聚合时使用此工具。
import os
from unittest import result

from dotenv import load_dotenv
from mysql.connector import connect

from api.monitor import monitor
from utils.logger_utils import logger

load_dotenv(override=True)

# 产生用于连接数据的配置的函数
def _get_db_config()->dict:
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),  # 主机号
        "port": int(os.getenv("MYSQL_PORT", "3306")),  # 端口号
        "user": os.getenv("MYSQL_USER"),  # 用户名
        "password": os.getenv("MYSQL_PASSWORD"),  # 密码
        "database": os.getenv("MYSQL_DATABASE"),  # 数据库名
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),  # 字符集
    }

    # 过滤掉config中值为空的项
    config = {k:v for k,v in config.items() if v}
    # 必须的key列表
    required_keys = ["user", "password", "database"]
    # 得到缺少的Key列表
    missing_keys = [k for k in required_keys if k not in config]
    # 如果它有值，说明缺少必须的key, 抛出错误，提示缺少哪些key
    if missing_keys:
        raise ValueError(f"缺少必须的配置项：{missing_keys}")

    return config

# 得到连接配置
_db_config = _get_db_config()

# 1. list_sql_tables: 列出数据库中所有可用的表，这是了解数据库结构的第一步。
def list_sql_tables()-> str:
    """
        列出数据库中所有可用的表
    :return:   有表： 可用的表：a,b,c  没表：没有可用的表
    """
    logger.info("======获取表名列表========")
    monitor.report_tool("list_sql_tables", {})
    try:
        # 连接数据，得到连接对象
        with connect(**_db_config) as conn:
            # 通过连接到游标对象
            with conn.cursor() as cursor:
                # 通过游标执行查询表信息的SQL
                cursor.execute("show tables;")
                # 获取结果数据
                rows = cursor.fetchall()
                # 如果没有表，返回： “没有可用的表”
                if not rows:
                    return "没有可用的表"
                # 有表， 返回： “可用的表：a,b,c”
                # print(rows) # [('drugs',), ('inventory',), ('sales_records',)]
                table_names_str = ",".join([row[0] for row in rows])
                result = f"可用的表：{table_names_str}"
                logger.info(result)
                return result

    except Exception as e:
        return f"操作数据库失败: {str(e)}"


# 2. get_table_data: 读取指定表的前100行数据，用于快速预览数据内容。
def get_table_data(table_name:str)->str:
    """
        获取指定表名的前至多100条数据列表，同时带字段名列表
        :param table_name: 表名
        :return:

         表数据
        id   name    age
        1  二狗子    18
        2  驴蛋蛋    19

        返回的结果数据： "id,name,age\n1,二狗子,18\n2,驴蛋蛋,19"
    """
    logger.info(f"======获取{table_name}表的前100行数据========")
    monitor.report_tool("get_table_data", {"table_name": table_name})
    try:
        # 连接数据，得到连接对象
        with connect(**_db_config) as conn:
            # 通过连接到游标对象
            with conn.cursor() as cursor:
                # 通过游标执行查询表信息的SQL
                cursor.execute(f"select * from {table_name} limit 100;")
                # 获取结果数据
                rows = cursor.fetchall()
                # 如果没有数据，返回： “xxx表中没有任何数据”
                if not rows:
                    return f"{table_name}表中没有任何数据"
                # 有数据， 返回： "id,name,age\n1,二狗子,1\n2,驴蛋蛋,19"
                print(type(rows[0]), rows)
                # print(cursor.column_names)
                column_names_str = ",".join(cursor.column_names)
                # map(str, row) 将列表中的所有元素都转换为str类型
                row_values_str = "\n".join([",".join(map(str, row)) for row in rows])
                # print(row_values_str)
                result = column_names_str + "\n" + row_values_str

                logger.info(f"查询{table_name}的数据列表：{result}")
                return result

    except Exception as e:
        return f"操作数据库失败: {str(e)}"


# 3. execute_sql_query: 执行自定义SQL查询。当需要复杂的筛选、联接或聚合时使用此工具。
def execute_sql_query(sql:str)->str:
    """
        根据指定sql执行，返回查询的结果
        :param sql: 由大模型生成的sql
        :return:  字段列表和数据列表的字符串
    """
    logger.info(f"----正在执行SQL：{sql}")
    monitor.report_tool("execute_sql_query", {"sql": sql})
    try:
        # 连接数据，得到连接对象
        with connect(**_db_config) as conn:
            # 通过连接到游标对象
            with conn.cursor() as cursor:
                # 通过游标执行查询表信息的SQL
                cursor.execute(sql)
                # 获取结果数据
                rows = cursor.fetchall()
                # 如果没有数据，返回： “xxx表中没有任何数据”
                if not rows:
                    return f"执行语句{sql}, 没有任何数据"
                # 有数据， 返回： "id,name,age\n1,二狗子,1\n2,驴蛋蛋,19"
                print(type(rows[0]), rows)
                # print(cursor.column_names)
                column_names_str = ",".join(cursor.column_names)
                # map(str, row) 将列表中的所有元素都转换为str类型
                row_values_str = "\n".join([",".join(map(str, row)) for row in rows])
                # print(row_values_str)
                result = column_names_str + "\n" + row_values_str

                logger.info(f"执行{sql}的数据列表：{result}")
                return result

    except Exception as e:
        return f"操作数据库失败: {str(e)}"

if __name__ == '__main__':
    # print(_get_db_config())
    # list_sql_tables()
    # get_table_data("drugs")
    execute_sql_query("select * from drugs")