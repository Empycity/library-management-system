-- ==========================================
-- 图书馆管理系统数据库创建脚本
-- ==========================================
-- 功能说明：
-- 1. 创建图书馆管理系统数据库
-- 2. 创建所有必需的数据表
-- 3. 设置表结构、索引和约束
-- 4. 创建统计视图和存储过程
-- 
-- 作者: 图书馆管理系统开发团队
-- 版本: 1.0
-- 创建日期: 2024-01-15
-- ==========================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS library_management 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE library_management;

-- ==========================================
-- 1. 图书分类表 (categories)
-- ==========================================
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
    name VARCHAR(100) NOT NULL COMMENT '分类名称',
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '分类编码',
    description TEXT COMMENT '分类描述',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书分类表';

-- ==========================================
-- 2. 图书表 (books)
-- ==========================================
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '图书ID',
    isbn VARCHAR(20) NOT NULL UNIQUE COMMENT 'ISBN号码',
    title VARCHAR(200) NOT NULL COMMENT '图书标题',
    author VARCHAR(100) NOT NULL COMMENT '作者',
    publisher VARCHAR(100) NOT NULL COMMENT '出版社',
    category_id INT NOT NULL COMMENT '分类ID',
    publish_date DATE COMMENT '出版日期',
    price DECIMAL(10,2) DEFAULT 0.00 COMMENT '价格',
    location VARCHAR(50) COMMENT '存放位置',
    description TEXT COMMENT '图书描述',
    status ENUM('available', 'borrowed', 'damaged', 'lost') DEFAULT 'available' COMMENT '图书状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    
    -- 索引
    INDEX idx_isbn (isbn),
    INDEX idx_title (title),
    INDEX idx_author (author),
    INDEX idx_category (category_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书表';

-- ==========================================
-- 3. 读者表 (readers)
-- ==========================================
CREATE TABLE IF NOT EXISTS readers (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '读者ID',
    card_number VARCHAR(20) NOT NULL UNIQUE COMMENT '读者卡号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    gender ENUM('男', '女', '其他') NOT NULL COMMENT '性别',
    birth_date DATE COMMENT '出生日期',
    phone VARCHAR(20) NOT NULL COMMENT '电话号码',
    email VARCHAR(100) COMMENT '邮箱地址',
    address TEXT COMMENT '地址',
    register_date DATE NOT NULL COMMENT '注册日期',
    max_borrow_count INT DEFAULT 5 COMMENT '最大借阅数量',
    status ENUM('active', 'suspended', 'expired') DEFAULT 'active' COMMENT '读者状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_card_number (card_number),
    INDEX idx_name (name),
    INDEX idx_phone (phone),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='读者表';

-- ==========================================
-- 4. 借阅记录表 (borrows)
-- ==========================================
CREATE TABLE IF NOT EXISTS borrows (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '借阅记录ID',
    reader_id INT NOT NULL COMMENT '读者ID',
    book_id INT NOT NULL COMMENT '图书ID',
    borrow_date DATE NOT NULL COMMENT '借阅日期',
    due_date DATE NOT NULL COMMENT '应还日期',
    return_date DATE COMMENT '实际归还日期',
    renew_count INT DEFAULT 0 COMMENT '续借次数',
    fine_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '罚款金额',
    status ENUM('borrowed', 'returned', 'overdue', 'lost', 'damaged', 'reserved', 'fined') DEFAULT 'borrowed' COMMENT '借阅状态',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    
    -- 索引
    INDEX idx_reader_id (reader_id),
    INDEX idx_book_id (book_id),
    INDEX idx_borrow_date (borrow_date),
    INDEX idx_due_date (due_date),
    INDEX idx_status (status),
    INDEX idx_reader_status (reader_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='借阅记录表';

-- ==========================================
-- 5. 管理员表 (admins)
-- ==========================================
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '管理员ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(MD5加密)',
    real_name VARCHAR(50) NOT NULL COMMENT '真实姓名',
    email VARCHAR(100) COMMENT '邮箱地址',
    phone VARCHAR(20) COMMENT '电话号码',
    role ENUM('super_admin', 'admin', 'librarian') DEFAULT 'librarian' COMMENT '角色',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    last_login_time TIMESTAMP NULL COMMENT '最后登录时间',
    last_login_ip VARCHAR(45) COMMENT '最后登录IP',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_username (username),
    INDEX idx_status (status),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

-- ==========================================
-- 6. 系统日志表 (system_logs)
-- ==========================================
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_type ENUM('admin', 'reader', 'system') NOT NULL COMMENT '用户类型',
    user_id INT COMMENT '用户ID',
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    target_type VARCHAR(50) COMMENT '操作对象类型',
    target_id INT COMMENT '操作对象ID',
    description TEXT COMMENT '操作描述',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_user_type_id (user_type, user_id),
    INDEX idx_action (action),
    INDEX idx_target (target_type, target_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统日志表';

-- ==========================================
-- 7. 预约表 (reservations)
-- ==========================================
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '预约ID',
    reader_id INT NOT NULL COMMENT '读者ID',
    book_id INT NOT NULL COMMENT '图书ID',
    reservation_date DATE NOT NULL COMMENT '预约日期',
    expiry_date DATE NOT NULL COMMENT '预约到期日期',
    status ENUM('active', 'fulfilled', 'cancelled', 'expired') DEFAULT 'active' COMMENT '预约状态',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    
    -- 索引
    INDEX idx_reader_id (reader_id),
    INDEX idx_book_id (book_id),
    INDEX idx_status (status),
    INDEX idx_reservation_date (reservation_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书预约表';

-- ==========================================
-- 创建统计视图
-- ==========================================

-- 图书统计视图
CREATE OR REPLACE VIEW book_statistics AS
SELECT 
    b.id,
    b.title,
    b.author,
    b.isbn,
    c.name as category_name,
    COUNT(br.id) as total_borrows,
    COUNT(CASE WHEN br.status = 'borrowed' THEN 1 END) as current_borrows,
    COUNT(CASE WHEN br.status = 'returned' THEN 1 END) as returned_count,
    COUNT(CASE WHEN br.status = 'overdue' THEN 1 END) as overdue_count,
    b.status as book_status
FROM books b
LEFT JOIN categories c ON b.category_id = c.id
LEFT JOIN borrows br ON b.id = br.book_id
GROUP BY b.id, b.title, b.author, b.isbn, c.name, b.status;

-- 读者借阅统计视图
CREATE OR REPLACE VIEW borrow_statistics AS
SELECT 
    r.id,
    r.name,
    r.card_number,
    COUNT(br.id) as total_borrows,
    COUNT(CASE WHEN br.status = 'borrowed' THEN 1 END) as current_borrows,
    COUNT(CASE WHEN br.status = 'returned' THEN 1 END) as returned_count,
    COUNT(CASE WHEN br.status = 'overdue' THEN 1 END) as overdue_count,
    r.status as reader_status
FROM readers r
LEFT JOIN borrows br ON r.id = br.reader_id
GROUP BY r.id, r.name, r.card_number, r.status;

-- 借阅趋势统计视图
CREATE OR REPLACE VIEW borrow_trend_statistics AS
SELECT 
    DATE_FORMAT(borrow_date, '%Y-%m') as month,
    COUNT(*) as borrow_count,
    COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned_count,
    COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_count
FROM borrows
WHERE borrow_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
GROUP BY DATE_FORMAT(borrow_date, '%Y-%m')
ORDER BY month DESC;

-- ==========================================
-- 创建存储过程
-- ==========================================

-- 自动处理逾期图书的存储过程
DELIMITER //
CREATE PROCEDURE UpdateOverdueBooks()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE borrow_id INT;
    DECLARE overdue_cursor CURSOR FOR 
        SELECT id FROM borrows 
        WHERE status = 'borrowed' AND due_date < CURDATE();
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN overdue_cursor;
    
    read_loop: LOOP
        FETCH overdue_cursor INTO borrow_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- 更新借阅状态为逾期
        UPDATE borrows SET status = 'overdue' WHERE id = borrow_id;
        
        -- 记录系统日志
        INSERT INTO system_logs (user_type, action, target_type, target_id, description)
        VALUES ('system', '自动更新', 'borrow', borrow_id, '系统自动将借阅记录标记为逾期');
    END LOOP;
    
    CLOSE overdue_cursor;
END //
DELIMITER ;

-- 清理过期预约的存储过程
DELIMITER //
CREATE PROCEDURE CleanExpiredReservations()
BEGIN
    UPDATE reservations 
    SET status = 'expired' 
    WHERE status = 'active' AND expiry_date < CURDATE();
    
    -- 记录系统日志
    INSERT INTO system_logs (user_type, action, description)
    VALUES ('system', '清理过期预约', '系统自动清理过期的图书预约记录');
END //
DELIMITER ;

-- ==========================================
-- 创建触发器
-- ==========================================

-- 借阅记录插入时自动更新图书状态
DELIMITER //
CREATE TRIGGER after_borrow_insert
AFTER INSERT ON borrows
FOR EACH ROW
BEGIN
    IF NEW.status = 'borrowed' THEN
        UPDATE books SET status = 'borrowed' WHERE id = NEW.book_id;
    END IF;
END //
DELIMITER ;

-- 借阅记录更新时自动更新图书状态
DELIMITER //
CREATE TRIGGER after_borrow_update
AFTER UPDATE ON borrows
FOR EACH ROW
BEGIN
    IF NEW.status = 'returned' AND OLD.status != 'returned' THEN
        UPDATE books SET status = 'available' WHERE id = NEW.book_id;
    ELSEIF NEW.status = 'lost' THEN
        UPDATE books SET status = 'lost' WHERE id = NEW.book_id;
    ELSEIF NEW.status = 'damaged' THEN
        UPDATE books SET status = 'damaged' WHERE id = NEW.book_id;
    END IF;
END //
DELIMITER ;

-- ==========================================
-- 创建事件调度器（定时任务）
-- ==========================================

-- 启用事件调度器
SET GLOBAL event_scheduler = ON;

-- 每日自动处理逾期图书
CREATE EVENT IF NOT EXISTS daily_overdue_check
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
  CALL UpdateOverdueBooks();

-- 每日自动清理过期预约
CREATE EVENT IF NOT EXISTS daily_reservation_cleanup
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
  CALL CleanExpiredReservations();

-- ==========================================
-- 插入默认数据
-- ==========================================

-- 插入默认管理员账户（密码：admin123，MD5加密）
INSERT IGNORE INTO admins (username, password, real_name, role) 
VALUES ('admin', '0192023a7bbd73250516f069df18b500', '系统管理员', 'super_admin');

-- 插入默认图书分类
INSERT IGNORE INTO categories (name, code, description, sort_order) VALUES
('计算机科学', 'CS', '计算机科学与技术相关图书', 1),
('文学', 'LIT', '文学作品和文学理论', 2),
('历史', 'HIST', '历史类图书', 3),
('科学', 'SCI', '自然科学类图书', 4),
('艺术', 'ART', '艺术类图书', 5),
('哲学', 'PHIL', '哲学类图书', 6),
('经济', 'ECON', '经济学类图书', 7),
('教育', 'EDU', '教育学类图书', 8);

-- ==========================================
-- 数据库创建完成
-- ==========================================

SELECT '图书馆管理系统数据库创建完成！' as message;
SELECT '默认管理员账户: admin / admin123' as login_info;