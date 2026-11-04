# Hoàn thiện phần mềm trước, đo máy sau

## Phạm vi bản phần mềm này

Hoàn thiện đường đi dữ liệu và bộ kiểm tra mà không cần máy thật. Các mục gồm:
cổng dữ liệu mẫu liên tục; chặn gói sai và theo dõi im lặng; thử truyền trên cùng
máy; trang tổng quan mới; kiểm tra tổng hợp; hồ sơ và mã băm nguồn.

Các mô đun chu trình, dự báo 1D, MuJoCo nền, đặt lại, đối chiếu và lưới nghiên cứu
được giữ và đưa vào bộ kiểm tra chung. Không tự thay tham số vật lý để làm thử đạt.

## Cổng dữ liệu mới làm gì?

Nhận gói JSON qua UDP ở địa chỉ 127.0.0.1 — chỉ trong máy đang chạy chương trình.
Đây là chỗ để một trình đọc thiết bị sau này gửi dữ liệu đã lấy được vào lõi DT.
Hiện bộ thử đóng vai nguồn dữ liệu đó. Chưa có trình đọc giao thức S7 của Siemens;
không gọi cổng UDP này là đã kết nối CPU 1214C.

Gói chứa session_id, generation, sequence, source_time, values và quality.
source_time được quy đổi theo bảng mapping.json. Thời điểm nhận do cổng tự ghi;
gói không được tự khai received_time_s. Gói lớn hơn 16 KiB, sai JSON hoặc dữ liệu
không hợp lệ bị ghi lỗi. Bộ chặn phiên/thứ tự và bộ kiểm tra im lặng vẫn dùng lõi chung.

Không có gói mới không được hiểu là cảm biến báo false. Khi dữ liệu im lặng quá
ngưỡng trong hồ sơ, lõi dừng chờ; dữ liệu trở lại không tự cho chạy. Các lệnh chỉ
ghi commands_dry_run.jsonl — tệp để xem thử, không gửi ra thiết bị.

Ví dụ một gói mẫu (source_time là mili giây theo bảng ví dụ; các trạng thái chỉ
là dữ liệu thử, không phải số đọc máy):

```json
{
  "session_id": "demo",
  "generation": 0,
  "sequence": 1,
  "source_time": 20,
  "values": {"PS2_upstream": false},
  "quality": {"PS2_upstream": "good"}
}
```

Gói minh họa này thiếu các cảm biến khác nên không đủ để cho chu trình chạy.
Chạy stream-check để dùng bộ dữ liệu thử đầy đủ cho trạng thái cấp phôi.
Cổng xử lý tối đa một gói trong mỗi nhịp; gửi dồn quá nhanh có thể làm dữ liệu
đợi trong bộ đệm UDP và trở nên cũ. Không coi đây là dịch vụ sản xuất đã định chuẩn tải.

Bảng recording_map_unverified.json giữ thông số chưa xác nhận ở trạng thái chưa
biết. recording_map_example.json chỉ dùng dữ liệu mẫu. Không lấy việc gói thử
chạy được để đánh dấu bảng vật lý đã xác nhận hoặc đồng hồ PLC đã đồng bộ.

## Cách kiểm tra dễ nhất

Trong môi trường Python của dự án:

```text
python mujoco/check_stream.py --output output/thu_cong_du_lieu_moi
python mujoco/check_software.py --output output/kiem_tra_phan_mem_moi
```

Lệnh đầu tự mở cổng nội bộ và gửi các gói thử: im lặng rồi trở lại; gói lặp/sai
phiên/sai JSON; bảng chưa xác nhận. Không cần tự mở hai cửa sổ hoặc nối PLC.
Lệnh thứ hai kiểm kê đủ sáu mục rồi chạy các nhóm kiểm tra; có thể mất vài phút.
Thư mục xuất phải chưa tồn tại. Xem report.md, software_check.json và từng tệp log.

Docker:

```powershell
./scripts/docker_dt.ps1 -Mode stream-check
./scripts/docker_dt.ps1 -Mode software-check
```

Docker vẫn không có kết nối mạng ra ngoài; loopback chỉ hoạt động trong container.
Không mở cổng để máy bên ngoài gửi dữ liệu vào trong hạng mục này.

## Xem trên trang tổng quan

Chạy python web/server.py rồi mở http://127.0.0.1:8765/tong_quan.html.
Bảng mới hiển thị báo cáo cổng dữ liệu, đối chiếu mô hình và kiểm tra tổng hợp.
Cũng có thể chọn các tệp JSON đã lưu để xem mà không tải lên dịch vụ ngoài.

## Những gì vẫn phải làm khi có máy thật

Chốt và kiểm tra địa chỉ I/O; viết/ghép trình đọc S7 phù hợp với dự án TIA thực;
đo quy đổi đồng hồ và độ trễ; xác định ma sát/quãng dừng/tốc độ/phản hồi; đối chiếu
hình học và thử nghiệm máy. Các công việc này được để riêng, chưa đánh dấu hoàn thành.
Phần mềm mô phỏng chưa thay thế phản hồi, cơ cấu an toàn hoặc chương trình PLC thật.
MuJoCo nền vẫn chỉ quan sát. Chưa tự chọn ngưỡng mới từ lưới nghiên cứu.

## Kết quả bản Docker cuối

Đạt cả tám nhóm trong software-check: 126 kiểm tra lõi, 8 kiểm tra web; ba trường
hợp UDP thực trên cùng máy; tích hợp; đặt lại; dự báo nền; lưới 144 đầu vào và
24 lượt đối chứng. Hai kiểm tra đóng gói cũng đạt. Đây là phạm vi thử phần mềm,
không có số đo máy thật hoặc lệnh gửi thiết bị.

Lần WSL đầu có một lỗi dữ liệu thử dùng cùng thời điểm nhiều lần. Thư mục lần đó
vẫn được giữ và hiển thị chưa đạt; sửa dữ liệu thử rồi chạy lại toàn bộ trong Docker.
Mã ảnh và bằng chứng: [hồ sơ candidate](../docker/evidence/candidate-20261103-software-v2.json).
Người dùng đã chấp thuận bản v2 ngày 03/11/2026 bằng lời xác nhận
“ok tất cả mọi thứ đều ổ, hãy cập nhật vào docker”. Trạng thái chấp thuận được
lưu riêng tại [hồ sơ phát hành Docker](../docker/RELEASES.md); hồ sơ candidate gốc
giữ nguyên để truy lại trạng thái lúc dựng. Phạm vi là phần mềm v2, không phải
hiệu chuẩn, kết nối hoặc kiểm chứng máy thật.

## Bổ sung ngày 04/11/2026

Hai mục mới: phát lại phiên dữ liệu (giữ cả nhịp im lặng) và gói ZIP hồ sơ
có kiểm tra mã băm. Xem [hướng dẫn](phat_lai_va_dong_goi_phien.md).
Bản mới dùng nhãn `candidate-20261104-stream-evidence`; bản nghiệm thu mặc định giữ nguyên.
