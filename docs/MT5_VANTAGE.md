# MetaTrader 5 (Vantage Markets) Integration & Broker Abstraction Guide

Tài liệu hướng dẫn kết nối hệ thống giao dịch tự động với sàn **Vantage Markets** thông qua **MetaTrader 5 Python Win32 SDK**.

---

## 1. Kiến trúc Trừu tượng Broker (Broker Abstraction Architecture)

Kiến trúc đảm bảo **Trading Engine** và **Risk Engine** hoàn toàn độc lập với chi tiết kỹ thuật của Vantage hoặc MT5:

```
Trading Engine & Risk Engine
              ↓
    IBrokerAdapter (Interface trừu tượng)
              ↓
    MT5BrokerAdapter (Thực thi cụ thể cho MetaTrader 5)
              ↓
  MetaTrader 5 Desktop Terminal (64-bit)
              ↓
   Vantage Markets Server (Demo / Live)
```

> [!IMPORTANT]
> * **Môi trường mặc định**: Luôn là **DEMO/PAPER TRADING** (`TRADING_ENV=DEMO`). Tuyệt đối không bao giờ mặc định chạy tài khoản thật (LIVE).
> * **Đường dẫn linh hoạt**: Không bao giờ hard-code đường dẫn cài đặt MT5. Hệ thống sử dụng biến môi trường `MT5_PATH` trong `.env`.

---

## 2. Quy trình Cài đặt & Cấu hình MT5 với Sàn Vantage

### 2.1. Cài đặt MetaTrader 5 Terminal
1. Tải bộ cài MT5 từ sàn Vantage: `https://www.vantagemarkets.com/trading-platform/metatrader-5/`
2. Tiến hành cài đặt (Mặc định tại `C:\Program Files\Vantage - MetaTrader 5\terminal64.exe`).

### 2.2. Đăng nhập Tài khoản Vantage Demo
1. Mở phần mềm **MetaTrader 5**.
2. Chọn menu: `File` -> `Login to Trade Account`.
3. Nhập thông tin tài khoản:
   * **Login**: Số tài khoản MT5 (ví dụ: `12345678`).
   * **Password**: Mật khẩu giao dịch.
   * **Server**: Chọn đúng server demo (ví dụ: `VantageInternational-Demo` hoặc `VantageFX-Demo`).
4. Kiểm tra góc dưới cùng bên phải của MT5: Cột sóng mạng chuyển sang màu xanh/đỏ (có dung lượng data nhận về) báo hiệu đăng nhập thành công.

### 2.3. Cấu hình Cho phép Giao dịch Tự động (Algo Trading)
1. Trong cửa sổ MT5, vào menu: `Tools` -> `Options` (hoặc phím tắt `Ctrl + O`).
2. Chọn tab **Expert Advisors**:
   * Tích chọn ô: **`Allow Algo Trading`** (Cho phép giao dịch tự động).
   * Tích chọn ô: **`Allow WebRequest for listed URL`** (nếu cần).
3. Đảm bảo nút **Algo Trading** trên thanh công cụ chính (Toolbar) đang ở trạng thái xanh bật (▶️).

---

## 3. Cấu hình Môi trường trong file `.env`

Cập nhật thông số kết nối trong file [`.env`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/.env):

```ini
# Runtime & Safety Environment
APP_ENV=local
DEBUG=true
TRADING_ENV=DEMO                       # BẮT BUỘC: DEMO hoặc LIVE (Mặc định DEMO)

# MetaTrader 5 Vantage Configuration
MT5_PATH=C:\Program Files\Vantage - MetaTrader 5\terminal64.exe
MT5_LOGIN=12345678                     # Số tài khoản Vantage của bạn
MT5_PASSWORD=YourPasswordHere          # Mật khẩu tài khoản Vantage
MT5_SERVER=VantageInternational-Demo   # Tên Server của sàn Vantage
MT5_TIMEOUT_MS=10000                   # Timeout kết nối (10 giây)

# Symbol Mapping
DEFAULT_SYMBOL=XAUUSD
BROKER_SYMBOL_MAP={"XAUUSD": "XAUUSD"} # Hỗ trợ mapping nếu sàn dùng XAUUSD.pro, GOLD...
```

---

## 4. Cơ chế Tự động Đối soát Dữ liệu Khởi động (Post-Startup Reconciliation)

Hệ thống được trang bị cơ chế **Reconciliation Engine** tự động chạy mỗi khi Backend khởi động lại hoặc sau sự cố sập nguồn/crash server:

```
FastAPI Server Khởi động
           ↓
Kết nối MetaTrader 5 Terminal
           ↓
Lấy danh sách các vị thế thực tế đang mở trên MT5
           ↓
Truy vấn bảng positions trong cơ sở dữ liệu MySQL
           ↓
So khớp và phát hiện sai lệch (Discrepancy Detection):
  * Trường hợp A: DB ghi nhận vị thế OPEN nhưng trên sàn MT5 đã đóng 
    (do cắn Stop Loss / Take Profit trong lúc bot tắt server) -> Tự động cập nhật DB sang CLOSED.
  * Trường hợp B: Trên sàn MT5 có lệnh mở nhưng DB chưa có (do can thiệp thủ công) 
    -> Ghi log cảnh báo vào bảng bot_events để người dùng quan sát.
           ↓
Chụp ảnh tài khoản (Account Snapshot) và sẵn sàng nhận lệnh mới.
```

---

## 5. Hướng dẫn Kiểm tra Kết nối Trực tiếp (Local Testing)

Chạy script kiểm tra đường truyền giữa Python và MT5 terminal:

```powershell
python "backend/scripts/check_mt5_link.py"
```

Kết quả trả về sẽ hiển thị đầy đủ:
* Phiên bản MetaTrader5 SDK
* Trạng thái kết nối (`connected: True`)
* Tên server Vantage và số dư tài khoản (`Balance`, `Equity`, `Free Margin`)
* Giá Bid/Ask và Spread hiện tại của cặp vàng `XAUUSD`.

---

## 6. Hướng dẫn Triển khai trên Windows VPS (24/7 Production)

1. Cài đặt **MetaTrader 5** lên Windows VPS (Amazon EC2, Hetzner, Vultr Windows Server).
2. Đăng nhập tài khoản Vantage, tích chọn **Save password**.
3. Cấu hình biến môi trường trên VPS trong `.env`:
   * `MT5_PATH=C:\Program Files\Vantage - MetaTrader 5\terminal64.exe`
   * `TRADING_ENV=DEMO` (chạy thử nghiệm ít nhất 1 tuần trước khi cân nhắc chuyển sang `LIVE`).
4. Thiết lập chạy nền tự khởi động lại qua **NSSM** (Non-Sucking Service Manager):
   ```cmd
   nssm install GoldTradingBot "d:\BOT Giao dịch\scripts\run_backend.bat"
   nssm set GoldTradingBot AppDirectory "d:\BOT Giao dịch"
   nssm start GoldTradingBot
   ```
