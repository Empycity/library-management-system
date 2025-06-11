#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本

本脚本用于初始化图书馆管理系统数据库，包括：
1. 读取并执行SQL创建脚本
2. 插入示例数据
3. 验证数据库结构
4. 生成初始化报告

使用方法:
    python init_database.py

注意事项:
    - 确保MySQL服务已启动
    - 确保数据库连接配置正确
    - 首次运行会创建数据库和表结构
    - 重复运行会重置数据库（谨慎使用）

作者: 图书馆管理系统开发团队
版本: 1.0
创建日期: 2024-01-15
"""

import os
import sys
import pymysql
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== 配置参数 ====================

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # 请根据实际情况修改密码
    'charset': 'utf8mb4',
    'autocommit': False  # 手动控制事务
}

# 目标数据库名称
TARGET_DATABASE = 'library_management'

# SQL文件路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CREATE_SQL_FILE = os.path.join(CURRENT_DIR, 'create_database.sql')
SAMPLE_DATA_FILE = os.path.join(CURRENT_DIR, 'insert_sample_data.sql')

# ==================== 工具函数 ====================

def read_sql_file(file_path):
    """
    读取SQL文件内容
    
    Args:
        file_path (str): SQL文件路径
        
    Returns:
        str: SQL文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"错误：找不到SQL文件 {file_path}")
        return None
    except Exception as e:
        print(f"错误：读取SQL文件失败 {e}")
        return None

def execute_sql_script(connection, sql_content, script_name="SQL脚本"):
    """
    执行SQL脚本
    
    Args:
        connection: 数据库连接对象
        sql_content (str): SQL脚本内容
        script_name (str): 脚本名称（用于日志）
        
    Returns:
        bool: 执行是否成功
    """
    try:
        # 分割SQL语句（以分号分隔）
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        with connection.cursor() as cursor:
            for i, statement in enumerate(statements, 1):
                # 跳过注释和空语句
                if statement.startswith('--') or not statement:
                    continue
                    
                try:
                    cursor.execute(statement)
                    print(f"  ✓ 执行语句 {i}/{len(statements)}")
                except Exception as e:
                    # 某些语句可能因为已存在而失败，这是正常的
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"  ⚠ 语句 {i} 跳过（对象已存在）")
                    else:
                        print(f"  ✗ 语句 {i} 执行失败: {e}")
                        print(f"    SQL: {statement[:100]}...")
                        return False
            
            # 提交事务
            connection.commit()
            print(f"✓ {script_name} 执行完成")
            return True
            
    except Exception as e:
        print(f"✗ {script_name} 执行失败: {e}")
        connection.rollback()
        return False

def verify_database_structure(connection):
    """
    验证数据库结构是否正确创建
    
    Args:
        connection: 数据库连接对象
        
    Returns:
        dict: 验证结果
    """
    verification_result = {
        'success': True,
        'tables': {},
        'views': {},
        'procedures': {},
        'events': {}
    }
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查表
            expected_tables = [
                'categories', 'books', 'readers', 'borrows', 
                'admins', 'system_logs', 'reservations'
            ]
            
            cursor.execute("SHOW TABLES")
            existing_tables = [row[f'Tables_in_{TARGET_DATABASE}'] for row in cursor.fetchall()]
            
            for table in expected_tables:
                if table in existing_tables:
                    # 获取表结构信息
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    verification_result['tables'][table] = {'exists': True, 'count': count}
                else:
                    verification_result['tables'][table] = {'exists': False, 'count': 0}
                    verification_result['success'] = False
            
            # 检查视图
            expected_views = [
                'book_statistics', 'borrow_statistics', 'borrow_trend_statistics'
            ]
            
            cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
            existing_views = [row[f'Tables_in_{TARGET_DATABASE}'] for row in cursor.fetchall()]
            
            for view in expected_views:
                verification_result['views'][view] = view in existing_views
            
            # 检查存储过程
            cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (TARGET_DATABASE,))
            existing_procedures = [row['Name'] for row in cursor.fetchall()]
            
            expected_procedures = ['UpdateOverdueBooks', 'CleanExpiredReservations']
            for procedure in expected_procedures:
                verification_result['procedures'][procedure] = procedure in existing_procedures
            
            # 检查事件
            cursor.execute("SHOW EVENTS")
            existing_events = [row['Name'] for row in cursor.fetchall()]
            
            expected_events = ['daily_overdue_check', 'daily_reservation_cleanup']
            for event in expected_events:
                verification_result['events'][event] = event in existing_events
                
    except Exception as e:
        print(f"验证数据库结构时出错: {e}")
        verification_result['success'] = False
    
    return verification_result

