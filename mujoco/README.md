# Lõi mô phỏng MuJoCo của trạm phân loại

Mô hình này chuyển bố cục Fusion 360/CAD hiện có sang mô phỏng vật lý MuJoCo. Hệ trục giữ nguyên: **+X** ngang sang phải, **+Y** từ băng tải vào dãy sáu hộp, **+Z** hướng lên; đơn vị trong MuJoCo là mét, kg, giây.

## Thành phần

**Cập nhật 30/10/2026:** đã thêm plant chức năng tham số hóa cho kích thước bao mới,
phôi 60 mm và ba quang, ở `configs/measured_cell_20261030.json`.
Xem [hướng dẫn nhập thông số và đo tiếp](../docs/parameterized_core.md).
Mô tả baseline bên dưới vẫn đúng cho profile `simulation.json`, không phải profile mới.

**Đường chạy hiện tại:** xem [lõi dạng mô-đun và tiếp nhận số đo](../docs/modular_twin.md).
Thông số nằm ở `configs/simulation.json`; `run_twin.py --config` tạo MJCF riêng
và lưu cấu hình hiệu lực/manifest cho từng lượt. `check_twin.py --extended`
thử thêm các biến thể profile và trễ/mất dữ liệu mạng giả lập.

Đã thêm [dự báo nhiều kịch bản 1D và supervisor](../docs/predictive_core.md),
bật bằng `configs/predictive_demo.json`. Đây chưa phải rollout tiếp xúc
MuJoCo toàn hệ thống; baseline mặc định vẫn tắt chức năng này.

- [`production_cell.urdf`](production_cell.urdf): cây động học chuẩn gồm khung cố định, trục X, trục Y, xi lanh hạ A2 và xi lanh đẩy A1; có trục, hành trình, quán tính giả định và sổ giả định ngay đầu tệp.
- [`build_cell.py`](build_cell.py): kết hợp URDF với `cad_reference/production_twin_v0_parts.csv` (xuất từ nguồn Fusion) để tạo [`production_cell.xml`](production_cell.xml). Không cần chạy Fusion 360 trong WSL.
- [`production_cell.xml`](production_cell.xml): MJCF có hai băng tải dùng vận tốc bề mặt tiếp xúc, thanh dẫn, sáu hộp, robot XY, giác hút, phôi tự do và tia cảm biến PS1/PS2.
- [`run_cell.py`](run_cell.py): API điều khiển mô phỏng và chu trình nghiệm thu một phôi: băng tải 1 → A1 đẩy → băng tải 2 → PS1/PS2 → gắp → hộp 1–6.

## Chạy trong WSL Ubuntu

Từ thư mục gốc của kho, lần đầu cài môi trường Python **trong hệ tệp Linux**:

```bash
python3 -m venv ~/dt-cpps-venv
~/dt-cpps-venv/bin/python -m pip install 'mujoco==3.16.0'
```

Môi trường `~/dt-cpps-venv` đã được cài trên máy này. Sau khi sửa URDF hoặc `parts.csv`, tạo lại MJCF:

```bash
python3 mujoco/build_cell.py
~/dt-cpps-venv/bin/python mujoco/run_cell.py --commission --bin 1 --log /tmp/cell_bin1.csv
```

Đổi `--bin` thành 1–6. Thêm `--view` để xem chu trình chạy trong cửa sổ MuJoCo nếu WSLg có giao diện đồ họa; cửa sổ giữ nguyên kết quả cuối để bạn xem và tự đóng. Tệp CSV ghi trạng thái theo thời gian khoảng 0,1 giây. Xem trước hình tĩnh tại [`preview.png`](preview.png).

Kiểm tra URDF bằng `cadgen urdf validate mujoco/production_cell.urdf --strict` từ PowerShell. Có thể xem URDF trong CAD Viewer; MJCF mới là mô hình đầy đủ với băng tải, hộp, cảm biến và phôi.

## Giao diện điều khiển bước đầu

`Cell.belts_at(front=..., long=...)` đặt vận tốc hai băng tải (m/s); `Cell.targets(x_joint=..., y_joint=..., a2_joint=..., a1_joint=...)` đặt vị trí đích (m); `Cell.grip(True/False)` bật/tắt lực bám tiếp xúc của giác hút; `Cell.step()` tiến mô phỏng; `Cell.observe()` trả thời gian, vị trí phôi, PS1/PS2, bốn trục và lệnh hút. Đây là giao diện phần mềm để sau này nối PLC, đồng bộ thời gian, mạng và bộ dự báo.

## Baseline dùng tín hiệu và ước lượng

Chạy `run_twin.py` thay cho commissioning để dùng bộ ước lượng PS1/PS2
và máy trạng thái mới. Xem [cách chạy, giả định và kết quả nghiệm thu](../docs/dt_estimator_sequence.md).
Mặc định dừng ở giới hạn quan sát; `--assume-open-loop` cho phép thử trọn
chu trình trong mô phỏng với các giả định XY/A2/chân không được ghi rõ.
`check_twin.py` chạy 12 kịch bản; `test_sequence.py` kiểm tra logic bằng thư viện chuẩn.

## Giới hạn hiện tại

Lớp tín hiệu, ghi dữ liệu và phát lại đã được bổ sung ngày 27/10/2026; xem
[tiến độ và hướng dẫn chạy](../docs/dt_core_progress.md). Riêng lệnh
`run_cell.py --commission` vẫn dùng trạng thái chuẩn. Baseline mới ở
`run_twin.py` dùng tín hiệu và ước lượng, với giới hạn vòng hở nêu trên.

- Kích thước toàn trạm và đa số hành trình được **ước lượng từ ảnh và mô hình Fusion**, chưa đo trực tiếp. Hành trình 75 mm của A2 đọc từ nhãn xi lanh; hành trình A1 và giới hạn XY là giả định.
- Khối lượng, ma sát, tốc độ, lực hút 5 N và quán tính là thông số nghiệm thu mô phỏng, **chưa được hiệu chuẩn** trên máy thực. Giác hút dùng contact adhesion; chưa có mô hình áp suất khí nén, rò rỉ hay kiểm tra Vacuum_OK.
- Chu trình nghiệm thu dùng vị trí phôi trực tiếp từ bộ giải vật lý để canh gắp. Khi ghép PLC phải thay bằng vị trí suy ra từ PS1/PS2, encoder hoặc camera đã hiệu chuẩn.
- Chưa có cầu nối live với TIA Portal/PLC, ROS 2; chưa đo độ trễ đồng bộ và chưa huấn luyện ML. Chu trình nghiệm thu chạy **một phôi mỗi lần reset**, kiểm tra riêng từng hộp.
