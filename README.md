# Network-Aware Production Twin

Kho làm việc chung cho mô hình số của hệ thống hai băng tải, cơ cấu đẩy A1,
giàn XY và đầu hút. Gồm nguồn CAD, Unity, lõi DT chạy MuJoCo, Docker, trang
trình bày và tài liệu. Một số kích thước đã cập nhật theo số đo sơ bộ người dùng;
động lực học chưa hiệu chuẩn và chưa kết nối điều khiển PLC thật.

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
- **Fusion 360/CAD:** nguồn dựng ở `fusion/ProductionTwin_V0/ProductionTwin_V0.py`. Bản tham chiếu V4 nằm trong `cad_reference/`.
- **MuJoCo/WSL:** URDF, MJCF và chu trình vật lý thử nghiệm cho băng tải, A1, robot XY, A2 và giác hút ở [mujoco/README.md](mujoco/README.md).
- **Lõi Digital Twin:** lớp tín hiệu cảm biến, timestamp, ghi/phát lại dữ liệu và kết quả thử mới nhất ở [docs/dt_core_progress.md](docs/dt_core_progress.md).
- **Cấu hình và số đo:** kiến trúc mô-đun, profile JSON, nhập số đo CSV và mạng giả lập ở [docs/modular_twin.md](docs/modular_twin.md).
- **Dự báo và giám sát:** mô hình 1D nhiều kịch bản có ngân sách tính toán, lựa chọn CONTINUE/HOLD ở [docs/predictive_core.md](docs/predictive_core.md).
- **Factory I/O:** cầu nối tùy chọn trong `src/factoryio_mcp`; hướng dẫn bên dưới.

## Cách nhóm cùng làm

1. Mỗi người tạo nhánh từ `main` (ví dụ `unity/sensor-visuals`, `plc/sequence`, `twin/prediction`).
2. Ghi thay đổi giao diện tín hiệu, hệ tọa độ, đơn vị đo và giới hạn chuyển động trong [CONTRIBUTING.md](CONTRIBUTING.md) khi nộp pull request.
3. Chỉ ghép vào `main` sau khi người phụ trách phần liên quan xem lại và kiểm tra scene hoặc mô phỏng. GitHub lưu phiên bản và kiểm tra thay đổi; việc ghép hành vi chạy đúng cần hợp đồng dữ liệu và kiểm thử tích hợp.

## Factory I/O MCP bridge

Cầu nối MCP local để Codex đọc và điều khiển mô phỏng Factory I/O qua driver
**Modbus TCP/IP Server**.

## 1. Cấu hình Factory I/O

1. Mở scene cần sử dụng.
2. Chọn **File > Drivers** (`F4`).
3. Chọn **Modbus TCP/IP Server**.
4. Trong **Configuration**, đặt:
   - Port: `502`
   - Slave ID: `1`
   - Write Digital: `Inputs`
   - Read Digital: `Coils`
   - Write Register: `Input Registers`
   - Read Register: `Holding Registers`
5. Kéo các sensor/actuator vào địa chỉ mong muốn, ghi lại bảng mapping.
6. Nhấn **Connect** và chuyển scene sang **Run**.

Factory I/O dùng địa chỉ hiển thị theo mapping của driver. MCP dùng địa chỉ
zero-based đúng như tham số `address` của Modbus. Hãy thử địa chỉ `0` trước;
nếu mapping xuất ra dùng ký hiệu `00001`/`40001`, địa chỉ MCP tương ứng thường là
`0`.

## 2. Các MCP tool

- `factoryio_status`: kiểm tra kết nối, không ghi dữ liệu.
- `read_digital`: đọc `coils` hoặc `discrete_inputs`.
- `read_analog`: đọc `holding_registers` hoặc `input_registers`, có hỗ trợ scale.
- `set_digital_output`: ghi một coil điều khiển actuator.
- `set_analog_output`: ghi một holding register điều khiển actuator.

Mặc định server chỉ kết nối tới `127.0.0.1:502`, Slave ID `1`.

## 3. Chạy và kiểm tra thủ công

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\check_connection.py
.\.venv\Scripts\python.exe scripts\smoke_mcp.py
```

Nếu cần đổi kết nối, cấu hình các biến môi trường trong mục MCP của Codex:
`FACTORYIO_HOST`, `FACTORYIO_PORT`, `FACTORYIO_DEVICE_ID`, và
`FACTORYIO_TIMEOUT`.

Sau khi cấu hình MCP được thêm, mở task Codex mới hoặc khởi động lại Codex để
server mới xuất hiện trong danh sách tool.

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

## An toàn kết nối

Các tool ghi chỉ tác động đến Modbus server ở địa chỉ đã cấu hình. Giữ host là
`127.0.0.1` để bảo đảm chúng chỉ điều khiển mô phỏng Factory I/O trên máy này.
