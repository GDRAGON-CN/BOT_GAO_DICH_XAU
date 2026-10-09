# TradingView Pine Script Configuration

## Pine Script Strategy (`gold_strategy.pine`)
Chiến lược giao dịch vàng tự động theo xu hướng kết hợp:
* **Fast EMA (9)** và **Slow EMA (21)** xác định điểm giao cắt xu hướng.
* **ATR (14)** với hệ số x1.5 xác định khoảng dừng lỗ động (Stop Loss).
* Tỷ lệ **Risk:Reward = 1:2** để chốt lời (Take Profit).

## Cấu hình Alert trên TradingView
1. Mở biểu đồ vàng **XAUUSD** (khung thời gian khuyến nghị: **M15** hoặc **M5**).
2. Vào **Pine Editor**, dán toàn bộ mã từ [`gold_strategy.pine`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/pine/gold_strategy.pine) và nhấn **Add to Chart**.
3. Nhấp vào biểu tượng đồng hồ bấm giờ (Create Alert) hoặc phím tắt `Alt + A`.
4. Trong mục **Condition**, chọn chiến lược `XAUUSD Automated Bot Strategy`.
5. Đánh dấu tích vào ô **Webhook URL** và điền URL máy chủ của bạn:
   * **Local qua Tunnel**: `https://<your-ngrok-or-cloudflared-domain>/api/v1/webhook/tradingview`
   * **VPS Production**: `https://tradebot.yourdomain.com/api/v1/webhook/tradingview`
6. Trong mục **Message**, đảm bảo để trống hoặc điền `{{strategy.order.alert_message}}`.
7. Nhấn **Create**.
