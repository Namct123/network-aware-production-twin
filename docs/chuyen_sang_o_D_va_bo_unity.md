# Dự án trên ổ D — chỉ mô phỏng bằng MuJoCo

## Mở dự án

Thư mục chính: `D:\Projects\network-aware-production-twin`.
Trong Codex hoặc trình sửa mã, chọn mở thư mục này cho các lần làm việc sau.

```powershell
cd D:\Projects\network-aware-production-twin
./scripts/docker_dt.ps1 -Mode demo -Tag candidate-20261104-mujoco-only
```

Bản mới là candidate để kiểm nghiệm. Bản Docker đã được chấp thuận trước đây vẫn
được giữ, không tự nâng phiên bản sau khi kiểm tra tự động đạt.

## Thư mục và chức năng

| Thư mục | Nội dung cần giữ |
|---|---|
| `mujoco/` | Lõi DT, mô hình vật lý, cấu hình sửa được và các phép kiểm tra |
| `cad_reference/`, `fusion/`, `scenes/` | CAD, nguồn dựng và bảng chi tiết hình học |
| `web/` | Giao diện giải thích, đọc kết quả và chạy thí nghiệm nội bộ |
| `paper/`, `reports/`, `docs/` | Bản thảo, báo cáo và nhật ký |
| `docker/`, `scripts/` | Đóng gói, chạy và kiểm tra phần mềm |
| `output/` | Kết quả mô phỏng và tệp bàn giao; không đưa vào Git |
| `tmp/` | Công cụ/tệp trung gian cũ; chưa xóa tùy tiện vì có thể cần tái tạo CAD/PDF |

Bảng CAD cũ cần cho MuJoCo ở `cad_reference/production_twin_v0_parts.csv`,
không còn nằm trong tài sản Unity. 113 chi tiết và mã băm của bảng giữ nguyên.
`scripts/export_cad_parts.py` tái tạo bảng bằng thư viện chuẩn, không cần Unity
hoặc thư viện vẽ ảnh. Bảng này vẫn là hình học baseline; không gọi nó là CAD V5
đã đồng bộ hoặc mô hình đã hiệu chuẩn vật lý.

## Những gì đã bỏ và những gì được bảo toàn

Đã bỏ scene, C#, vật liệu, tệp .meta và script xuất Unity khỏi nguồn hiện hành;
bỏ kiểm tra Unity trên GitHub Actions. Dự án Unity riêng `C:\Users\Admin\My project`
và Library của nó được xóa theo yêu cầu người dùng. Không cần cài Unity để chạy DT.

Các ZIP cũ chứa lẫn CAD/lõi DT và Unity được chuyển nguyên trạng ra
`D:\DT_CPPS_Archives\20261104`, có kiểm tra mã băm. Chúng không thuộc bản làm việc
hiện tại. Không sửa lịch sử Git hoặc bằng chứng Docker cũ để giả rằng chúng chưa
bao giờ dùng đường dẫn cũ. Không xóa ảnh Docker đã được nghiệm thu.

Đã dọn bộ nhớ tải xuống pip/http và npm/_cacache. Không đụng các gói đang cài,
_npx đang có thể được dùng bởi công cụ, hoặc xóa hàng loạt Temp/Downloads.

## Đường dẫn tương thích

Codex đang giữ mở thư mục cũ trên C. Vì vậy, từng thư mục con ở
`C:\Users\Admin\Documents\ChatGPT\plc` trỏ sang thư mục tương ứng trên D.
Đây là liên kết thư mục, không phải hai bản dữ liệu lớn. Một số tệp nhỏ ở gốc C
được giữ/sao chép tương thích; luôn sửa bản D. Một cache .pytest_cache bị Windows
khóa quyền vẫn ở C; không chiếm lại bộ dữ liệu dự án đã chuyển.

Sau này mở trực tiếp bản D. Không xóa đệ quy các liên kết trên C bằng công cụ
không rõ cách xử lý liên kết, vì có thể đi theo tới dữ liệu trên D.

## Hồ sơ chuyển và môi trường chạy

Hồ sơ chi tiết tại `D:\DT_CPPS_Migration\20261104`: bảng SHA-256 của 26.579
tệp trước chuyển, trạng thái Git, danh sách cache đã dọn, Unity đã xóa và các ZIP
đã chuyển riêng. Mọi thay đổi chưa commit lúc chuyển được giữ.

Môi trường MuJoCo là Ubuntu-24.04 với Python `/home/admin/dt-cpps-venv/bin/python`.
Vị trí đĩa WSL và kiểm tra Docker sau chuyển được ghi trong `wsl_migration.json`
và hồ sơ kiểm tra đi kèm. Tên distro và đường dẫn Linux không cần đổi.

Đĩa WSL hiện ở `D:\WSL\Ubuntu-24.04\ext4.vhdx`. Mã băm khi đã dừng khớp trước/sau chuyển; 19 ảnh Docker và phiên bản Python/MuJoCo/NumPy giữ nguyên.
