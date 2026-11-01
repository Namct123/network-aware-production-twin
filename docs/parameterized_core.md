# Lõi DT tham số hóa — 30/10/2026

## Trạng thái và phạm vi

Đã thêm một plant MuJoCo chức năng sinh trực tiếp từ profile JSON, thay vì tiếp tục
co giãn bản XML cũ. Nó dùng các kích thước bao mới, phôi 60 mm và ba quang. Đây là
**mô hình vật lý chức năng giản lược**, không phải toàn bộ mesh/CAD V5 đã được đồng bộ
hoặc mô hình máy thật đã hiệu chuẩn. Baseline XML 22 mm và bản Docker đã chấp thuận
`accepted-20261030-core-v1` được giữ nguyên để đối chiếu.

Profile mới: `mujoco/configs/measured_cell_20261030.json`.
Các giá trị trong đó đều có thể chỉnh; những giá trị chưa đo vẫn là giả định được
ghi rõ, không phải thông số cố định trong thuật toán. Mô hình vẫn dành cho một phôi
mỗi lần reset và sáu hộp, với cấu trúc bốn khớp cố định. Muốn thay cấu trúc máy phải
đổi mô hình; muốn thay thông số đang hỗ trợ thì chỉ đổi profile/CSV.

## Các kích thước đã áp dụng

| Đại lượng | Giá trị sơ bộ được người dùng cung cấp |
|---|---|
| Tiết diện nhôm | 20 × 20 mm |
| Lòng khung ngang × dọc băng | 465 × 460 mm |
| Mặt dưới thanh di chuyển | 325 mm trên đế |
| Bề rộng hữu dụng hai băng | 80 mm |
| Chiều dài băng dọc / băng ngang | 530 / 470 mm |
| Mặt băng trên đế | 100 mm |
| Phôi | 60 × 60 × 60 mm |
| Mặt tiếp xúc giác hút thu / duỗi | 230 / 130 mm trên đế |
| Hành trình dụng cụ suy ra | 100 mm, chưa xác nhận hành trình ghi trên xi lanh |
| Độ hạ tới mặt trên phôi suy ra | 70 mm |

Gốc XY, vị trí hộp, gá, A1 và nhiều chi tiết chưa đo. Quan hệ 270 mm và bố trí quang
được kế thừa theo cách diễn giải đã ghi ở `cad_v5_measured.md`; không coi tọa độ CAD
là số đo world độc lập. Độ không chắc của các số đo chưa được cung cấp, giữ `null`.

## Ba cảm biến: tên vật lý và vai trò phần mềm

| Trên máy/CAD | Tín hiệu trong lõi | Vai trò |
|---|---|---|
| PS1 trên đầu đẩy, quét +Y cùng chiều A1 | `transfer_present` | Phát hiện phôi tới vùng đẩy, thay cấp phôi chỉ theo thời gian |
| PS2 bên băng, giữ vị trí Y=-215 mm trong bố trí CAD | `ps1` | Mốc đầu để ước lượng trên băng dọc |
| PS3 bên băng, Y=+45 mm sau dịch 50 mm từ vị trí cũ | `ps2` | Mốc sau/canh gắp |

Tên `ps1`/`ps2` là alias logic cũ của estimator, KHÔNG phải tự động đổi địa chỉ PLC.
Ánh xạ rõ ở `mechanics.sensor_roles` và `summary.json`. `ps2_stuck_low` trong CLI
của profile mới vì vậy là lỗi **quang vật lý PS3**, không phải quang vật lý PS2.
Chưa xác nhận chân I/O thật nên không tự điền địa chỉ.

Quang đầu đẩy được gắn vào body A1 nên di chuyển theo A1. FEED có độ bù căn giữa
phôi sau phát hiện; độ bù này còn giả định và nằm trong profile. Nếu quang không
phát hiện, giới hạn hành trình dựa trên reset đã biết yêu cầu HOLD trước giới hạn
đỡ phôi theo mô hình. Đó là bảo vệ theo giả định tốc độ/reset, chưa là bảo đảm an toàn
máy thật với trượt băng, nhiều phôi hoặc phôi đến ngẫu nhiên.

