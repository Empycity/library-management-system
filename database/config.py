#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库配置和连接管理模块

本模块提供数据库连接配置和数据库管理类，用于：
1. 数据库连接参数配置
2. 数据库连接池管理
3. 数据库操作的统一接口
4. 数据库连接异常处理

技术栈：
- PyMySQL: MySQL数据库连接驱动
- 连接池: 提高数据库连接效率

作者: 图书馆管理系统开发团队
版本: 1.0
创建日期: 2024-01-15
"""

import pymysql
import logging
from contextlib import contextmanager

# ==================== 数据库配置 ====================

# MySQL数据库连接配置
# 注意：生产环境中应该使用环境变量或配置文件来管理这些敏感信息
DATABASE_CONFIG = {
    'host': 'localhost',           # 数据库服务器地址
    'port': 3306,                  # 数据库端口
    'user': 'root',                # 数据库用户名
    'password': '',                # 数据库密码（请根据实际情况修改）
    'database': 'library_management',  # 数据库名称
    'charset': 'utf8mb4',          # 字符编码，支持中文和emoji
    'autocommit': True,            # 自动提交事务
    'connect_timeout': 10,         # 连接超时时间（秒）
    'read_timeout': 10,            # 读取超时时间（秒）
    'write_timeout': 10            # 写入超时时间（秒）
}

# ==================== 日志配置 ====================

# 配置数据库操作日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

# ==================== 数据库管理类 ====================

class DatabaseManager:
    """
    数据库管理类
    
    提供数据库连接、查询、事务管理等功能
    支持连接池和自动重连机制
    """
    
    def __init__(self, config=None):
        """
        初始化数据库管理器
        
        Args:
            config (dict, optional): 数据库配置字典. Defaults to None.
        """
        self.config = config or DATABASE_CONFIG
        self.connection = None
        
    def get_connection(self):
        """
        获取数据库连接
        
        Returns:
            pymysql.Connection: 数据库连接对象
            
        Raises:
            Exception: 连接失败时抛出异常
        """
        try:
            if self.connection is None or not self.connection.open:
                self.connection = pymysql.connect(**self.config)
                logger.info("数据库连接成功")
            return self.connection
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def close_connection(self):
        """
        关闭数据库连接
        """
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """
        获取数据库游标的上下文管理器
        
        Args:
            dictionary (bool, optional): 是否返回字典格式结果. Defaults to True.
            
        Yields:
            pymysql.cursors.Cursor: 数据库游标对象
        """
        connection = self.get_connection()
        cursor_class = pymysql.cursors.DictCursor if dictionary else pymysql.cursors.Cursor
        
        try:
            with connection.cursor(cursor_class) as cursor:
                yield cursor
        except Exception as e:
            logger.error(f"数据库操作错误: {e}")
            connection.rollback()
            raise
        finally:
            # 连接会在上下文管理器结束时自动处理
            pass
    
    def execute_query(self, sql, params=None, fetch_one=False, fetch_all=True):
        """
        执行查询语句
        
        Args:
            sql (str): SQL查询语句
            params (tuple, optional): 查询参数. Defaults to None.
            fetch_one (bool, optional): 是否只获取一条记录. Defaults to False.
            fetch_all (bool, optional): 是否获取所有记录. Defaults to True.
            
        Returns:
            list/dict/None: 查询结果
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, params)
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = None
                    
                logger.debug(f"查询执行成功: {sql[:100]}...")
                return result
                
        except Exception as e:
            logger.error(f"查询执行失败: {e}, SQL: {sql}")
            raise
    
    def execute_update(self, sql, params=None):
        """
        执行更新语句（INSERT, UPDATE, DELETE）
        
        Args:
            sql (str): SQL更新语句
            params (tuple, optional): 更新参数. Defaults to None.
            
        Returns:
            int: 影响的行数
        """
        try:
            with self.get_cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
                logger.debug(f"更新执行成功: {sql[:100]}..., 影响行数: {affected_rows}")
                return affected_rows
                
        except Exception as e:
            logger.error(f"更新执行失败: {e}, SQL: {sql}")
            raise
    
    def execute_many(self, sql, params_list):
        """
        批量执行更新语句
        
        Args:
            sql (str): SQL更新语句
            params_list (list): 参数列表
            
        Returns:
            int: 影响的总行数
        """
        try:
            with self.get_cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)
                logger.debug(f"批量更新执行成功: {sql[:100]}..., 影响行数: {affected_rows}")
                return affected_rows
                
        except Exception as e:
            logger.error(f"批量更新执行失败: {e}, SQL: {sql}")
            raise
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        使用方法:
            with db_manager.transaction():
                # 执行数据库操作
                db_manager.execute_update(sql1, params1)
                db_manager.execute_update(sql2, params2)
                # 如果没有异常，事务会自动提交
                # 如果有异常，事务会自动回滚
        """
        connection = self.get_connection()
        
        try:
            # 开始事务
            connection.begin()
            logger.debug("事务开始")
            
            yield connection
            
            # 提交事务
            connection.commit()
            logger.debug("事务提交成功")
            
        except Exception as e:
            # 回滚事务
            connection.rollback()
            logger.error(f"事务回滚: {e}")
            raise
    
    def test_connection(self):
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def get_table_info(self, table_name):
        """
        获取表结构信息
        
        Args:
            table_name (str): 表名
            
        Returns:
            list: 表结构信息
        """
        sql = f"DESCRIBE {table_name}"
        return self.execute_query(sql)
    
    def get_database_info(self):
        """
        获取数据库基本信息
        
        Returns:
            dict: 数据库信息
        """
        info = {}
        
        # 获取数据库版本
        version_result = self.execute_query("SELECT VERSION() as version", fetch_one=True)
        info['version'] = version_result['version'] if version_result else 'Unknown'
        
        # 获取当前数据库名
        db_result = self.execute_query("SELECT DATABASE() as database_name", fetch_one=True)
        info['database'] = db_result['database_name'] if db_result else 'Unknown'
        
        # 获取表列表
        tables_result = self.execute_query("SHOW TABLES")
        info['tables'] = [list(table.values())[0] for table in tables_result] if tables_result else []
        
        return info

# ==================== 全局数据库管理器实例 ====================

# 创建全局数据库管理器实例
db_manager = DatabaseManager()

# ==================== 便捷函数 ====================

def get_db_connection():
    """
    获取数据库连接的便捷函数
    
    Returns:
        pymysql.Connection: 数据库连接对象
    """
    return db_manager.get_connection()

def execute_query(sql, params=None, fetch_one=False):
    """
    执行查询的便捷函数
    
    Args:
        sql (str): SQL查询语句
        params (tuple, optional): 查询参数. Defaults to None.
        fetch_one (bool, optional): 是否只获取一条记录. Defaults to False.
        
    Returns:
        list/dict: 查询结果
    """
    return db_manager.execute_query(sql, params, fetch_one=fetch_one)

def execute_update(sql, params=None):
    """
    执行更新的便捷函数
    
    Args:
        sql (str): SQL更新语句
        params (tuple, optional): 更新参数. Defaults to None.
        
    Returns:
        int: 影响的行数
    """
    return db_manager.execute_update(sql, params)

def test_database_connection():
    """
    测试数据库连接的便捷函数
    
    Returns:
        bool: 连接是否成功
    """
    return db_manager.test_connection()

# ==================== 模块初始化 ====================

if __name__ == "__main__":
    # 模块测试代码
    print("测试数据库连接...")
    
    if test_database_connection():
        print("✓ 数据库连接成功")
        
        # 获取数据库信息
        db_info = db_manager.get_database_info()
        print(f"数据库版本: {db_info['version']}")
        print(f"当前数据库: {db_info['database']}")
        print(f"数据表数量: {len(db_info['tables'])}")
        
        if db_info['tables']:
            print("数据表列表:")
            for table in db_info['tables']:
                print(f"  - {table}")
    else:
        print("✗ 数据库连接失败")
        print("请检查数据库配置和服务状态")