# Bản bàn giao cần giữ — 2026-11-06

Đọc tệp này và AGENTS.md để tiếp tục; không cần đọc lại toàn bộ chat.

## Mục tiêu và quy tắc

Nghiên cứu phương pháp giám sát sự kiện bằng DT dự báo, xét tuổi/chất lượng và
lịch sử dữ liệu. Dây chuyền MuJoCo là một bệ thử; chưa có kiểm chứng đa máy.
Tự cấu hình PLC là mục tiêu dài hạn, chưa đạt. Không bắt buộc ML thắng, không
che kết quả bất lợi, không nới ngưỡng sau kết quả rồi gọi là kiểm chứng mới.

Làm ở D:/Projects/network-aware-production-twin; C:/Users/Admin/Documents/
ChatGPT/plc là đường tương thích. Repo: github.com/Namct123/network-aware-production-twin.
WSL Ubuntu-24.04; Python /home/admin/dt-cpps-venv/bin/python; Docker engine ở WSL.
Được cập nhật nguồn GitHub, chưa được đẩy image registry. Báo cáo tiếng Việt
ít thuật ngữ, ghi từng mục ở docs/nhat_ky_cong_viec.md; ưu tiên tái sử dụng.

## Mã và thông số

- event_window.py: lõi so miền dự kiến với sự kiện, không biết thiết bị.
- eta_monitor.py: bộ nối xung quang, kiểm tra dữ liệu và dự phòng; chỉ cảnh báo.
- eta_ml.py/models/: Ridge, bù hằng và miền sai số đã khóa, không ghi PLC.
- study_network_clock.py: phép so đồng hồ/tuổi mới, kế hoạch Git5a39fe5.
- research_scope.json:35 tệp nguồn cho Docker tập trung; configs/ có tham số
  đổi được. Bộ nối mới cần mô hình/hiệu chuẩn riêng, không dùng trọng số như
  mô hình phổ quát. Lõi/profile/CAD và bằng chứng lịch sử vẫn giữ trong kho đầy đủ.

CPU1214C DC/DC/DC; chưa có S7 live. Trong mã: ps1=PS2 vật lý, ps2=PS3 vật lý,
transfer_present=PS1 trên đầu xi lanh đẩy. CAD V5 và MuJoCo chức năng khác hình
học; số đo là sơ bộ. Không dùng Unity/Factory I/O; tạm hoãn RL, mở rộng giao
diện và điều khiển toàn mô hình.

## Kết quả và giới hạn quan trọng

Bộ cũ:61 đoạn học;31 bản ghi/465 phát lại. ML MAE15,4 ms so với bù hằng18,1 ms
trên9 ca, nhưng cảnh báo bằng hoặc muộn20–40 ms; ngoài miền ML kém hơn.

Bộ mới đã khóa trước chạy:12 điều kiện,36 bản ghi/720 phát lại.6/12 ca bình
thường thiếu đầu xung; trong6 ca đủ dữ liệu, ngưỡng cũ báo nhầm2 ca dù không
trễ. Trễ80 ms: thời gian nguồn2 ca, thời gian nhận5 ca. Trễ120 ms có chặn tuổi:
từ chối tất cả, không phải chẩn đoán đúng. Kết quả không đạt mục tiêu0 báo nhầm.
12 cặp mất PS3/băng đứng cùng quan sát, nên không tách được nguyên nhân.

171 kiểm tra lõi WSL,16 kiểm tra Docker; không suy thành độ chính xác máy thật.
Đọc chi tiết: docs/doi_chung_thoi_gian_20261106.md.

## Docker, bài báo và bước kế tiếp

Accepted vẫn production-twin-dt:accepted-20261103-software-v2,
ID sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8.
Bản mới candidate-20261106-network-clock chờ người dùng kiểm tra; chỉ khi người
dùng nghiệm thu mới nâng tag. IDs/hash ở docker/RELEASES.md.

Nguồn paper/title_abstract.tex riêng, paper/body.tex chính; PDF ở
reports/dt_cppps_manuscript_virtual.pdf. Chuẩn LNCS; tác giả và vật lý trống,
chưa duyệt/nộp. Bản rộng cũ Git7bbde4a. Phạm vi ở docs/pham_vi_bai_bao_20261106.md.

Tiếp theo: rà mô hình cạnh/lấy mẫu/khởi đầu; tạo tập hiệu chuẩn khác và khóa
trước một tập chưa xem; sau đó thêm bộ nối sự kiện xi lanh. Đo máy thật sau.
Không dùng lại bộ mới đã xem để tự chứng nhận sau khi sửa.

Tệp này là bản tóm tắt làm việc, chưa xóa hay compact chat. Sau lượt hiện tại,
người dùng có thể dùng /compact. Nếu mở chat khác, yêu cầu đọc tệp này và
AGENTS.md, kiểm tra Git HEAD/trạng thái rồi tiếp tục đúng phạm vi trên.
