# 图书馆管理系统

## 项目概述
这是一个基于Web的图书馆管理系统，采用前后端分离架构。

## 技术栈
- **前端**: HTML + CSS + JavaScript (原生)
- **后端**: Python + Flask
- **数据库**: MySQL

## 项目结构
```
library_management_system/
├── frontend/          # 前端模块 (负责人A)
├── backend/           # 后端模块 (负责人B) 
├── database/          # 数据库模块 (负责人C)
└── docs/             # 项目文档
```

## 三人分工

### 前端模块 (负责人A)
- 用户界面设计与实现
- 页面交互逻辑
- 与后端API对接
- 响应式布局

### 后端模块 (负责人B)
- RESTful API设计与实现
- 业务逻辑处理
- 数据验证
- 跨域处理

### 数据库模块 (负责人C)
- 数据库设计
- 表结构创建
- 数据初始化
- 数据库连接配置

## 功能模块
1. 图书管理 (增删改查)
2. 读者管理 (注册、信息管理)
3. 借阅管理 (借书、还书、续借)
4. 系统管理 (用户权限、统计报表)

## 开发环境
- Python 3.7+
- MySQL 5.7+
- 现代浏览器

## 安装依赖
```bash
pip install flask flask-cors pymysql
```

## 运行项目
1. 启动MySQL服务
2. 创建数据库并导入初始数据
3. 运行后端服务: `python backend/app.py`
4. 打开前端页面: `frontend/index.html`