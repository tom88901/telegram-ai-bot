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

# 🤖 Multi-AI Telegram Bot v1.1

Bot AI Telegram trả lời thông minh, hỗ trợ đa nguồn API, quản lý key linh hoạt, giới hạn lượt dùng mỗi user, quản lý profile, chọn mô hình AI, log chi tiết, phân quyền admin, chuẩn hóa cho deploy Railway hoặc VPS.

---

## 🚀 **Tính năng bản v1.1**

- Chat AI tự động (xoay tua nhiều API key, chọn mô hình GPT/Gemini/Deepinfra...)
- Giới hạn lượt sử dụng mỗi user mỗi ngày, admin chỉnh sửa hạn mức dễ dàng
- Lưu hồ sơ (profile) từng user: username, số lượt dùng, mô hình đã chọn, thời gian cuối dùng, tổng số lượt gọi API
- Người dùng chọn mô hình AI qua lệnh `/model` (dùng inline button Telegram)
- Lưu hội thoại riêng từng người dùng, hỗ trợ xuất log chi tiết theo ngày
- Quản lý, thêm/xóa key API (chỉ admin), xem/sửa hồ sơ user
- Thống kê top user, top model, xuất log sử dụng user
- Cảnh báo khi hết key, tự động log lỗi API
- Phân quyền admin (ẩn thông tin, bảo mật, thao tác profile, key)
- Sẵn sàng nâng cấp lên các bản tiếp theo với module rõ ràng

---

## 🌐 **Nguồn lấy API key miễn phí**
- [OpenRouter (lấy key miễn phí)](https://openrouter.ai/)
- [DeepInfra (lấy key miễn phí)](https://deepinfra.com/)

## ☁️ **Nền tảng deploy bot Telegram**
- [Railway (deploy siêu nhanh)](https://railway.com/)
- VPS, Render, hoặc local

---

## 🛠️ **Hướng dẫn triển khai**

### 1. Chuẩn bị
- Python 3.10+
- Một tài khoản Telegram
- Token bot Telegram (lấy ở [@BotFather](https://t.me/BotFather))
- API key từ [OpenRouter](https://openrouter.ai/) hoặc [DeepInfra](https://deepinfra.com/)
- Railway, Render, VPS hoặc máy tính cá nhân

### 2. Cài đặt & cấu hình
```bash
git clone https://github.com/[tài-khoản]/[repo-của-bạn].git
cd [repo-của-bạn]
pip install python-telegram-bot requests
---

**Tác giả:** [Tom88901](https://github.com/tom88901)  
**Phiên bản:** v1.1
