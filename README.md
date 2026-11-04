# Network-Aware Production Twin

Kho làm việc chung cho mô hình số của hệ thống hai băng tải, cơ cấu đẩy A1,
giàn XY và đầu hút. Gồm nguồn CAD, Unity, lõi DT chạy MuJoCo, Docker, trang
trình bày và tài liệu. Một số kích thước đã cập nhật theo số đo sơ bộ người dùng;
động lực học chưa hiệu chuẩn và chưa kết nối điều khiển PLC thật.

**Bản phần mềm trước khi đo máy — v2:**
[hướng dẫn và phạm vi](docs/phan_mem_truoc_khi_do_may.md).
Có cổng dữ liệu mẫu liên tục, trang theo dõi và một lệnh kiểm tra toàn bộ nhóm mới:
`./scripts/docker_dt.ps1 -Mode software-check`.
Bản v2 được người dùng chấp thuận ngày 03/11/2026 và dùng nhãn
`accepted-20261103-software-v2`. Cổng mẫu chưa phải trình đọc S7.
Các nhãn candidate bên dưới ghi lại từng mốc phát triển trước đó.

**Nghiên cứu giới hạn mô hình — 03/11:**
[kế hoạch và cách chạy](docs/nghien_cuu_gioi_han_mo_hinh.md).
Lưới vị trí/tốc độ/tuổi dữ liệu/ma sát so 1D với hai cách chấm MuJoCo;
không dùng MuJoCo làm đáp án vật lý hoặc tự sửa hồ sơ điều khiển.
Ảnh mới `candidate-20261103-boundary-study` chờ kiểm nghiệm.

**Đối chiếu dự báo — 03/11:** [bộ đọc ngoại tuyến](docs/doi_chieu_du_bao.md)
so mô hình 1D và MuJoCo từ cùng ảnh đầu vào, phân biệt kết quả tính thiếu và bị loại.
Không dùng tỷ lệ cùng khuyến nghị làm độ chính xác vật lý. Docker mới:
`candidate-20261103-model-audit`, chờ nghiệm thu.

**Bổ sung 03/11 — dự báo MuJoCo chạy nền:**
[cách chạy](docs/du_bao_nen_quan_sat.md),
[báo cáo đối chứng](docs/bao_cao_du_bao_nen_20261103.md).
Nhánh 1D vẫn quyết định lệnh; MuJoCo nền chỉ ghi quan sát, chưa được cho phép
chạy/dừng/đặt lại máy. Ảnh `candidate-20261103-background-observer` chờ nghiệm thu.

**Bản tích hợp phần mềm số 1 — 01/11/2026:**
[hướng dẫn mở](docs/ban_tich_hop_phan_mem.md),
[báo cáo dễ hiểu](docs/bao_cao_tich_hop_so1.md),
[nhật ký từng mục](docs/nhat_ky_cong_viec.md).
Mã đã qua 93 kiểm tra logic và các kiểm tra tích hợp trong Docker.
Ảnh `candidate-20261031-integrated-core-v1` vẫn chờ người dùng nghiệm thu.
Nhánh dự báo MuJoCo băng/phôi mới chưa được xác nhận đáp ứng hạn 20 ms;
nhánh tính cũ vẫn là mặc định. CAD V5 và cảnh MuJoCo **chưa đồng bộ đầy đủ**.

