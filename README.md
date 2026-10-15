# Network-Aware Production Twin

Kho làm việc chung cho mô hình số của hệ thống hai băng tải, cơ cấu đẩy A1, giàn XY và đầu hút. Kho gồm nguồn CAD, gói Unity và cầu nối Factory I/O. Các kích thước CAD hiện là **ước lượng từ ảnh**, chưa được đo trên máy; PLC, mạng và digital twin trực tuyến chưa kết nối.

## Bắt đầu

- **Unity:** dùng Unity `6000.0.84f1`, chép `unity/Assets/ProductionTwin` cùng `ProductionTwin.meta` vào thư mục `Assets` của dự án. Mở scene `ProductionTwin.unity`; hướng dẫn ở [unity/README.md](unity/README.md).
- **Fusion 360/CAD:** nguồn dựng ở `fusion/ProductionTwin_V0/ProductionTwin_V0.py`. Bản tham chiếu V4 nằm trong `cad_reference/`.
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

## An toàn

Các tool ghi chỉ tác động đến Modbus server ở địa chỉ đã cấu hình. Giữ host là
`127.0.0.1` để bảo đảm chúng chỉ điều khiển mô phỏng Factory I/O trên máy này.