## Giác hút và cơ cấu

Một giác hút được xấp xỉ bằng **bốn điểm tiếp xúc số trong cùng một vùng hút**,
không phải thêm bốn giác hút vật lý. Tổng lực bám hiệu dụng N được chia cho các điểm;
vị trí/kích thước vùng tiếp xúc và các hệ số ma sát đều là tham số. Không set-parent,
teleport hoặc dùng weld hoàn hảo. Hai thử nghiệm đầu dùng một điểm tiếp xúc đã không
đặt phôi đạt; các log thất bại vẫn giữ trong `output/measured_profile_first_20261030`
và `output/measured_profile_contact6_20261030`.

Mô hình vùng tiếp xúc mới đã có chu trình đặt phôi đạt, nhưng lực/mô-men giữ chưa được
đo. Đây chưa phải mô hình áp suất, rò khí hoặc biến dạng cao su. Không nhập bar/kPa
vào trường `plant.vacuum_adhesion_n` có đơn vị N.

Đích hạ gắp và hạ nhả hộp được tách riêng; loader kiểm tra chiều cao tiếp xúc và
khoảng hở qua thành hộp. Thay kích thước phôi/cao độ có thể cần cập nhật các giá trị
liên quan cùng lúc. Tốc độ khớp, gain, damping, khối lượng và quán tính đều nhập được.
Gia tốc thực cần dùng dữ liệu để nhận dạng đáp ứng servo; chưa có trường gia tốc độc
lập. Không tạo ô nhập cho tham số mà mô hình chưa sử dụng.

## Các tệp bạn có thể nhập/sửa

1. `mujoco/configs/measured_cell_20261030.json`: tất cả thông số thực dùng của profile mới.
2. `mujoco/configs/measurements_to_fill_20261030.csv`: bảng nhập mới, để trống giá trị
   chưa đo. Có 194 trường số, bao gồm cả thiết lập mô phỏng/điều khiển; **không phải
   cả 194 trường đều phải đo trên máy**.
3. `docs/parameter_catalog_20261030.json`: giá trị hiện tại, đơn vị, trạng thái nguồn
   và cờ có đang dùng trong mô hình này không. Hai trường FEED theo thời gian của
   baseline được đánh dấu không hoạt động khi dùng cơ chế quang mới.
4. `parameters.json` trong mỗi lượt chạy: kiểm kê từ đúng profile thực dùng, không
   dựa vào danh mục tĩnh. Khi sửa JSON làm khác giá trị đo đã ghi, trạng thái thành
   `changed_since_measurement`, không âm thầm gọi giá trị mới là đã đo.

### Cách nhập bằng CSV

- Sao chép CSV mẫu sang tên phiên đo riêng trước khi nhập. Mở bằng Excel/LibreOffice
  hoặc trình soạn thảo; giữ nguyên tiêu đề các cột và `path`.
- Chỉ điền `value` cho mục đã có số đo; để trống mục chưa đo, không dùng 0 thay trống.
- Đơn vị SI: m, s, kg, N. 95 mm = 0.095 m; 30 g = 0.030 kg; 20 ms = 0.020 s.
- Dùng dấu chấm thập phân. Ghi `measured_on` dạng YYYY-MM-DD, `method`, người đo;
  `uncertainty` chưa biết thì để trống. Các thiết lập số/thuật toán dùng JSON hoặc
  ghi rõ đây là lựa chọn thiết kế, không giả làm số đo vật lý.
- Trường bool và nhãn vai trò cảm biến sửa trực tiếp trong JSON, không ép thành float CSV.

Từ môi trường Python của dự án:

```text
python mujoco/calibrate.py --base mujoco/configs/measured_cell_20261030.json --measurements mujoco/configs/measurements_session.csv --output mujoco/configs/machine_session.json --name machine_session_partial
```

Importer kiểm tra cả lô trước khi ghi, từ chối ghi đè profile cũ. Mẫu trắng không
tạo ra profile hiệu chuẩn. Muốn xuất mẫu mới theo profile khác:

```text
python mujoco/calibrate.py --base mujoco/configs/machine_session.json --export-template mujoco/configs/next_session.csv
```