- [Tải các gói bàn giao](https://github.com/Namct123/network-aware-production-twin/releases).
- [Báo cáo PDF và bản thảo](reports/README.md).
- [CAD V5 STEP](cad_reference/production_twin_v5.step) và
  [nguồn dựng V5](fusion/ProductionTwin_V5/ProductionTwin_V5.py).
- Trang tổng quan: chạy `python web/server.py`, mở `http://127.0.0.1:8765/tong_quan.html`.

## Bắt đầu

- **Docker — lõi DT không cửa sổ:** xem [hướng dẫn chạy và nghiệm thu](docs/docker.md).
  Bản lõi đầu đã được chấp thuận với tag `accepted-20261030-core-v1`; các hạng mục mới
  tiếp tục dùng candidate chờ bạn kiểm nghiệm.
- **Lõi dùng số đo mới, tham số nhập được:** [profile, bảng CSV và hướng dẫn](docs/parameterized_core.md).

- **Unity:** dùng Unity `6000.0.84f1`, chép `unity/Assets/ProductionTwin` cùng `ProductionTwin.meta` vào thư mục `Assets` của dự án. Mở scene `ProductionTwin.unity`; hướng dẫn ở [unity/README.md](unity/README.md).
- **Fusion 360/CAD:** nguồn hiện tại ở `fusion/ProductionTwin_V5/ProductionTwin_V5.py`, bản STEP/GLB V5 nằm trong `cad_reference/`. V0/V4 giữ làm tham chiếu lịch sử; không phải hình học của cảnh MuJoCo đã kiểm tra.
- **MuJoCo/WSL:** URDF, MJCF và chu trình vật lý thử nghiệm cho băng tải, A1, robot XY, A2 và giác hút ở [mujoco/README.md](mujoco/README.md).
- **Lõi Digital Twin:** lớp tín hiệu cảm biến, timestamp, ghi/phát lại dữ liệu và kết quả thử mới nhất ở [docs/dt_core_progress.md](docs/dt_core_progress.md).
- **Cấu hình và số đo:** kiến trúc mô-đun, profile JSON, nhập số đo CSV và mạng giả lập ở [docs/modular_twin.md](docs/modular_twin.md).
- **Dự báo và giám sát:** mô hình 1D nhiều kịch bản có ngân sách tính toán, lựa chọn CONTINUE/HOLD ở [docs/predictive_core.md](docs/predictive_core.md).

## Cách nhóm cùng làm

1. Mỗi người tạo nhánh từ `main` (ví dụ `unity/sensor-visuals`, `plc/sequence`, `twin/prediction`).
2. Ghi thay đổi giao diện tín hiệu, hệ tọa độ, đơn vị đo và giới hạn chuyển động trong [CONTRIBUTING.md](CONTRIBUTING.md) khi nộp pull request.
3. Chỉ ghép vào `main` sau khi người phụ trách phần liên quan xem lại và kiểm tra scene hoặc mô phỏng. GitHub lưu phiên bản và kiểm tra thay đổi; việc ghép hành vi chạy đúng cần hợp đồng dữ liệu và kiểm thử tích hợp.

## Giao diện giải thích Digital Twin

Lõi DT và Docker: [hướng dẫn chạy](docs/docker.md), [tham số máy](docs/parameterized_core.md),
[ước lượng khi đổi tốc độ và giám sát tín hiệu](docs/observer_health.md).
Phần mới: [tái cấu hình phần mềm](docs/reconfiguration.md).
Kiểm chứng mở rộng: [ma trận nhiều seed và biến thiên plant/mạng](docs/robustness.md).
Thử nghiệm tiếp theo: [cap tốc độ theo tuổi dữ liệu và bất định](docs/adaptive_speed.md).
Xử lý sau dừng: [phân loại HOLD và đánh giá điều kiện khôi phục](docs/hold_recovery.md).
Đọc dễ hiểu: [dự án hiện làm được gì](docs/bao_cao_tien_do_de_hieu.md).
Bước mới: [đặt lại để chạy một chu trình mô phỏng mới](docs/dat_lai_chu_trinh_moi.md).
Theo dõi [những gì đã làm và tác dụng/chức năng](docs/dt_core_progress.md).

Mở `web/START_EXPLORER.cmd`, rồi vào http://127.0.0.1:8765 để phát lại 10 ca
MuJoCo và thử trực tiếp bộ dự báo 1D. Xem [hướng dẫn trình bày](web/README.md).
Đây là giao diện dữ liệu mô phỏng, chưa kết nối PLC.

Muốn chạy lượt MuJoCo mới hoặc so sánh nền/dự báo từ web, mở
`web/START_SIMULATION_EXPLORER.cmd`. Xem [bộ chạy thí nghiệm WSL](docs/live_experiments.md).

## Kiểm tra phần mềm

Các bộ kiểm tra hiện tại dùng `unittest` có sẵn trong Python. Chạy trong môi trường
MuJoCo đã cài theo `docker/requirements.lock`, hoặc dùng Docker như hướng dẫn:

```text
python -m unittest discover -s mujoco -p "test_*.py"
python -m unittest discover -s web -p "test_*.py"
python docker/test_delivery.py
```

Lõi hiện chưa có lệnh điều khiển PLC thật. Đọc lại dữ liệu chỉ tạo tệp lệnh để
xem xét. Xem [phạm vi và hướng dẫn tích hợp](docs/ban_tich_hop_phan_mem.md).


## Đánh giá có đối chứng

[Bộ đo thời gian dự báo và 24 lượt lỗi/mạng/sai tham số](docs/danh_gia_co_doi_chung.md). Không thay ngưỡng điều khiển hoặc tự nghiệm thu theo kết quả.

Kết quả 02/11/2026: [báo cáo dễ hiểu](docs/bao_cao_danh_gia_20261102.md). Docker thử nghiệm mới: `candidate-20261102-qualification`, chờ nghiệm thu; giữ nguyên hạn điều khiển.


## Bài báo đang phát triển

[Bản thảo LaTeX hiện tại](paper/README.md) và [PDF lý thuyết/kết quả ảo](reports/dt_cppps_manuscript_virtual.pdf). Phần kiểm chứng vật lý và thông tin tác giả chưa điền; đây là bản làm việc, chưa được tác giả duyệt để nộp.


## Tối ưu MuJoCo — 03/11/2026

[Bản native có số luồng nhập được](docs/toi_uu_du_bao_mujoco.md), [kết quả và giới hạn](docs/bao_cao_toi_uu_20261103.md). Vẫn chưa đạt hạn 20 ms; điều khiển mặc định giữ nhánh 1 chiều.

## Bổ sung ngày 04/11/2026

Hai mục mới: phát lại phiên dữ liệu (giữ cả nhịp im lặng) và gói ZIP hồ sơ
có kiểm tra mã băm. Xem [hướng dẫn](docs/phat_lai_va_dong_goi_phien.md).
Bản mới dùng nhãn `candidate-20261104-stream-evidence`; bản nghiệm thu mặc định giữ nguyên.
