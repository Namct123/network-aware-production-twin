# Kết quả dự báo MuJoCo chạy nền — 03/11/2026

## Hệ thống mới làm gì?

Nhánh tính nhanh vẫn ra lệnh cho chu trình. Một tiến trình riêng dùng MuJoCo để dự báo từ bản sao ước lượng. Nó gửi kết quả về để ghi và đối chiếu; hiện chưa được đổi lệnh máy.
Khi đang tính một yêu cầu, hệ thống bỏ qua yêu cầu mới. Cách này tránh hàng đợi dài dần và tránh buộc nhánh nhanh đợi MuJoCo.

## Thử được những gì?

Ảnh Docker mới đạt 110 kiểm tra logic, bộ tích hợp, 15 trường hợp bản tin đặt lại kèm 2 lượt MuJoCo, và 24 lượt hồi quy với 0 lỗi tiêu chí. Hai kiểm tra đóng gói tại máy chủ cũng đạt.
Ba chu trình đối chứng đều đặt phôi và có cùng dấu vết thời gian mô phỏng, pha, lệnh, ước lượng. Một chu trình tắt nền, một bật nền và một ép nền không tính đủ. Mỗi chu trình là một lần thử, không phải hàng trăm lần sản xuất độc lập.

| Chu trình Docker | Số bước lõi | Trung vị (ms) | p95 (ms) | Lớn nhất (ms) | Bước >20 ms |
|---|---:|---:|---:|---:|---:|
| Tắt nền | 697 | 0.320 | 2.591 | 4.917 | 0 |
| Bật nền | 697 | 0.475 | 3.505 | 12.629 | 0 |
| Nền tính thiếu | 697 | 0.455 | 3.013 | 4.565 | 0 |

Lần bật nền gửi 35 yêu cầu, nhận 34 kết quả để quan sát, loại 1. Lần ép tính thiếu loại 81 kết quả do tính chưa đủ. Tất cả tiến trình đã đóng. Một phép thử riêng dừng cưỡng bức tiến trình nền vẫn gọi được bước lõi.

p95 là mức mà ít nhất 95% số mẫu quan sát không vượt quá. Bảng chỉ đo RuntimeCore.step, gồm xử lý kết quả nền, không gồm bước cơ học, ghi tệp, nhịp chờ, khởi tạo hoặc kết thúc. Không phải cam kết hạn thời gian thực hay độ trễ PLC thật.

## Vì sao chưa tự áp kết quả nền?

Kết quả có thể tính từ vị trí cũ và chỉ xét chạy thêm một khoảng thời gian ngắn rồi dừng. Khi nó quay lại, vật có thể đã đi xa hơn. Vì vậy một kết quả cũ nói có thể chạy tiếp chưa đủ để cấp lệnh chạy tiếp ở hiện tại. Kiểm tra định danh, tuổi, thứ tự mẫu và thay đổi lệnh giúp lọc quan sát; chưa thay thế chứng minh này.

## Mở để tự kiểm nghiệm

Từ thư mục dự án, chạy trong PowerShell:

```powershell
./scripts/docker_dt.ps1 -Mode background-check
```

Xem thư mục kết quả được in sau dòng Results:; mở report.md, background_check.json và ba thư mục con. Chi tiết tham số ở [hướng dẫn](du_bao_nen_quan_sat.md). Muốn dùng cảnh có cửa sổ, chạy run_twin.py với hồ sơ background_observer_20261103.json và --pace-wall-time; mô-đun nền không tự bật trong demo mặc định.

## Trạng thái bàn giao

Ảnh candidate-20261103-background-observer, chờ người dùng kiểm nghiệm. Mã ảnh: `sha256:6b492b8a086469154e4853bc50161672db58eb8633a8645c8bbf24b629e0e914`.
Ảnh đã nghiệm thu và mọi candidate trước giữ nguyên. Không đưa ảnh lên kho công khai. CAD V5 và hình học MuJoCo vẫn chưa đồng bộ đầy đủ; các tham số vật lý chưa đo không được đánh dấu hiệu chuẩn.
Bằng chứng và mã băm nguồn: [hồ sơ Docker](../docker/evidence/candidate-20261103-background-observer.json). Không có số liệu máy thật trong báo cáo này.
