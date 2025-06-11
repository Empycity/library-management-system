#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图书馆管理系统后端API服务

本文件是图书馆管理系统的核心后端服务，提供RESTful API接口
主要功能包括：
1. 图书管理（增删改查）
2. 读者管理（注册、信息管理）
3. 借阅管理（借书、还书、续借）
4. 统计报表（仪表板数据、各类统计）
5. 用户认证（登录验证）

技术栈：
- Flask: Web框架
- PyMySQL: MySQL数据库连接
- Flask-CORS: 跨域资源共享

作者: 图书馆管理系统开发团队
版本: 1.0
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import pymysql
from datetime import datetime, timedelta
import json
import os

# ==================== Flask应用初始化 ====================

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(project_root, 'frontend')

# 创建Flask应用实例，配置静态文件目录
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
# 启用跨域资源共享，允许前端页面访问后端API
CORS(app)

# ==================== 数据库配置 ====================

# MySQL数据库连接配置
# 注意：实际部署时请修改密码并使用环境变量
DB_CONFIG = {
    'host': 'localhost',        # 数据库服务器地址
    'user': 'root',            # 数据库用户名
    'password': '',            # 数据库密码（请修改为实际密码）
    'database': 'library_management',  # 数据库名称
    'charset': 'utf8mb4'       # 字符编码，支持中文和emoji
}

# ==================== 数据库操作函数 ====================

def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        pymysql.Connection: 数据库连接对象，连接失败时返回None
    """
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def execute_query(sql, params=None, fetch=True):
    """
    执行SQL查询的通用函数
    
    Args:
        sql (str): SQL语句
        params (tuple, optional): SQL参数. Defaults to None.
        fetch (bool, optional): 是否获取查询结果. Defaults to True.
    
    Returns:
        list/int/None: 
            - fetch=True时返回查询结果列表
            - fetch=False时返回影响的行数
            - 执行失败时返回None
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        # 使用字典游标，返回结果为字典格式
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            if fetch:
                # 查询操作：返回所有结果
                result = cursor.fetchall()
            else:
                # 增删改操作：提交事务并返回影响行数
                connection.commit()
                result = cursor.rowcount
        return result
    except Exception as e:
        print(f"SQL执行错误: {e}")
        return None
    finally:
        # 确保连接被正确关闭
        connection.close()

# ==================== 系统日志功能 ====================

