# Bản tích hợp phần mềm số 1

Bản này ghép các mô đun cho **một phôi mỗi chu trình**. Viết đủ sáu mục trước,
sau đó mới chạy kiểm tra chung. Đã viết không có nghĩa đã hiệu chuẩn hoặc đã
được người dùng nghiệm thu. Nhật ký chi tiết: `docs/nhat_ky_cong_viec.md`.

## Sáu mục làm gì?

1. **M01 — Chặn nhầm lượt:** mỗi tín hiệu và lệnh mang mã phiên, lần khởi tạo,
   số thứ tự. Dữ liệu lượt cũ không được đưa vào điều khiển lượt mới.
2. **M02 — Chuẩn hóa đầu vào:** bảng tên cảm biến, chiều tác động và quy đổi
   thời gian đặt trong JSON. Chưa xác nhận thì giữ trạng thái chưa biết.
3. **M03 — Một lõi dùng chung:** chạy mô phỏng và đọc lại tệp đều đi qua cùng
   trình tự điều khiển, ước lượng, đánh giá lỗi, dự báo và chặn lệnh.
4. **M04 — Dự báo cơ học riêng:** MuJoCo tính tiếp chuyển động băng/phôi từ
   trạng thái ước lượng. Nhánh này không đọc vị trí thật để chọn lệnh. Chưa mô
   hình hóa lực hút, khí nén hoặc toàn bộ robot. Nhánh tính đơn giản cũ vẫn
   là mặc định; nhánh MuJoCo cần đánh giá thời gian tính trước khi sử dụng.
5. **M05 — Trang tổng quan:** xem kết quả đã lưu và nhật ký bằng tiếng Việt;
   không gửi lệnh tới máy. HOLD nghĩa là **dừng chờ**, không tự chạy lại.
6. **M06 — Ghép và bàn giao:** danh mục tệp, dấu kiểm tra nguồn, bộ kiểm tra
   tích hợp, gói ZIP và ảnh Docker thử nghiệm (candidate: chờ nghiệm thu).

## Mở trên máy hiện tại

Tại thư mục dự án, chạy `python web/server.py`, rồi mở
`http://127.0.0.1:8765/tong_quan.html`. Nếu không chạy máy chủ, mở trang HTML
và dùng nút chọn tệp để đọc kết quả/nhật ký trên máy. Không tải tệp ra ngoài.

Máy có Python và MuJoCo theo `docker/requirements.lock` có thể chạy:

```text
python mujoco/assemble.py --output output/assembly_01 --validate
```

Thư mục kết quả phải chưa tồn tại. Lệnh kiểm tra đủ sáu mục đã viết, rồi chạy
kiểm tra logic và tích hợp. `validation.json` cho biết đạt/chưa đạt;
`integration/report.md` giải thích kết quả. Không tìm tham số tối ưu trong lệnh này.

Với Docker đã cài, dùng PowerShell:

```text
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode build
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode tests
powershell -ExecutionPolicy Bypass -File scripts/docker_dt.ps1 -Mode integration-check
```

Kết quả Docker lưu ở `output/docker`. Docker này chạy lõi không có cửa sổ;
trang web chạy riêng bên ngoài. Chưa tự công nhận ảnh thử nghiệm là bản ổn định.

## Đổi thông số và đọc dữ liệu đã ghi

Sao chép một hồ sơ trong `mujoco/configs` trước khi sửa. Độ dài dùng mét,
thời gian dùng giây, tốc độ dùng mét/giây. Thông số số đo, ma sát, thời gian,
ngưỡng và chất lượng đồng hồ là các nhóm khác nhau; không gọi tất cả là đã đo.
`recording_map_unverified.json` chưa có địa chỉ PLC đã xác nhận.
`recording_map_example.json` chỉ dành cho dữ liệu giả lập.

```text
python mujoco/replay_input.py --input du_lieu.jsonl --mapping mujoco/configs/recording_map_unverified.json --config mujoco/configs/reconfigurable_cell_20261030.json --output output/doc_lai_01
```

Mỗi dòng JSON cần `session_id`, `generation`, `sequence`, `source_time`,
`received_time_s`, `values` và `quality`. Giá trị cảm biến là true/false/null;
chất lượng là good/stale/unavailable (tốt/cũ/chưa có nguồn). Xem tệp giả lập
do kiểm tra tích hợp tạo để biết cấu trúc. Đồng hồ nguồn phải đổi về cùng
thang thời gian trước khi so tuổi dữ liệu. Chỉ khai báo verified sau khi kiểm
chứng độc lập. Lệnh kết quả chỉ ghi ra tệp, **không điều khiển PLC thật**.

## Sau khi kiểm tra chung

Sửa lỗi chương trình trước. Sau đó mới lập từng thử nghiệm: mất cảm biến,
trễ mạng, thay tốc độ, sai tham số. Mỗi lần thay một nhóm và lưu hồ sơ/kết quả
riêng để so sánh. Kiểm tra nhánh dự báo MuJoCo có tính kịp hạn hay không;
quá hạn phải chuyển sang dừng chờ. Không báo phần trăm cải thiện khi chưa đo.

Phần còn lại cần giai đoạn riêng: đo máy thật, đồng bộ CAD V5 với cảnh MuJoCo,
phản hồi vị trí trục/chân không, hiệu chuẩn khí nén và ma sát, nhiều phôi cùng
lúc, xử lý phôi đang dang dở sau lỗi. Hiện tại đặt lại chỉ chuẩn bị **chu trình
mới**, không khẳng định tiếp tục an toàn phôi cũ.
