# Hướng dẫn Tích hợp Chiến lược TradingView & Webhook API

Tài liệu hướng dẫn kết nối chiến lược **Pine Script (TradingView)** với **Backend FastAPI Trading Engine** qua HTTPS Webhook.

---

## 1. Nguyên tắc Kiến trúc Tích hợp

```
TradingView (Pine Script Strategy Alert)
               ↓ (HTTPS Webhook POST)
FastAPI Backend (/api/webhooks/tradingview)
               ↓ (Xác thực Secret + Kiểm tra Idempotency Duplicate + Ghi DB WebhookEvent)
Fast Acknowledgment HTTP 200 Response (< 20ms)
               ↓ (Đẩy vào Background Worker nội bộ)
Trading Engine Pipeline (Session -> Risk Engine -> Position Limits -> MT5 Execution)
```

* **TradingView**: Chịu trách nhiệm tạo tín hiệu chiến lược (Strategy Signal Generator).
* **Backend**: Nắm toàn quyền kiểm duyệt (Final Authority), thẩm định rủi ro và thực thi lệnh vào MetaTrader 5.
* **Tách rời hoàn toàn**: Chiến lược có thể tùy biến, thêm bớt chỉ báo (RSI, Bollinger Bands, EMA, FVG) mà không ảnh hưởng đến execution engine.

---

## 2. Chuẩn Payload JSON (Canonical Alert Payload)

Khi một thanh nến đóng thoả mãn điều kiện chiến lược, TradingView sẽ gửi payload JSON theo định dạng chuẩn:

```json
{
  "event_id": "1728468000000_gold_m15_v1_BUY",
  "symbol": "XAUUSD",
  "action": "BUY",
  "timeframe": "M15",
  "entry": 2650.50,
  "stop_loss": 2642.50,
  "take_profit": 2666.50,
  "strategy": "gold_m15_v1",
  "risk_percent": 1.0,
  "timestamp": "1728468000",
  "secret": "{{WEBHOOK_SECRET_TOKEN}}"
}
```

### Bảng định nghĩa các trường:

| Trường | Kiểu | Bắt buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `event_id` | String | Có | Mã định danh duy nhất của sự kiện nến (kết hợp timestamp + strategy + action) |
| `symbol` | String | Có | Cặp tài sản giao dịch (mặc định: `XAUUSD`) |
| `action` | String | Có | Hành động: `BUY` hoặc `SELL` |
| `timeframe` | String | Có | Khung thời gian: `M15`, `H1`, `M5`... |
| `entry` / `price` | Float | Có | Giá vào lệnh dự kiến tại thời điểm nến đóng |
| `stop_loss` / `sl` | Float | Có | Mức giá cắt lỗ bắt buộc (tính bằng ATR multiplier) |
| `take_profit` / `tp` | Float | Không | Mức giá chốt lời mục tiêu (tính theo tỷ lệ R:R) |
| `strategy` | String | Không | Tên phiên bản chiến lược (ví dụ: `gold_m15_v1`) |
| `risk_percent` | Float | Không | % rủi ro trên vốn cho lệnh này (mặc định: `1.0%`) |
| `timestamp` | String | Không | Unix timestamp thời điểm phát tín hiệu |
| `secret` | String | Có | Khóa bí mật webhook để xác thực request |

---

## 3. Cài đặt Pine Script trên TradingView

File mã nguồn chiến lược: [`pine/gold_strategy.pine`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/pine/gold_strategy.pine)

### Các bước cài đặt:
1. Mở **TradingView** trên trình duyệt hoặc Desktop App.
2. Mở biểu đồ vàng **XAUUSD** (khung thời gian khuyên dùng: **15 Phút - M15**).
3. Mở tab **Pine Editor** ở phía dưới biểu đồ.
4. Bấm **Open** -> **New blank strategy** (hoặc xóa sạch code mặc định).
5. Sao chép toàn bộ nội dung từ file [`pine/gold_strategy.pine`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/pine/gold_strategy.pine) và dán vào.
6. Bấm nút **Save** và đặt tên `XAUUSD Modular Gold Strategy Engine`.
7. Bấm nút **Add to chart** (Thêm vào biểu đồ).

