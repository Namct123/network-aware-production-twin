# MuJoCo + CAD + lõi Digital Twin — gói chuyển máy 29/10/2026

Gói giữ nguyên mã lõi DT hiện có: tín hiệu, cảm biến, mạng giả lập, ước lượng,
điều khiển tuần tự, dự báo, supervisor, đánh giá, ghi/phát lại và cấu hình.
Không cần Fusion, Unity, PLC hoặc tài khoản Codex để chạy mô phỏng.
Internet cần cho lần cài các gói Python; chạy mô phỏng sau cài không cần mạng.

## 1. Lựa chọn nhanh trên Windows

1. Giải nén TOÀN BỘ ZIP vào thư mục bạn có quyền ghi, ví dụ `D:\DT_Package`.
   Không chạy bên trong cửa sổ xem ZIP. Giữ nguyên các thư mục con.
2. Cài Python **3.12 64-bit**, gồm Python launcher (`py`).
3. Bấm `SETUP_WINDOWS.cmd`. Script tạo môi trường `.venv` riêng và cài hai
   phụ thuộc trong `requirements.txt`. Không chép `.venv` từ máy cũ.
4. Bấm `RUN_WINDOWS.cmd`: chạy chu trình gắp thả với lõi DT, có cửa sổ MuJoCo.
5. Cửa sổ có thể đứng ở trạng thái cuối sau khi chu trình xong: đóng cửa sổ
   MuJoCo để kết thúc tiến trình và đọc tổng kết trong terminal.
6. Kết quả mỗi lượt nằm ở thư mục `output/` riêng. Trong cửa sổ viewer,
   nút Run không thay thế chương trình điều khiển: chạy bằng launcher này.

Gói được kiểm tra headless trong WSL Ubuntu 24.04, Python 3.12.3,
MuJoCo 3.16.0, NumPy 2.5.4. Cách chạy Windows native có trong gói nhưng chưa
được kiểm chứng trên một máy Windows thứ hai. Viewer cần driver đồ họa/OpenGL.
Nếu cửa sổ đồ họa lỗi, thử lệnh headless ở mục 3 trước để phân biệt lỗi GUI/lõi.

## 2. Linux hoặc WSL trên máy khác

Trong Ubuntu, chuyển đến thư mục vừa giải nén rồi chạy:

```bash
sudo apt update
sudo apt install python3-venv
python3 -m venv "$HOME/dt-cpps-venv"
"$HOME/dt-cpps-venv/bin/python" -m pip install -r requirements.txt
"$HOME/dt-cpps-venv/bin/python" launch.py demo
"$HOME/dt-cpps-venv/bin/python" launch.py demo --view
```

Dùng Python 3.12 để gần môi trường đã thử. Thay đường dẫn theo nơi giải nén;
không sử dụng `/home/admin` của máy cũ. WSL có giao diện cần WSLg hoạt động.
Thiếu thư viện đồ họa trên Ubuntu có thể cần `sudo apt install libgl1 libglfw3`.
Không cần quyền root để chạy mô phỏng.

## 3. Các lệnh thực hành

Mở terminal tại thư mục chứa `launch.py`. Trên Windows, thay `python` trong các
lệnh dưới bằng `.venv\Scripts\python.exe`; trên Linux dùng Python trong venv.

```text
python launch.py demo
python launch.py demo --view --bin 3
python launch.py fault
python launch.py strict
python launch.py acceptance
python launch.py predictive-check
```

- `demo`: một phôi đến hộp đích, có dự báo; bật giả định XY/A2/hút hở vòng
  CHỈ TRONG MÔ PHỎNG để xem toàn chu trình. Kỳ vọng DONE và placement=true.
- `fault`: chèn PS2 kẹt thấp, kỳ vọng HOLD. Đây là kiểm tra giám sát, không phải
  chứng minh đã chẩn đoán đúng nguyên nhân hay tự phục hồi.
- `strict`: không cho phép các giả định hở vòng, kỳ vọng HOLD vì thiếu phản hồi.
  Đây là kết quả có chủ đích, không phải lỗi cài đặt.
- `acceptance`: bộ 12 trường hợp baseline; `predictive-check`: bộ 10 trường hợp
  so sánh nền/dự báo. Các bộ này không mở viewer. Mã thoát 0 biểu thị đạt tiêu chí.
  Thời gian tính và deadline có thể khác trên CPU/tải hệ thống khác nhau.

Trong thư mục lượt chạy, đọc `summary.json`; xem `controller_state`, `hold_reason`,
`placement_pass_evaluator_only`. `ground_truth.jsonl` chỉ dùng đánh giá, không được
đưa vào bộ điều khiển. Các log cảm biến, controller, prediction và manifest giúp
truy vết kết quả. Đường chạy commissioning cũ trong `run_cell.py` dùng ground truth;
launcher mặc định dùng `run_twin.py`, tức lõi DT tách thông tin quan sát.

Kiểm tra logic không cần viewer:

```text
python -m unittest discover -s mujoco -p "test_*.py"
```

