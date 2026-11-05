# Predictive Digital Twin cho dây chuyền gắp–thả

Mục tiêu: **so sánh dữ liệu thực nhận với dự đoán để nhận biết bất thường,
đánh giá độ không chắc chắn và chọn cấu hình PLC giúp hệ thống tiếp tục làm việc
khi còn đủ điều kiện**. Đối tượng gồm hai băng tải, xi lanh đẩy A1, robot XY,
xi lanh A2, giác hút và các cảm biến. Camera là nguồn quan sát có thể bổ sung,
chưa coi là phần cứng đã triển khai.

## Trạng thái trung thực

- Đã có mô phỏng MuJoCo, lõi nhận tín hiệu, ước lượng, dự báo, giám sát mạng,
  giảm tốc/HOLD và công cụ lưu/phát lại thí nghiệm.
- Chưa có kết nối điều khiển PLC thật, hiệu chuẩn vật lý, mô hình ML đã huấn luyện
  hoặc bằng chứng tổng thể tốt hơn bộ điều khiển đối chứng được thiết kế tốt.
- CAD V5 và mô hình MuJoCo chức năng chưa đồng bộ đầy đủ. Độ không chắc chắn
  hiện là giả định kỹ thuật, chưa phải khoảng tin cậy đã kiểm chứng.
- **Bản accepted vẫn là `accepted-20261103-software-v2`.** Các bổ sung mới chỉ
  là candidate; kiểm tra tự động không thay cho nghiệm thu người dùng.

## Đọc và chạy từ đâu?

1. [Mục tiêu, tiêu chí và lộ trình nghiên cứu](docs/huong_nghien_cuu_hien_tai.md).
2. [Thử nghiệm sai lệch dự đoán–quan sát](docs/sai_lech_du_doan_quan_sat.md).
3. [Hướng dẫn Docker](docs/docker.md), [tham số nhập/thay đổi được](docs/parameterized_core.md).
4. [Nhật ký công việc](docs/nhat_ky_cong_viec.md).

```powershell
# Chạy bản đã nghiệm thu, không tự nâng lên bản mới
./scripts/docker_dt.ps1 -Mode demo -Tag accepted-20261103-software-v2
# Giao diện giải thích cục bộ
python web/server.py --port 8766
```

Mở http://127.0.0.1:8766/anatomy.html để xem bảy tình huống và so sánh những gì
máy làm với những gì DT biết. Đây là phát lại mô phỏng, không điều khiển PLC.
[Hướng dẫn Anatomy](docs/truc_quan_anatomy.md).

## Tổ chức dự án

| Thư mục | Vai trò |
|---|---|
| `mujoco/` | Lõi, mô hình chức năng, profile, thí nghiệm và kiểm tra |
| `docker/` | Đóng gói candidate, bằng chứng phiên bản, các bản đã nghiệm thu |
| `docs/` | Hướng dẫn hiện hành, kết quả và nhật ký |
| `web/` | Giải thích hệ thống, phát lại và theo dõi thí nghiệm |
| `cad_reference/`, `fusion/`, `scenes/` | Hình học và nguồn CAD; giữ nguồn baseline cần để tái lập |
| `paper/` | Một nguồn bài báo hiện hành, title/abstract tách riêng; kết quả vật lý còn trống |
| `reports/` | Bản PDF hiện hành và hai tài liệu nhập môn |
| `output/` | Dữ liệu thí nghiệm/tệp sinh ra, không đưa vào Git |

Nguồn bài: [paper/README.md](paper/README.md). Các bản nháp trùng và gói kiểm tra
cũ đã bỏ khỏi cây làm việc; [biên bản dọn](docs/don_du_an_20261105.md).
Không dùng Unity hay Factory I/O. Các thí nghiệm/bản Docker lịch sử cần để kiểm
chứng vẫn được giữ; không sửa lại bằng chứng cũ.

## Đối chứng bắt buộc

So điều khiển tuần tự, điều khiển theo quy tắc thích nghi và Predictive DT trên
cùng mô hình, cùng thông tin quan sát và cùng kịch bản. Khi đánh giá thêm ML,
so thêm DT có/không ML. Khi thêm camera, các phương án đối chứng cũng phải
được dùng camera. Đo sản phẩm hoàn thành, thời gian dừng, vi phạm ràng buộc,
báo nhầm và thời gian phát hiện; không chỉ đếm số lần phát hiện hoặc số mô đun.

Quy tắc làm việc nhóm: [CONTRIBUTING.md](CONTRIBUTING.md).