### Tùy chỉnh tham số chiến lược (Settings):
* **Dual EMA Filter**: Bật/tắt lọc xu hướng theo cặp đường EMA 9 / EMA 21.
* **RSI Momentum Filter**: Bật/tắt lọc xung lượng RSI (chu kỳ 14, ngưỡng Long >= 50, Short <= 50).
* **Bollinger Bands Filter**: Lọc biến động giá dựa trên dải giữa BB.
* **Fair Value Gap (FVG)**: Lọc mô hình khoảng trống giá nến 3 thanh.
* **ATR Multiplier (SL)**: Hệ số khoảng cách cắt lỗ (mặc định: 1.5 x ATR).
* **Risk/Reward Ratio (TP)**: Tỷ lệ chốt lời (mặc định: 2.0R).

---

## 4. Thiết lập Webhook Alert trên TradingView

1. Trên biểu đồ TradingView, nhấp chuột phải vào nến hoặc nhấp biểu tượng đồng hồ báo thức ⏰ ở thanh công cụ bên phải -> Chọn **Create Alert**.
2. **Condition**: Chọn chiến lược vừa thêm: `XAUUSD Modular Gold Strategy Engine`.
3. **Trigger**: Chọn `Order fills and alert() function calls`.
4. Mở tab **Notifications**:
   * Tích chọn ô **Webhook URL**.
   * Nhập địa chỉ URL của bot (Nếu chạy local thì dùng link Cloudflare Tunnel hoặc ngrok; nếu VPS thì dùng domain HTTPS):
     ```
     https://your-domain-or-tunnel.com/api/webhooks/tradingview
     ```
5. Mở tab **Settings**:
   * **Alert name**: `XAUUSD M15 Strategy Alert`
   * **Message**: Nhập `{{strategy.order.alert_message}}`
6. Bấm **Create** để kích hoạt cảnh báo tự động.

---

## 5. Thử nghiệm Webhook (Testing & Simulation)

Bạn có thể mô phỏng tín hiệu TradingView gửi vào backend mà không cần chờ nến đóng bằng script có sẵn:

```powershell
python "backend/scripts/test_webhook.py"
```

Hoặc qua `curl`:
```bash
curl -X POST "http://127.0.0.1:8000/api/webhooks/tradingview" \
     -H "Content-Type: application/json" \
     -H "X-Webhook-Secret: YOUR_SECRET_HERE" \
     -d '{
       "event_id": "test_alert_001",
       "symbol": "XAUUSD",
       "action": "BUY",
       "timeframe": "M15",
       "entry": 2650.00,
       "stop_loss": 2645.00,
       "take_profit": 2660.00,
       "strategy": "gold_m15_v1",
       "timestamp": "1728468000",
       "secret": "YOUR_SECRET_HERE"
     }'
```

---

## 6. Xử lý Sự cố thường gặp (Troubleshooting)

| Vấn đề | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| **Lỗi 401 Unauthorized** | Sai secret token hoặc thiếu header `X-Webhook-Secret` / trường `secret` | Kiểm tra giá trị `WEBHOOK_SECRET` trong `.env` và khớp với secret khai báo trong Pine Script/Alert. |
| **Lỗi status: ignored (duplicate_signal)** | TradingView gửi retry hoặc bắn 2 alert giống hệt trong 30s | Đây là cơ chế Idempotency bảo vệ tài khoản khỏi vào trùng lệnh. Lệnh đầu đã được ghi nhận. |
| **Lỗi status: rejected (outside_allowed_sessions)** | Tín hiệu kích hoạt ngoài phiên London/New York hoặc vào cuối tuần | Xem cấu hình `ALLOW_TRADING_SESSIONS` trong `.env`. Bot chặn để tránh spread cao. |
| **Lỗi status: rejected (spread_exceeded)** | Độ giãn spread của broker tại thời điểm đó vượt `MAX_SPREAD_POINTS` | Chờ thị trường ổn định thanh khoản hoặc điều chỉnh lại trần spread trong cấu hình. |
| **Webhook timeout từ TradingView** | Backend xử lý tính toán quá lâu trong luồng HTTP | Endpoint đã dùng **BackgroundTasks** để trả lời phản hồi `< 20ms` trước khi dispatch lệnh ngầm. |
