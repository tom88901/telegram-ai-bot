# Multi-AI Telegram Bot 🤖

Bot Telegram sử dụng nhiều API như OpenRouter và DeepInfra để cung cấp trả lời thông minh, có khả năng:
- Xoay tua API key
- Cảnh báo khi hết key
- Lệnh quản trị viên riêng biệt
- Theo dõi trạng thái key

## Triển khai

### 1. Tạo biến môi trường:
- `TELEGRAM_TOKEN`: Token của bot Telegram
- `OPENROUTER_API_KEYS`: Danh sách key OpenRouter, cách nhau bởi dấu phẩy
- `DEEPINFRA_API_KEYS`: Danh sách key DeepInfra
- `ADMIN_IDS`: ID của quản trị viên (phân cách bằng dấu phẩy)

### 2. Railway
- Kết nối GitHub repo chứa code
- Railway sẽ tự chạy `Procfile`

### 3. Chạy thủ công:
```bash
chmod +x start.sh
./start.sh
```

## Lệnh hỗ trợ:
- `/start`, `/help`, `/reset`, `/see`
- Lệnh quản trị: `/error`, `/delete`, `/addkey`, `/dashboard`
## Nguồn key
https://openrouter.ai/
https://deepinfra.com/
---

**Version**: v2.3
