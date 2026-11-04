# Phát lại và mang hồ sơ phiên chạy sang máy khác

## Hai hạng mục mới — 04/11/2026

1. **Phát lại phiên dữ liệu:** dùng lại từng gói và từng thời điểm lõi đã xử lý,
   kể cả nhịp không có gói. So trạng thái, lý do dừng, kết quả chặn gói và lệnh
   ghi thử với lần cũ. Nhờ vậy có thể xem lỗi có lặp khi dùng đúng đầu vào không.
2. **Gói hồ sơ phiên:** ZIP gồm cấu hình, bảng tín hiệu, thông tin phiên, dữ liệu
   nhận thô, các lệnh ghi thử và báo cáo cuối. Mỗi tệp có mã SHA-256 để phát hiện
   thay đổi khi sao chép. Chỉ đóng đúng sáu tệp của phiên, không lấy cả thư mục.

Mã nằm trong `mujoco/stream_archive.py`; bộ thử là `check_stream_archive.py`.
Không đổi tham số cơ khí, quyền điều khiển hoặc cơ chế dừng chờ của lõi.

## Bước 1 — Tạo hồ sơ mẫu

Trong môi trường Python dự án đã cài, tại thư mục gốc:

```text
python mujoco/check_stream_archive.py --output output/thu_phat_lai_01
```

Thư mục xuất phải mới. Lệnh tự thử ba phiên: mất dữ liệu rồi có lại;
gói sai/lặp; bảng tín hiệu chưa xác nhận. Mỗi phiên được phát lại, đóng ZIP và
kiểm tra ZIP. Đọc `report.md` và `stream_archive_check.json` ở thư mục xuất.

## Bước 2 — Phát lại một phiên để truy tìm lỗi

```text
python mujoco/stream_archive.py replay --input output/thu_phat_lai_01/stream/gap_then_return --output output/phat_lai_01
```

Trong `replay.json`, `passed: true` nghĩa là các kết quả logic được so đều giống;
`mismatch_tick_indices` liệt kê nhịp khác nhau, bắt đầu từ 0. Đối chiếu
`replayed_commands.jsonl` với `commands_dry_run.jsonl` của phiên gốc.
Thời gian tính toán `core_step_ms` được đo mới và không đưa vào phép so bằng nhau.
Thời điểm nhận đã lưu được dùng lại; chương trình không giả chạy thời gian thực.

Mã nguồn phải trùng mã băm trong phiên. Phiên mới ghi toàn bộ tệp Python
trong thư mục MuJoCo; phiên cũ chỉ ghi bốn tệp thì chỉ kiểm tra được bốn tệp đó.
Giữ cùng phiên bản Python/thư viện hoặc dùng đúng ảnh Docker để hạn chế khác biệt.
Giới hạn tính toán theo thời gian thực vẫn có thể khiến kết quả khác. Khi khác,
chương trình báo không đạt và giữ bản phát lại; không sửa kết quả cũ cho khớp.
Phiên bật dự báo nền bất đồng bộ hiện bị từ chối phát lại; cấu hình không bị
tự tắt chức năng. Phiên bị ngắt lỗi hoặc thiếu lệnh cuối cũng bị từ chối.

## Bước 3 — Đóng gói và kiểm tra trên máy nhận

```text
python mujoco/stream_archive.py bundle --input output/thu_phat_lai_01/stream/gap_then_return --output output/phien_01.zip
python mujoco/stream_archive.py verify --input output/phien_01.zip
```

Không ghi đè ZIP đã có. Bộ kiểm tra chặn tệp thiếu/thừa, tên đường dẫn lạ/trùng,
vượt giới hạn kích thước hoặc khác mã băm; không tự giải nén.
Sau khi kiểm tra, giải nén bằng công cụ hệ điều hành vào thư mục mới rồi chạy
`replay --input <thư_mục_đã_giải_nén> --output <thư_mục_kết_quả_mới>`.
Máy nhận cần mã nguồn và môi trường tương ứng. ZIP phiên không chứa Python,
MuJoCo, CAD hoặc toàn bộ dự án.

Mã băm phát hiện khác biệt so với bảng đi kèm, **không chứng minh người gửi là ai**:
người sửa cả dữ liệu và bảng mã băm vẫn có thể tạo gói nhất quán. Chức năng này
chỉ lưu cục bộ, không tự tải hồ sơ lên dịch vụ ngoài.

## Kiểm nghiệm bản Docker mới

```powershell
./scripts/docker_dt.ps1 -Mode build
./scripts/docker_dt.ps1 -Mode stream-archive-check -Tag candidate-20261104-stream-evidence
./scripts/docker_dt.ps1 -Mode software-check -Tag candidate-20261104-stream-evidence
```

Kết quả ở `output/docker/stream-archive-check_<mã_lần_chạy>` hoặc
`software-check_<mã_lần_chạy>`. Bộ kiểm tra tổng hợp thêm nhóm thứ chín
`stream_archive`. Bản mới là candidate; demo mặc định vẫn dùng bản đã được
chấp thuận `accepted-20261103-software-v2`. Chưa đổi nhãn nghiệm thu.

## Phạm vi kết luận

Giống kết quả phát lại không phải độ chính xác phát hiện lỗi vật lý. Ba phiên
mẫu chưa đi qua pha theo dõi chuyển động có dự báo; chưa chứng minh phát lại
mọi quỹ đạo hoặc tải máy. Đây là nền tảng điều tra lỗi dữ liệu.
Chưa có trình đọc S7, kết nối PLC, hiệu chuẩn cảm biến hoặc lệnh ghi ra máy thật.
CAD V5 và mô hình MuJoCo chưa được coi là đồng bộ đầy đủ.

## Kết quả kiểm tra đã thực hiện

Docker đạt đủ chín nhóm, gồm 132 kiểm tra lõi và 8 web. Ba phiên phát lại tổng
102 nhịp, không khác kết quả logic; ba ZIP được xác nhận đúng mã băm. Các trường
hợp âm (dữ liệu cố tình sai) được sáu phép thử mới kiểm tra. Hai kiểm tra đóng gói
nguồn và cú pháp PowerShell/JavaScript cũng đạt. Bằng chứng tại
[docker/evidence/candidate-20261104-stream-evidence.json](../docker/evidence/candidate-20261104-stream-evidence.json).
