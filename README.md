# 🤖 Multi-AI Telegram Bot v1.0

Bot AI Telegram trả lời thông minh, hỗ trợ đa nguồn API, quản lý key linh hoạt, giới hạn lượt dùng mỗi user, phân quyền admin, chuẩn hóa cho deploy Railway hoặc VPS.

---

## 🚀 **Tính năng bản v1.0**
- Chat AI tự động (xoay tua nhiều API key)
- Giới hạn lượt sử dụng mỗi user mỗi ngày
- Lưu hội thoại riêng từng người dùng
- Quản lý, thêm/xóa key API (chỉ admin)
- Cảnh báo khi hết key
- Phân quyền admin (ẩn thông tin, bảo mật)
- Sẵn sàng nâng cấp lên các bản tiếp theo

---

## 🌐 **Nguồn lấy API key miễn phí**
- [OpenRouter (lấy key miễn phí)](https://openrouter.ai/)
- [DeepInfra (lấy key miễn phí)](https://deepinfra.com/)

## ☁️ **Nền tảng deploy bot Telegram**
- [Railway (deploy siêu nhanh)](https://railway.com/)

---

## 🛠️ **Hướng dẫn triển khai**

### 1. Chuẩn bị
- Python 3.10+
- Một tài khoản Telegram
- Token bot Telegram (lấy ở [@BotFather](https://t.me/BotFather))
- API key từ [OpenRouter](https://openrouter.ai/) hoặc [DeepInfra](https://deepinfra.com/)
- Railway (nên dùng cho nhanh) hoặc server riêng

### 2. Cài đặt & cấu hình
```bash
git clone https://github.com/[tài-khoản]/[repo-của-bạn].git
cd [repo-của-bạn]
pip install -r requirements.txt