def print_verification_report(verification_result):
    """
    打印验证报告
    
    Args:
        verification_result (dict): 验证结果
    """
    print("\n" + "="*50)
    print("数据库结构验证报告")
    print("="*50)
    
    # 表验证结果
    print("\n📋 数据表:")
    for table, info in verification_result['tables'].items():
        status = "✓" if info['exists'] else "✗"
        count_info = f"({info['count']} 条记录)" if info['exists'] else ""
        print(f"  {status} {table} {count_info}")
    
    # 视图验证结果
    print("\n👁 视图:")
    for view, exists in verification_result['views'].items():
        status = "✓" if exists else "✗"
        print(f"  {status} {view}")
    
    # 存储过程验证结果
    print("\n⚙ 存储过程:")
    for procedure, exists in verification_result['procedures'].items():
        status = "✓" if exists else "✗"
        print(f"  {status} {procedure}")
    
    # 事件验证结果
    print("\n⏰ 定时事件:")
    for event, exists in verification_result['events'].items():
        status = "✓" if exists else "✗"
        print(f"  {status} {event}")
    
    # 总体结果
    overall_status = "成功" if verification_result['success'] else "失败"
    print(f"\n🎯 总体状态: {overall_status}")
    print("="*50)

def main():
    """
    主函数：执行数据库初始化流程
    """
    print("图书馆管理系统 - 数据库初始化工具")
    print("="*50)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标数据库: {TARGET_DATABASE}")
    print("="*50)
    
    # 第一步：连接到MySQL服务器（不指定数据库）
    print("\n🔌 连接到MySQL服务器...")
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ MySQL连接成功")
    except Exception as e:
        print(f"✗ MySQL连接失败: {e}")
        print("请检查MySQL服务是否启动，以及连接配置是否正确")
        return False
    
    try:
        # 第二步：读取并执行数据库创建脚本
        print("\n📖 读取数据库创建脚本...")
        create_sql = read_sql_file(CREATE_SQL_FILE)
        if not create_sql:
            return False
        
        print("\n🏗 执行数据库创建脚本...")
        if not execute_sql_script(connection, create_sql, "数据库创建脚本"):
            return False
        
        # 第三步：切换到目标数据库
        print(f"\n🎯 切换到数据库 {TARGET_DATABASE}...")
        with connection.cursor() as cursor:
            cursor.execute(f"USE {TARGET_DATABASE}")
        print("✓ 数据库切换成功")
        
        # 第四步：插入示例数据（如果文件存在）
        if os.path.exists(SAMPLE_DATA_FILE):
            print("\n📝 读取示例数据脚本...")
            sample_sql = read_sql_file(SAMPLE_DATA_FILE)
            if sample_sql:
                print("\n💾 插入示例数据...")
                execute_sql_script(connection, sample_sql, "示例数据脚本")
        else:
            print("\n⚠ 未找到示例数据文件，跳过示例数据插入")
        
        # 第五步：验证数据库结构
        print("\n🔍 验证数据库结构...")
        verification_result = verify_database_structure(connection)
        print_verification_report(verification_result)
        
        # 第六步：显示完成信息
        print("\n🎉 数据库初始化完成！")
        print("\n📋 系统信息:")
        print(f"  • 数据库名称: {TARGET_DATABASE}")
        print(f"  • 默认管理员: admin")
        print(f"  • 默认密码: admin123")
        print(f"  • 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return verification_result['success']
        
    except Exception as e:
        print(f"\n✗ 初始化过程中发生错误: {e}")
        return False
        
    finally:
        # 关闭数据库连接
        if connection:
            connection.close()
            print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 数据库初始化成功完成！")
            sys.exit(0)
        else:
            print("\n❌ 数据库初始化失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 程序异常退出: {e}")
        sys.exit(1)