def log_operation(user_type, user_id, action, target_type=None, target_id=None, description=None, ip_address=None):
    """
    记录系统操作日志，用于审计和追踪用户操作
    
    Args:
        user_type (str): 用户类型，如'admin'、'reader'等
        user_id (int): 用户ID
        action (str): 操作类型，如'添加'、'删除'、'修改'、'查询'等
        target_type (str, optional): 操作对象类型，如'book'、'reader'等. Defaults to None.
        target_id (int, optional): 操作对象ID. Defaults to None.
        description (str, optional): 操作描述. Defaults to None.
        ip_address (str, optional): 操作者IP地址. Defaults to None.
    
    Returns:
        None: 日志记录不返回结果
    """
    sql = """
        INSERT INTO system_logs (user_type, user_id, action, target_type, target_id, description, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (user_type, user_id, action, target_type, target_id, description, ip_address)
    # 日志记录不需要返回结果，所以fetch=False
    execute_query(sql, params, fetch=False)

# ==================== 图书管理API ====================

@app.route('/api/books', methods=['GET'])
def get_books():
    """
    获取所有图书列表
    
    HTTP方法: GET
    路径: /api/books
    
    Returns:
        JSON: 图书列表数组，按ID降序排列
        - 成功: 200状态码 + 图书数据数组
        - 失败: 500状态码 + 错误信息
    
    示例响应:
        [
            {
                "id": 1,
                "isbn": "9787111544937",
                "title": "Java核心技术",
                "author": "Cay S. Horstmann",
                "publisher": "机械工业出版社",
                "category": "计算机",
                "status": "available"
            }
        ]
    """
    sql = """
        SELECT b.*, c.name as category_name 
        FROM books b 
        LEFT JOIN categories c ON b.category_id = c.id 
        ORDER BY b.id DESC
    """
    books = execute_query(sql)
    
    if books is None:
        return jsonify({'error': '获取图书列表失败'}), 500
    
    return jsonify(books)

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """
    根据ID获取单本图书详细信息
    
    HTTP方法: GET
    路径: /api/books/<book_id>
    
    Args:
        book_id (int): 图书ID
    
    Returns:
        JSON: 单本图书的详细信息
        - 成功: 200状态码 + 图书详细数据
        - 图书不存在: 404状态码 + 错误信息
    """
    sql = "SELECT * FROM books WHERE id = %s"
    books = execute_query(sql, (book_id,))
    
    if not books:
        return jsonify({'error': '图书不存在'}), 404
    
    return jsonify(books[0])

@app.route('/api/books', methods=['POST'])
def add_book():
    """
    添加新图书到系统
    
    HTTP方法: POST
    路径: /api/books
    
    请求体 (JSON):
        {
            "isbn": "图书ISBN号",
            "title": "图书标题",
            "author": "作者",
            "publisher": "出版社",
            "category": "分类",
            "publish_date": "出版日期(可选)",
            "price": "价格(可选)",
            "location": "存放位置(可选)",
            "description": "图书描述(可选)"
        }
    
    Returns:
        JSON: 操作结果
        - 成功: 201状态码 + 成功信息
        - 参数错误: 400状态码 + 错误信息
        - 服务器错误: 500状态码 + 错误信息
    """
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['isbn', 'title', 'author', 'publisher', 'category_id']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    # 插入新图书，默认状态为可借阅
    sql = """
        INSERT INTO books (isbn, title, author, publisher, category_id, publish_date, price, location, description, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'available')
    """
    
    params = (
        data['isbn'],
        data['title'],
        data['author'],
        data['publisher'],
        data['category_id'],
        data.get('publish_date'),  # 可选字段，如果没有提供则为None
        data.get('price', 0.00),   # 价格，默认为0.00
        data.get('location'),      # 存放位置
        data.get('description')    # 图书描述
    )
    
    result = execute_query(sql, params, fetch=False)
    
    if result is None:
        return jsonify({'error': '添加图书失败'}), 500
    
    # 记录操作日志，用于审计追踪
    log_operation('admin', 1, '添加图书', 'book', None, f'添加图书: {data["title"]}', request.remote_addr)
    
    return jsonify({'message': '图书添加成功'}), 201

@app.route('/api/books/search', methods=['GET'])
def search_books():
    """
    根据关键词搜索图书
    
    HTTP方法: GET
    路径: /api/books/search?q=关键词
    
    查询参数:
        q (str): 搜索关键词，支持按标题、作者、ISBN搜索
    
    Returns:
        JSON: 匹配的图书列表
        - 成功: 200状态码 + 图书数据数组
        - 失败: 500状态码 + 错误信息
    
    搜索范围:
        - 图书标题 (模糊匹配)
        - 作者姓名 (模糊匹配)
        - ISBN号码 (模糊匹配)
    """
    keyword = request.args.get('q', '')
    
    # 使用LIKE进行模糊搜索，支持多字段搜索
    sql = """
        SELECT * FROM books 
        WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s
        ORDER BY id DESC
    """
    
    # 构造模糊搜索的通配符模式
    search_term = f'%{keyword}%'
    books = execute_query(sql, (search_term, search_term, search_term))
    
    if books is None:
        return jsonify({'error': '搜索失败'}), 500
    
    return jsonify(books)

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """
    更新图书信息
    
    HTTP方法: PUT
    路径: /api/books/<book_id>
    
    Args:
        book_id (int): 图书ID
    
    请求体 (JSON):
        {
            "title": "图书标题",
            "author": "作者",
            "publisher": "出版社",
            "category": "分类",
            "price": "价格",
            "location": "存放位置",
            "description": "图书描述"
        }
    
    Returns:
        JSON: 操作结果
    """
    data = request.get_json()
    
    # 检查图书是否存在
    check_sql = "SELECT id FROM books WHERE id = %s"
    existing = execute_query(check_sql, (book_id,))
    
    if not existing:
        return jsonify({'error': '图书不存在'}), 404
    
    # 构建更新SQL
    update_fields = []
    params = []
    
    for field in ['title', 'author', 'publisher', 'category', 'price', 'location', 'description']:
        if field in data:
            update_fields.append(f"{field} = %s")
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': '没有提供要更新的字段'}), 400
    
    params.append(book_id)
    sql = f"UPDATE books SET {', '.join(update_fields)} WHERE id = %s"
    
    result = execute_query(sql, params, fetch=False)
    
    if result is None:
        return jsonify({'error': '更新图书失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '更新图书', 'book', book_id, f'更新图书信息', request.remote_addr)
    
    return jsonify({'message': '图书更新成功'})



@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """
    删除图书
    
    HTTP方法: DELETE
    路径: /api/books/<book_id>
    
    Args:
        book_id (int): 图书ID
    
    Returns:
        JSON: 操作结果
    """
    # 检查图书是否存在
    check_sql = "SELECT id FROM books WHERE id = %s"
    existing = execute_query(check_sql, (book_id,))
    
    if not existing:
        return jsonify({'error': '图书不存在'}), 404
    
    # 检查是否有未归还的借阅记录
    borrow_check_sql = "SELECT id FROM borrows WHERE book_id = %s AND status = 'borrowed'"
    active_borrows = execute_query(borrow_check_sql, (book_id,))
    
    if active_borrows:
        return jsonify({'error': '该图书还有未归还的借阅记录，无法删除'}), 400
    
    # 删除图书
    sql = "DELETE FROM books WHERE id = %s"
    result = execute_query(sql, (book_id,), fetch=False)
    
    if result is None:
        return jsonify({'error': '删除图书失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '删除图书', 'book', book_id, f'删除图书', request.remote_addr)
    
    return jsonify({'message': '图书删除成功'})

# ==================== 读者管理API ====================

@app.route('/api/readers', methods=['GET'])
def get_readers():
    """
    获取所有读者列表
    
    HTTP方法: GET
    路径: /api/readers
    
    Returns:
        JSON: 读者列表数组，按ID降序排列
        - 成功: 200状态码 + 读者数据数组
        - 失败: 500状态码 + 错误信息
    
    示例响应:
        [
            {
                "id": 1,
                "card_number": "R20240001",
                "name": "张三",
                "gender": "男",
                "phone": "13812345678",
                "email": "zhangsan@email.com",
                "register_date": "2024-01-15"
            }
        ]
    """
    sql = "SELECT * FROM readers ORDER BY id DESC"
    readers = execute_query(sql)
    
    if readers is None:
        return jsonify({'error': '获取读者列表失败'}), 500
    
    return jsonify(readers)

@app.route('/api/readers', methods=['POST'])
def add_reader():
    """
    添加新读者到系统
    
    HTTP方法: POST
    路径: /api/readers
    
    请求体 (JSON):
        {
            "card_number": "读者卡号",
            "name": "姓名",
            "gender": "性别",
            "phone": "电话号码",
            "email": "邮箱(可选)"
        }
    
    Returns:
        JSON: 操作结果
        - 成功: 201状态码 + 成功信息
        - 参数错误: 400状态码 + 错误信息
        - 服务器错误: 500状态码 + 错误信息
    """
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['card_number', 'name', 'gender', 'phone']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    sql = """
        INSERT INTO readers (card_number, name, gender, birth_date, phone, email, address, register_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (
        data['card_number'],
        data['name'],
        data['gender'],
        data.get('birth_date', None),
        data['phone'],
        data.get('email', ''),
        data.get('address', ''),
        datetime.now().date()
    )
    
    result = execute_query(sql, params, fetch=False)
    
    if result is None:
        return jsonify({'error': '添加读者失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '添加读者', 'reader', None, f'添加读者: {data["name"]}', request.remote_addr)
    
    return jsonify({'message': '读者添加成功'}), 201

@app.route('/api/readers/<int:reader_id>', methods=['PUT'])
def update_reader(reader_id):
    """
    更新读者信息
    
    HTTP方法: PUT
    路径: /api/readers/<reader_id>
    
    Args:
        reader_id (int): 读者ID
    
    请求体 (JSON):
        {
            "name": "姓名",
            "gender": "性别",
            "phone": "电话号码",
            "email": "邮箱",
            "address": "地址",
            "max_borrow_count": "最大借阅数"
        }
    
    Returns:
        JSON: 操作结果
    """
    data = request.get_json()
    
    # 检查读者是否存在
    check_sql = "SELECT id FROM readers WHERE id = %s"
    existing = execute_query(check_sql, (reader_id,))
    
    if not existing:
        return jsonify({'error': '读者不存在'}), 404
    
    # 构建更新SQL
    update_fields = []
    params = []
    
    for field in ['name', 'gender', 'phone', 'email', 'address', 'max_borrow_count']:
        if field in data:
            update_fields.append(f"{field} = %s")
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': '没有提供要更新的字段'}), 400
    
    params.append(reader_id)
    sql = f"UPDATE readers SET {', '.join(update_fields)} WHERE id = %s"
    
    result = execute_query(sql, params, fetch=False)
    
    if result is None:
        return jsonify({'error': '更新读者失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '更新读者', 'reader', reader_id, f'更新读者信息', request.remote_addr)
    
    return jsonify({'message': '读者更新成功'})



@app.route('/api/readers/<int:reader_id>', methods=['DELETE'])
def delete_reader(reader_id):
    """
    删除读者
    
    HTTP方法: DELETE
    路径: /api/readers/<reader_id>
    
    Args:
        reader_id (int): 读者ID
    
    Returns:
        JSON: 操作结果
    """
    # 检查读者是否存在
    check_sql = "SELECT id FROM readers WHERE id = %s"
    existing = execute_query(check_sql, (reader_id,))
    
    if not existing:
        return jsonify({'error': '读者不存在'}), 404
    
    # 检查是否有未归还的借阅记录
    borrow_check_sql = "SELECT id FROM borrows WHERE reader_id = %s AND status = 'borrowed'"
    active_borrows = execute_query(borrow_check_sql, (reader_id,))
    
    if active_borrows:
        return jsonify({'error': '该读者还有未归还的借阅记录，无法删除'}), 400
    
    # 删除读者
    sql = "DELETE FROM readers WHERE id = %s"
    result = execute_query(sql, (reader_id,), fetch=False)
    
    if result is None:
        return jsonify({'error': '删除读者失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '删除读者', 'reader', reader_id, f'删除读者', request.remote_addr)
    
    return jsonify({'message': '读者删除成功'})

# ==================== 借阅管理API ====================

@app.route('/api/borrows', methods=['GET'])
def get_borrows():
    """获取所有借阅记录"""
    sql = """
        SELECT b.id, b.reader_id, b.book_id, b.borrow_date, b.due_date, 
               b.return_date, b.renew_count, b.fine_amount, b.status, b.notes,
               r.name as reader_name, bk.title as book_title, bk.status as book_status
        FROM borrows b
        JOIN readers r ON b.reader_id = r.id
        JOIN books bk ON b.book_id = bk.id
        ORDER BY b.id DESC
    """
    
    borrows = execute_query(sql)
    
    if borrows is None:
        return jsonify({'error': '获取借阅记录失败'}), 500
    
    # 动态判断逾期状态
    today = datetime.now().date()
    for borrow in borrows:
        if borrow['status'] == 'borrowed' and borrow['due_date'] < today:
            borrow['status'] = 'overdue'
    
    return jsonify(borrows)

@app.route('/api/borrows', methods=['POST'])
def create_borrow():
    """
    创建新的借阅记录
    
    HTTP方法: POST
    路径: /api/borrows
    
    请求体 (JSON):
        {
            "reader_id": int,
            "book_id": int,
            "borrow_days": int,
            "notes": str (可选)
        }
    
    借书条件:
         - 读者状态必须为active
         - 图书状态不能为lost（丢失状态不可借阅）
         - 图书状态不能为borrowed（已借出状态不可借阅）
         - 读者未达到最大借阅数量限制
         - 自动将图书状态更新为borrowed
    
    Returns:
        JSON: 操作结果和借阅记录ID
    """
    data = request.get_json()
    
    required_fields = ['reader_id', 'book_id', 'borrow_days']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必需字段: {field}'}), 400
    
    try:
        # 检查读者是否存在且状态正常
        reader_sql = "SELECT id, status, max_borrow_count FROM readers WHERE id = %s"
        reader = execute_query(reader_sql, (data['reader_id'],))
        if not reader:
            return jsonify({'error': '读者不存在'}), 400
        if reader[0]['status'] != 'active':
            return jsonify({'error': '读者状态异常，无法借阅'}), 400
        
        # 检查图书是否存在且可借阅
        book_sql = "SELECT id, status FROM books WHERE id = %s"
        book = execute_query(book_sql, (data['book_id'],))
        if not book:
            return jsonify({'error': '图书不存在'}), 400
        if book[0]['status'] == 'lost':
            return jsonify({'error': '图书已丢失，无法借阅'}), 400
        if book[0]['status'] == 'borrowed':
            return jsonify({'error': '图书已被借出，无法借阅'}), 400
        
        # 检查读者当前借阅数量
        current_borrows_sql = "SELECT COUNT(*) as count FROM borrows WHERE reader_id = %s AND status = 'borrowed'"
        current_count = execute_query(current_borrows_sql, (data['reader_id'],))
        if current_count and current_count[0]['count'] >= reader[0]['max_borrow_count']:
            return jsonify({'error': '已达到最大借阅数量限制'}), 400
        
        # 计算借阅日期和应还日期
        borrow_date = datetime.now().date()
        due_date = borrow_date + timedelta(days=int(data['borrow_days']))
        
        # 获取数据库连接并开始事务
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': '数据库连接失败'}), 500
            
        try:
            with connection.cursor() as cursor:
                # 创建借阅记录
                insert_sql = """
                    INSERT INTO borrows (reader_id, book_id, borrow_date, due_date, status, notes)
                    VALUES (%s, %s, %s, %s, 'borrowed', %s)
                """
                
                cursor.execute(
                    insert_sql, 
                    (data['reader_id'], data['book_id'], borrow_date, due_date, data.get('notes', ''))
                )
                
                # 获取新插入记录的ID
                borrow_id = cursor.lastrowid
                
                # 更新图书状态为已借出
                update_book_sql = "UPDATE books SET status = 'borrowed' WHERE id = %s"
                cursor.execute(update_book_sql, (data['book_id'],))
                
                # 提交事务
                connection.commit()
                
                # 记录操作日志
                log_operation('admin', 1, '创建借阅', 'borrow', borrow_id, f'创建借阅记录: 读者ID {data["reader_id"]}, 图书ID {data["book_id"]}', request.remote_addr)
                
                return jsonify({'message': '借阅记录创建成功', 'id': borrow_id}), 201
                
        except Exception as e:
            # 回滚事务
            connection.rollback()
            return jsonify({'error': f'创建借阅记录失败: {str(e)}'}), 500
            
        finally:
            # 关闭连接
            connection.close()
         
    except Exception as e:
        return jsonify({'error': f'创建借阅记录失败: {str(e)}'}), 500

@app.route('/api/borrows/<int:borrow_id>/return', methods=['POST'])
def return_book(borrow_id):
    """归还图书"""
    try:
        # 检查借阅记录是否存在
        check_sql = "SELECT * FROM borrows WHERE id = %s AND status = 'borrowed'"
        borrow = execute_query(check_sql, (borrow_id,))
        
        if not borrow:
            return jsonify({'error': '借阅记录不存在或已归还'}), 404
        
        # 更新借阅记录状态
        return_date = datetime.now().date()
        update_borrow_sql = """
            UPDATE borrows 
            SET status = 'returned', return_date = %s 
            WHERE id = %s
        """
        execute_query(update_borrow_sql, (return_date, borrow_id), fetch=False)
        
        # 更新图书状态为可借
        update_book_sql = "UPDATE books SET status = 'available' WHERE id = %s"
        execute_query(update_book_sql, (borrow[0]['book_id'],), fetch=False)
        
        # 记录操作日志
        log_operation('admin', 1, '归还图书', 'borrow', borrow_id, f'归还图书: 图书ID {borrow[0]["book_id"]}', request.remote_addr)
        
        return jsonify({'message': '图书归还成功'}), 200
        
    except Exception as e:
        return jsonify({'error': f'归还图书失败: {str(e)}'}), 500

@app.route('/api/borrows/<int:borrow_id>/renew', methods=['POST'])
def renew_book(borrow_id):
    """续借图书"""
    try:
        # 获取请求数据
        data = request.get_json() or {}
        extend_days = data.get('days', 30)  # 默认延长30天
        
        # 验证天数参数
        if not isinstance(extend_days, int) or extend_days < 1 or extend_days > 90:
            return jsonify({'error': '续借天数必须在1-90天之间'}), 400
        
        # 检查借阅记录是否存在
        check_sql = "SELECT * FROM borrows WHERE id = %s AND status = 'borrowed'"
        borrow = execute_query(check_sql, (borrow_id,))
        
        if not borrow:
            return jsonify({'error': '借阅记录不存在或已归还'}), 404
        
        # 检查是否已经续借过
        if borrow[0].get('renew_count', 0) >= 2:  # 最多续借2次
            return jsonify({'error': '已达到最大续借次数'}), 400
        
        # 计算新的应还日期
        current_due_date = borrow[0]['due_date']
        if isinstance(current_due_date, str):
            current_due_date = datetime.strptime(current_due_date, '%Y-%m-%d').date()
        new_due_date = current_due_date + timedelta(days=extend_days)
        
        # 更新借阅记录
        update_sql = """
            UPDATE borrows 
            SET due_date = %s, renew_count = COALESCE(renew_count, 0) + 1
            WHERE id = %s
        """
        execute_query(update_sql, (new_due_date, borrow_id), fetch=False)
        
        # 记录操作日志
        log_operation('admin', 1, '续借图书', 'borrow', borrow_id, f'续借图书: 图书ID {borrow[0]["book_id"]}, 延长{extend_days}天, 新到期日期 {new_due_date}', request.remote_addr)
        
        return jsonify({'message': '图书续借成功', 'new_due_date': new_due_date.isoformat(), 'extend_days': extend_days}), 200
        
    except Exception as e:
        return jsonify({'error': f'续借图书失败: {str(e)}'}), 500

@app.route('/api/borrows/<int:borrow_id>/fine', methods=['POST'])
def apply_fine(borrow_id):
    """设置罚款"""
    try:
        data = request.get_json()
        fine_amount = data.get('fine_amount')
        
        if not fine_amount or fine_amount <= 0:
            return jsonify({'error': '罚款金额必须大于0'}), 400
        
        # 检查借阅记录是否存在
        check_sql = "SELECT * FROM borrows WHERE id = %s"
        borrow = execute_query(check_sql, (borrow_id,))
        
        if not borrow:
            return jsonify({'error': '借阅记录不存在'}), 404
        
        # 更新借阅记录的罚款信息
        update_sql = """
            UPDATE borrows 
            SET fine_amount = %s, status = 'fined'
            WHERE id = %s
        """
        result = execute_query(update_sql, (fine_amount, borrow_id), fetch=False)
        
        if result is None:
            return jsonify({'error': '更新罚款信息失败'}), 500
        
        # 记录操作日志
        log_operation('admin', 1, '设置罚款', 'borrow', borrow_id, f'设置罚款: 金额 {fine_amount}', request.remote_addr)
        
        return jsonify({'message': '罚款设置成功', 'fine_amount': fine_amount}), 200
        
    except Exception as e:
        return jsonify({'error': f'设置罚款失败: {str(e)}'}), 500

@app.route('/api/borrows/<int:borrow_id>/status', methods=['PUT'])
def update_borrow_status(borrow_id):
    """
    更新借阅状态
    
    HTTP方法: PUT
    路径: /api/borrows/<borrow_id>/status
    
    Args:
        borrow_id (int): 借阅记录ID
    
    请求体 (JSON):
        {
            "status": "damaged|lost" (仅支持损伤和丢失状态的编辑)
        }
    
    功能说明:
         - 损伤状态：更新借阅表为damaged，图书表同步更新为damaged状态
         - 丢失状态：更新借阅表为lost，图书表同步更新为lost状态
         - 自动处理图书状态同步，只有丢失状态的图书不能借阅
    
    Returns:
        JSON: 操作结果
    """
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': '缺少status字段'}), 400
    
    status = data['status']
    valid_statuses = ['borrowed', 'returned', 'reserved', 'damaged', 'lost']
    
    if status not in valid_statuses:
        return jsonify({'error': f'无效的状态值，必须是: {", ".join(valid_statuses)}'}), 400
    
    # 检查借阅记录是否存在并获取图书ID
    check_sql = "SELECT id, book_id FROM borrows WHERE id = %s"
    existing = execute_query(check_sql, (borrow_id,))
    
    if not existing:
        return jsonify({'error': '借阅记录不存在'}), 404
    
    book_id = existing[0]['book_id']
    
    try:
        # 获取数据库连接并开始事务
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': '数据库连接失败'}), 500
            
        with connection.cursor() as cursor:
            # 更新借阅状态
            if status == 'returned':
                # 如果状态改为已归还，同时设置归还日期
                cursor.execute("UPDATE borrows SET status = %s, return_date = CURDATE() WHERE id = %s", (status, borrow_id))
            else:
                cursor.execute("UPDATE borrows SET status = %s WHERE id = %s", (status, borrow_id))
            
            # 根据借阅状态同步更新图书状态
            if status == 'lost':
                # 丢失状态：更新图书表为丢失
                cursor.execute("UPDATE books SET status = 'lost' WHERE id = %s", (book_id,))
            elif status == 'damaged':
                # 损伤状态：更新图书表为损坏
                cursor.execute("UPDATE books SET status = 'damaged' WHERE id = %s", (book_id,))
            elif status == 'returned':
                # 归还状态：图书表设为可用
                cursor.execute("UPDATE books SET status = 'available' WHERE id = %s", (book_id,))
            
            # 提交事务
            connection.commit()
            
        # 记录操作日志
        log_operation('admin', 1, '更新借阅状态', 'borrow', borrow_id, f'更新借阅状态为: {status}', request.remote_addr)
            
        return jsonify({'message': '借阅状态更新成功'})
        
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'error': f'更新借阅状态失败: {str(e)}'}), 500
    finally:
        if connection:
            connection.close()

# ==================== 统计API ====================

@app.route('/api/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """获取仪表板统计数据"""
    stats = {}
    
    # 图书总数
    total_books_sql = "SELECT COUNT(*) as count FROM books"
    result = execute_query(total_books_sql)
    stats['totalBooks'] = result[0]['count'] if result else 0
    
    # 读者总数
    total_readers_sql = "SELECT COUNT(*) as count FROM readers"
    result = execute_query(total_readers_sql)
    stats['totalReaders'] = result[0]['count'] if result else 0
    
    # 借阅中图书数
    borrowed_books_sql = "SELECT COUNT(*) as count FROM borrows WHERE status = 'borrowed'"
    result = execute_query(borrowed_books_sql)
    stats['borrowedBooks'] = result[0]['count'] if result else 0
    
    # 逾期图书数
    overdue_books_sql = "SELECT COUNT(*) as count FROM borrows WHERE status = 'borrowed' AND due_date < %s"
    result = execute_query(overdue_books_sql, (datetime.now().date(),))
    stats['overdueBooks'] = result[0]['count'] if result else 0
    
    return jsonify(stats)

@app.route('/api/stats/books', methods=['GET'])
def get_book_stats():
    """获取图书统计数据"""
    try:
        sql = "SELECT * FROM book_statistics ORDER BY total_borrows DESC"
        result = execute_query(sql)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/readers', methods=['GET'])
def get_reader_stats():
    """获取读者统计数据"""
    try:
        sql = "SELECT * FROM borrow_statistics ORDER BY total_borrows DESC"
        result = execute_query(sql)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/borrows', methods=['GET'])
def get_borrow_stats():
    """获取借阅统计数据"""
    try:
        # 使用借阅趋势统计视图
        sql = "SELECT * FROM borrow_trend_statistics LIMIT 12"
        result = execute_query(sql)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 用户认证API ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """管理员登录"""
    data = request.get_json()
    
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    # 对密码进行MD5加密
    import hashlib
    password_md5 = hashlib.md5(data['password'].encode()).hexdigest()
    
    # 查询管理员信息
    sql = "SELECT * FROM admins WHERE username = %s AND password = %s"
    admin = execute_query(sql, (data['username'], password_md5))
    
    if not admin:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    # 生成简单的token（实际项目中应使用JWT）
    import time
    token = hashlib.md5(f"{admin[0]['username']}{time.time()}".encode()).hexdigest()
    
    # 记录登录日志
    log_operation('admin', admin[0]['id'], '登录系统', None, None, f'管理员 {admin[0]["username"]} 登录系统', request.remote_addr)
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': admin[0]['id'],
            'username': admin[0]['username'],
            'role': admin[0]['role']
        }
    })





# ==================== 分类管理API ====================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """
    获取所有图书分类列表
    
    HTTP方法: GET
    路径: /api/categories
    
    Returns:
        JSON: 分类列表数组，按排序字段排列
        - 成功: 200状态码 + 分类数据数组
        - 失败: 500状态码 + 错误信息
    """
    sql = """
    SELECT c.*, 
           COALESCE(book_count.count, 0) as book_count
    FROM categories c
    LEFT JOIN (
        SELECT category_id, COUNT(*) as count 
        FROM books 
        GROUP BY category_id
    ) book_count ON c.id = book_count.category_id
    WHERE c.status = 'active' 
    ORDER BY c.sort_order, c.name
    """
    categories = execute_query(sql)
    
    if categories is None:
        return jsonify({'error': '获取分类列表失败'}), 500
    
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def add_category():
    """
    添加新的图书分类
    
    HTTP方法: POST
    路径: /api/categories
    
    请求体 (JSON):
        {
            "name": "分类名称",
            "code": "分类编码",
            "description": "分类描述(可选)",
            "sort_order": "排序(可选)"
        }
    
    Returns:
        JSON: 操作结果
    """
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'code']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    sql = """
        INSERT INTO categories (name, code, description, sort_order, status)
        VALUES (%s, %s, %s, %s, 'active')
    """
    
    params = (
        data['name'],
        data['code'],
        data.get('description'),
        data.get('sort_order', 0)
    )
    
    result = execute_query(sql, params, fetch=False)
    
    if result is None:
        return jsonify({'error': '添加分类失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '添加分类', 'category', None, f'添加分类: {data["name"]}', request.remote_addr)
    
    return jsonify({'message': '分类添加成功'}), 201

@app.route('/api/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """
    根据ID获取分类详情
    
    HTTP方法: GET
    路径: /api/categories/<category_id>
    
    Returns:
        JSON: 分类详情
    """
    sql = "SELECT * FROM categories WHERE id = %s"
    category = execute_query(sql, (category_id,))
    
    if category is None:
        return jsonify({'error': '获取分类失败'}), 500
    
    if not category:
        return jsonify({'error': '分类不存在'}), 404
    
    return jsonify(category[0])

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """
    更新分类信息
    
    HTTP方法: PUT
    路径: /api/categories/<category_id>
    
    请求体 (JSON):
        {
            "name": "分类名称",
            "code": "分类编码",
            "description": "分类描述(可选)",
            "sort_order": "排序(可选)"
        }
    
    Returns:
        JSON: 操作结果
    """
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'code']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    sql = """
        UPDATE categories 
        SET name = %s, code = %s, description = %s, sort_order = %s
        WHERE id = %s
    """
    
    params = (
        data['name'],
        data['code'],
        data.get('description'),
        data.get('sort_order', 0),
        category_id
    )
    
    result = execute_query(sql, params, fetch=False)
    
    if result is None:
        return jsonify({'error': '更新分类失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '更新分类', 'category', category_id, f'更新分类: {data["name"]}', request.remote_addr)
    
    return jsonify({'message': '分类更新成功'})

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    删除分类
    
    HTTP方法: DELETE
    路径: /api/categories/<category_id>
    
    Returns:
        JSON: 操作结果
    """
    # 检查是否有图书使用此分类
    check_sql = "SELECT COUNT(*) as count FROM books WHERE category_id = %s"
    result = execute_query(check_sql, (category_id,))
    
    if result is None:
        return jsonify({'error': '检查分类使用情况失败'}), 500
    
    if result[0]['count'] > 0:
        return jsonify({'error': '该分类下还有图书，无法删除'}), 400
    
    # 删除分类
    sql = "DELETE FROM categories WHERE id = %s"
    result = execute_query(sql, (category_id,), fetch=False)
    
    if result is None:
        return jsonify({'error': '删除分类失败'}), 500
    
    # 记录操作日志
    log_operation('admin', 1, '删除分类', 'category', category_id, f'删除分类', request.remote_addr)
    
    return jsonify({'message': '分类删除成功'})

@app.route('/api/categories/search', methods=['GET'])
def search_categories():
    """
    搜索分类
    
    HTTP方法: GET
    路径: /api/categories/search?q=关键词
    
    Returns:
        JSON: 匹配的分类列表
    """
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify([])
    
    sql = """
        SELECT * FROM categories 
        WHERE status = 'active' 
        AND (name LIKE %s OR code LIKE %s OR description LIKE %s)
        ORDER BY sort_order, name
    """
    
    search_pattern = f'%{keyword}%'
    categories = execute_query(sql, (search_pattern, search_pattern, search_pattern))
    
    if categories is None:
        return jsonify({'error': '搜索分类失败'}), 500
    
    return jsonify(categories)


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    # 如果是API请求，返回JSON错误
    if request.path.startswith('/api/'):
        return jsonify({'error': '接口不存在'}), 404
    # 否则返回前端首页（用于SPA路由）
    return send_file(os.path.join(frontend_dir, 'index.html'))

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    print("图书馆管理系统后端服务启动中...")
    print("请确保MySQL服务已启动并创建了相应的数据库和表")
    print("访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)