## 4. Mở CAD

- Mới nhất: `output/cad/production_twin_v5.step` (đầu hút thu).
- Tư thế gắp: `production_twin_v5_pick.step`.
- Hạ hết hành trình: `production_twin_v5_extended.step` — chỉ đối chiếu hành trình;
  có thể đi vào vùng phôi, không dùng làm đích gắp mặc định.
- Mỗi bản có GLB có màu cùng tên; xem bằng phần mềm hỗ trợ GLB. STEP dùng mm,
  MuJoCo dùng m; khi nhập phần mềm khác phải kiểm tra đơn vị.
- Trong Fusion 360: Upload STEP hoặc Open từ máy tính theo giao diện bản Fusion
  đang dùng. Không cần chạy script để xem STEP đã xuất.
- Nguồn Fusion V5: `fusion/ProductionTwin_V5/ProductionTwin_V5.py`, phụ thuộc
  thư mục `fusion/ProductionTwin_V0` đã kèm. Trong Scripts and Add-Ins của Fusion,
  chọn script V5 ở đúng cây thư mục rồi Run; script tạo tài liệu mới và xuất vào
  `output/cad`. Sao lưu nếu bạn đã có tệp trùng tên trước khi chạy script dựng lại.
- Có `.f3d` V4 trong `cad_reference/` để tham khảo phiên bản cũ. Gói không có
  `.f3d` V5 đã lưu; dùng STEP V5 hoặc chạy nguồn Fusion V5 khi cần.

Nguồn CAD Python ở `scenes/`, helper ở `scripts/`. Việc dựng lại bằng cadgen cần
môi trường CAD riêng (cadgen/build123d, Pillow, trimesh); không nằm trong hai
phụ thuộc tối thiểu chạy DT. Không cần cài chúng để xem CAD hoặc chạy MuJoCo.

## 5. Đọc trước khi đổi thông số

**CAD V5 và mô phỏng baseline chưa đồng bộ hình học.** CAD V5 có phôi 60 mm,
ba quang và các số đo sơ bộ mới; baseline MuJoCo giữ hai quang và phôi 22 mm
đã dùng cho các thử nghiệm. Tên PS trong CAD không tự ánh xạ sang địa chỉ PLC.
Gói giữ nguyên khác biệt này, không biến kết quả cũ thành nghiệm thu hình học V5.
Xem `docs/cad_v5_measured.md` và `docs/geometry_survey_20261028.md`.

- Chỉnh tham số chạy tại `mujoco/configs/simulation.json`, hoặc sao chép profile
  và gọi `python mujoco/run_twin.py --config <profile.json> --output <thu_muc_moi>`.
- `predictive_demo.json` bật supervisor; `survey_20261028.json` là hồ sơ đo,
  KHÔNG phải profile chạy có thể đưa thẳng vào `--config`.
- Đọc `docs/modular_twin.md` và `mujoco/configs/physical_measurements.csv` trước
  khi nhập số đo. Thay riêng kích thước phôi không bảo đảm cơ cấu vẫn gắp đúng.
- `unity/Assets/ProductionTwin/parts.csv` chỉ là bảng chi tiết baseline cần cho
  `mujoco/build_cell.py`; gói này không chứa project Unity đầy đủ.
- Không chạy `build_cell.py` để tự động chuyển V5: nó đọc bảng baseline và URDF
  hiện có. Các script xuất Unity cũ là nguồn tham khảo, không phải đường đồng bộ V5.

## 6. Giao diện web tùy chọn

```text
python web/server.py
```

Mở `http://127.0.0.1:8765`. Replay trong `web/data` là dữ liệu mô phỏng lưu sẵn,
không phải dữ liệu live. Máy chủ mặc định có phát lại và bài thực hành dự báo 1D.
Muốn chạy job mô phỏng từ web trên Windows cần WSL, xem `docs/live_experiments.md`:

```text
python web/server.py --enable-experiments --wsl-distro <ten_distro> --simulation-python <duong_dan_python_linux>
```

Đừng bấm script web chạy thí nghiệm với đường dẫn mặc định `/home/admin` trên máy
khác. Launcher `launch.py` là cách chính để chạy trực tiếp, không cần cầu nối WSL.

## 7. Phạm vi và tính toàn vẹn

Đây là gói mô phỏng nghiên cứu, chưa có PLC live, chưa hiệu chuẩn vật lý, chưa có
tự phục hồi hoàn chỉnh. Dự báo hiện là mô hình dừng 1D, không phải 54 kiểu lỗi hoặc
54 rollout tiếp xúc MuJoCo toàn hệ. Tệp thông số và lõi DT được giữ để tiếp tục phát triển.

Không kèm môi trường Python, tài khoản, khóa, cache, bài báo hay tệp cá nhân khác.
`MANIFEST.json` ghi kích thước/SHA-256 các tệp và phiên bản môi trường gốc.
Giữ nguyên bản ZIP gốc để đối chiếu khi chỉnh sửa.
