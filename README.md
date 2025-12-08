# Car Repair Center Management System

Hệ thống quản lý trung tâm sửa chữa ô tô được xây dựng bằng Flask và MySQL.

## Yêu cầu hệ thống

- Python 3.10+
- MySQL 8.0+

## Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd car-repair
```

### 2. Tạo môi trường ảo (khuyến nghị)

```bash
python -m venv env
```

Kích hoạt môi trường ảo:

**Windows:**
```bash
env\Scripts\activate
```

**Linux/macOS:**
```bash
source env/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình database

Tạo file `.env` trong thư mục gốc với nội dung:

```env
SECRET_KEY=your_secret_key_here
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=car_repair_db
```

### 5. Khởi tạo database

Chạy file SQL để tạo database và các bảng:

```bash
mysql -u root -p < database/schema.sql
```

Hoặc sử dụng MySQL Workbench để import file `database/schema.sql`.

### 6. Cập nhật schema (nếu cần)

```bash
python update_schema.py
```

## Chạy ứng dụng

### Development mode

```bash
flask --app app run --debug
```

Hoặc:

```bash
python -m flask --app app run --debug
```

Ứng dụng sẽ chạy tại: http://127.0.0.1:5000

### Production mode

```bash
flask --app app run --host=0.0.0.0 --port=5000
```

## Tài khoản mặc định

| Username   | Password | Role       |
|------------|----------|------------|
| admin      | 123      | Admin      |
| reception  | 123      | Reception  |
| tech       | 123      | Technician |
| cashier    | 123      | Cashier    |

## Cấu trúc thư mục

```
car-repair/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── update_schema.py    # Database migration script
├── database/
│   └── schema.sql      # Database schema
├── static/
│   └── images/         # Static images
└── templates/          # Jinja2 HTML templates
    ├── admin/
    ├── cashier/
    ├── reception/
    └── technician/
```

## Tính năng chính

- **Reception**: Tiếp nhận xe, tạo phiếu tiếp nhận
- **Technician**: Quản lý sửa chữa, thêm vật tư/phụ tùng
- **Cashier**: Tạo hóa đơn, xử lý thanh toán
- **Admin**: Dashboard thống kê, quản lý hệ thống
