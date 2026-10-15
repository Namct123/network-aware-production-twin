# Quy ước tích hợp

## Nguồn chuẩn hiện tại

- Hình học và kích thước ước lượng: `fusion/ProductionTwin_V0/ProductionTwin_V0.py`.
- Scene, vật liệu, chuyển động minh họa: `unity/Assets/ProductionTwin`.
- Tín hiệu I/O dự kiến theo sơ đồ: mục “Tín hiệu dự kiến để nối digital twin” trong `unity/README.md`. Địa chỉ này **chưa xác nhận đấu dây thực**.
- Đơn vị: CAD/CSV dùng mm; Unity dùng m (`1 unit = 1 m`). Trục CAD `(X,Y,Z)` chuyển sang Unity `(X,Z,Y)`.

## Quy trình đóng góp

1. Tạo nhánh riêng cho phần CAD, Unity, PLC hoặc digital twin.
2. Khi đổi tên một tín hiệu, trục, đơn vị hoặc giới hạn chuyển động, cập nhật tài liệu và phần nhận dữ liệu cùng lúc trong pull request.
3. Ghi cách kiểm tra thay đổi. Với Unity, mở `ProductionTwin.unity` và chạy thử một chu trình; với PLC, đính kèm bảng I/O và kết quả mô phỏng; với CAD, nêu kích thước đo thực nào đã thay thế ước lượng.
4. Không đưa mật khẩu, token, IP nội bộ, dữ liệu cá nhân, thư mục Unity `Library/` hay tệp xuất tạm vào kho.

## Điều kiện trước khi ghép với PLC thật

Xác nhận pin I/O, mức điện, hành trình, chiều trục, trạng thái dừng khẩn và liên động an toàn trên máy. `ProductionTwinDemo` hiện chỉ là hoạt ảnh; dữ liệu mạng và lệnh điều khiển thực chưa được triển khai.