## Ưu tiên những gì cần đo tiếp

| Ưu tiên | Cần đo/nhận dạng | Trường cấu hình chính |
|---|---|---|
| 1 | Khối lượng phôi và tải thực | `plant.product_mass_kg` |
| 1 | Hành trình A1, giới hạn XY và mốc home | `geometry.joint_limits_m`, `motion.home_xy_m`, `mechanics.pusher_rest_xyz_m` |
| 1 | Tọa độ tia quang, vị trí hộp theo cùng gốc | `geometry.ps_y_m`, `geometry.optical_xz_m`, `geometry.bin_centers_xy_m` |
| 1 | Tốc độ thực so với lệnh, quãng trôi của mỗi băng | `motion.*speed_m_s`, `plant.belt_speed_scale`, `mechanics.front_stop_coast_m`, `estimator.stop_coast_m` |
| 1 | Thời gian A1/A2 và tốc độ các trục | `motion.rates_m_s`, các thời gian chờ/ổn định |
| 1 | Lực và mô-men giữ của giác hút, thời gian hút/nhả | `plant.vacuum_adhesion_n`, `plant.cup_friction`, `motion.grip_wait_s`, `motion.release_wait_s` |
| 2 | Ma sát và quán tính để khớp đáp ứng vật lý | `plant.*friction`, `plant.link_inertials`, gain/damping |
| 2 | Sai số mốc, trôi ước lượng, dừng và canh gắp | `estimator.*`, `prediction.stop_margin_m` |
| 2 | Chu kỳ lấy mẫu, trễ đầu-cuối, jitter và mất dữ liệu | `timing.*`, `network.*` |

Hệ số ma sát xoắn/lăn trong MuJoCo là tham số hiệu dụng của tiếp xúc, không cùng
ý nghĩa với hệ số trượt. Chúng cần nhận dạng bằng thử tải/tiếp xúc phù hợp. Độ trễ
network hiện là trễ của kênh dữ liệu mô phỏng; mô hình chưa tách động học điện tử
của từng đầu cảm biến, không coi đó là thông số đã đo bằng cách gán 0.

## Chạy và kiểm nghiệm

Docker candidate mới mặc định chạy profile kích thước mới:

```powershell
./scripts/docker_dt.ps1 -Mode demo
./scripts/docker_dt.ps1 -Mode measured-check
./scripts/docker_dt.ps1 -Mode demo -Config machine_session.json -Bin 3
```

Muốn dùng viewer trực tiếp ngoài Docker:

```text
python mujoco/run_twin.py --config mujoco/configs/measured_cell_20261030.json --assume-open-loop --view --output output/measured_view_unique
```

Trong WSL thay `python` bằng Python venv MuJoCo đã cài. Chọn thư mục output chưa có.
Bỏ `--assume-open-loop` thì lõi chủ đích HOLD vì chưa có phản hồi XY/A2 giữa hành
trình/chân không. Không bỏ chặn này để tuyên bố đã điều khiển PLC thật.

`measured-check` kiểm tra 18 ca và có cặp so sánh baseline/predictive riêng của hình
học mới. Nếu hai phương án không khác thời điểm HOLD, báo đúng chênh lệch bằng 0;
không chuyển kết quả 40 ms của baseline cũ sang hình học mới. Bộ `predictive-check`
cũ vẫn dùng baseline cũ để hồi quy, không dùng bộ tiêu chí đó như kết quả đo máy.

Mỗi lượt có `effective_config.json`, `effective_model.xml`, `parameters.json`,
manifest hash, tín hiệu nguồn/nhận, controller, predictor và đáp án đánh giá riêng.
Phải xem cả `placement_pass_evaluator_only`; DONE một mình không đủ kết luận đặt đạt.

Hạng mục mới được đóng Docker candidate để bạn xem. Chỉ sau khi bạn xác nhận đạt
mới gắn tag được chấp thuận tiếp theo; bản `accepted-20261030-core-v1` vẫn giữ nguyên.

Tài liệu kỹ thuật tiếp xúc/rangefinder: https://mujoco.readthedocs.io/en/stable/XMLreference.html
