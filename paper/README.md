# Bản thảo hiện hành: phương pháp giám sát sự kiện tổng quát

Tên: **A Network-Aware Predictive Digital Twin Framework for Event-Based
Production Monitoring**. Bài đề xuất cách tách bộ dự báo, điều kiện dữ liệu
hợp lệ và lõi so sự kiện. Dây chuyền MuJoCo chỉ là một nghiên cứu tình huống.
Chưa chứng minh khả năng chuyển mô hình đã hiệu chuẩn giữa các loại máy.

- `title_abstract.tex`: title/abstract riêng,221 từ; tác giả/đơn vị còn trống.
- `body.tex`: lý thuyết tổng quát, giả thiết áp dụng, bệ thử, kết quả và giới hạn.
- `prepare.py`: tạo ba bảng từ receipt; kiểm tra trích dẫn, hash và mục vật lý.
- `evidence/`: dữ liệu dẫn xuất và hồ sơ nguồn; tác giả chưa xác minh/duyệt.
- `../reports/dt_cppps_manuscript_virtual.pdf`: PDF hiện hành theo template LNCS.

```bash
python paper/export_pdf.py
```

Cần Tectonic hoặc pdfLaTeX. Gói mẫu giữ llncs.cls; không tự thay font/lề để ép
số trang. Giới hạn trang và quy định AI/tác giả phải rà theo hội nghị cụ thể.

Bản rộng trước khi thu hẹp ở Git commit7bbde4a. Các thí nghiệm điều khiển toàn
chu trình và tối ưu toàn mô hình được giữ trong lịch sử/evidence, không dùng
làm bằng chứng cho câu hỏi hẹp hiện tại. Ba bảng giám sát/ETA/đồng hồ được sinh
và đưa vào bài. Kết quả ML kém về thời gian báo và ngoài miền vẫn được công bố.

Các phần vật lý để trống; không tự thêm số. Chưa có kết quả second-device,
nguồn PLC/mạng thật, độ chính xác chẩn đoán máy thật hoặc tự phục hồi. Đổi tên
sự kiện trong kiểm tra phần mềm không phải thử nghiệm trên máy thứ hai.

Hai nguồn mới Shao2023/Lu2024 đã xem tóm tắt tác giả và metadata NIST; chưa
xác minh toàn văn. Những thông tin đó được ghi ở literature_scope_20261106.json.
Bản thảo chưa sẵn sàng nộp, không có bảo đảm được hội nghị chấp nhận.

Bộ mới E014 khóa kế hoạch ở5a39fe5 trước chạy:36 bản ghi/720 phát lại; ngưỡng cũ không đạt mục tiêu0 báo nhầm. Báo cả6 ca thiếu xung và2/6 ca báo nhầm, không chỉ nêu lợi ích dùng thời gian nguồn.
