# Đối chiếu hai mô hình dự báo

## Dùng để hiểu điều gì?

Nhánh 1D tính nhanh bằng công thức dừng. MuJoCo tính tiếp xúc băng/phôi và thêm
điều kiện ngang, cao. Hai nhánh có thể đưa ra khuyến nghị khác nhau. Bộ đối chiếu
đọc nhật ký nền đã lưu và tính lại 1D từ đúng ước lượng, thời điểm nguồn và thời
điểm ra yêu cầu của MuJoCo. Không lấy vị trí phôi thật làm đầu vào.

Đây là phân tích sau lượt chạy; không phát lệnh, sửa hồ sơ hoặc làm máy chạy tiếp.
Đồng hồ hạn tính của 1D được tắt khi đọc lại để xem kết quả đầy đủ của mô hình.
Vì vậy đây không phải bản sao quyết định thực tế của nhánh nhanh khi chạy.

## Cách dùng

Trong môi trường Python của dự án:

```text
python mujoco/audit_background.py --source output/thu_nghiem/observer --output output/doi_chieu_moi
```

Thư mục nguồn cần effective_config.json, manifest.json và background.jsonl từ
cùng một lượt có bật dự báo nền. Thư mục xuất phải chưa tồn tại; không ghi đè kết quả.
Chạy background-check sẽ tự tạo observer_audit và incomplete_worker_audit trong
thư mục kết quả. Có thể chạy bộ đọc ngoại tuyến trên máy không cài MuJoCo vì chỉ
đọc kết quả tiếp xúc đã lưu, không chạy lại cơ học.

## Đọc báo cáo

- report.md: bảng số cặp có cùng/khác khuyến nghị, tách riêng kết quả được nhận
  để quan sát và kết quả bị loại tại thời điểm nhận.
- pairs.jsonl: từng bản ghi, mã yêu cầu, mã băm đầu vào và hai khuyến nghị.
- audit.json: tổng số bản ghi sai, kết quả thiếu, mã băm tệp và nguồn chương trình.

Kết quả thiếu thời gian tính không được tính thành một dự báo dừng hoàn chỉnh.
Bản ghi sai phiên, hồ sơ, số thứ tự, số kịch bản hoặc không hữu hạn được loại và
ghi lý do. Kết quả quá cũ có thể được so để tìm hiểu, nhưng vẫn không được dùng
điều khiển. Mã băm hỗ trợ truy nguồn; không phải chứng thực chống sửa tệp có chủ ý.

Hai biên tổng hợp có ràng buộc khác nhau nên không lấy hiệu để gọi là sai số vật lý.
Cùng khuyến nghị không có nghĩa cả hai đúng; khác nhau chưa xác định bên nào đúng.
Không chuyển tỷ lệ đồng ý thành độ chính xác chẩn đoán lỗi, hay tỷ lệ an toàn máy thật.
Các yêu cầu từ cùng một chu trình có tương quan; không coi là các lượt sản xuất độc lập.

## Kết quả bản thử Docker ngày 03/11/2026

- 116 kiểm tra lõi, 2 kiểm tra đóng gói, bộ tích hợp và bộ ba chu trình nền đạt.
- Lượt nền có 24 kết quả đủ để so: 22 đã được nhận để quan sát, 2 bị loại tại
  thời điểm nhận. Hai mô hình cùng khuyến nghị ở cả 24 đầu vào trong lượt này.
- Lượt ép tính thiếu có 82 kết quả thiếu; không kết quả nào được tính thành cặp đồng ý.
- Ba chu trình đều đặt phôi, dấu vết thời gian mô phỏng/pha/lệnh/ước lượng giống nhau.
  Tiến trình bị dừng trong phép thử riêng không chặn bước gọi lõi, các tiến trình đã đóng.
- **Giới hạn thời gian vẫn còn:** lượt ép tính thiếu có 1/697 bước lõi vượt 20 ms,
  lớn nhất 32,749 ms. Không bỏ mẫu này hoặc đổi hạn để ghi đạt. Nhánh nền bình thường
  có p95 3,984 ms và lớn nhất 14,690 ms; đó là số đo một lượt, không phải bảo đảm.
- Thời gian chỉ đo bước lõi, chưa gồm cơ học, ghi tệp, khởi tạo hay kết thúc tiến trình.
  Số kết quả nền có thể đổi theo tải máy; không dùng nó làm tốc độ sản xuất.

Mã ảnh và mã băm: [hồ sơ candidate](../docker/evidence/candidate-20261103-model-audit.json).
Ảnh mới chờ người dùng nghiệm thu. Các ảnh cũ và mọi kết quả đã lưu được giữ nguyên.
