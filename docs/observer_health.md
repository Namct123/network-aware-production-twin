# Bộ ước lượng khi đổi tốc độ và giám sát tín hiệu

**Hạng mục tiếp theo:** [tái cấu hình phần mềm](reconfiguration.md) dùng các dấu
hiệu sức khỏe để giới hạn tốc độ/yêu cầu HOLD trong profile riêng. Những mô tả
“chỉ ghi nhật ký” dưới đây áp dụng cho candidate observer và profile chưa bật
`reconfiguration`, không phải chính sách mới đang bật.

Phiên bản: `candidate-20261030-observer-health`. Chờ bạn kiểm nghiệm; chưa thay
thế bản `accepted-20261030-core-v1`. Không kết nối hoặc điều khiển PLC thật.

## 1. Hạng mục này làm gì?

Trước đây bộ ước lượng chỉ nhận hai cạnh cảm biến với giả thiết tốc độ băng không
đổi. Bản mới ghi lại **lệnh thực sự đã phát**, tính quãng đường theo từng đoạn
tốc độ, kể cả khi không có gói cảm biến mới. Nó không đọc vị trí hoặc vận tốc
thật của phôi trong MuJoCo để điều khiển.

Luồng xử lý:

`MuJoCo → cảm biến mô phỏng → mạng có trễ/mất → bộ ước lượng → trình tự/giám sát → lệnh → MuJoCo`

Mô-đun sức khỏe quan sát gói nhận được, lịch sử lệnh và ước lượng. Ground truth
chỉ đi tới bộ đánh giá và nhật ký riêng. Mô-đun sức khỏe không được nhận nhãn
lỗi chủ động gây ra hoặc thống kê mất gói của bộ giả lập mạng.

Đây là bước bổ sung khả năng quan sát. Chưa có tự chọn cảm biến thay thế, tự khởi
động lại từ HOLD, ROS 2 hoặc mô hình ML mới trong hạng mục này.

## 2. Nguyên lý tối thiểu

Nếu trong một khoảng có nhiều lệnh tốc độ, quãng đường lệnh là:

`D = tổng(v_lệnh_i × thời_gian_i)`.

Ước lượng vị trí tiến theo `y_mới = y_cũ + gain × D + lượng_trôi_khi_dừng`.
Sau khi quan sát được đúng hai cạnh quang theo thứ tự, hệ số được ước lượng từ:

`gain ≈ (khoảng_cách_hai_cảm_biến − trôi_do_các_lần_dừng) / D_giữa_hai_cạnh`.

Đây là hệ số giữa lệnh và chuyển động, **không phải phép đo encoder**. Trước
cạnh thứ hai, dùng gain danh định 1; giới hạn mặc định 0,8–1,2 là giả định cần
hiệu chuẩn. Chênh lệch thời điểm lấy mẫu, ma sát và trượt vẫn gây sai số.

Biên bất định tăng theo thời gian, thay đổi tốc độ và các lần dừng. Khi có cạnh
quang, vị trí được neo lại theo mặt trước phôi và cửa sổ lấy mẫu. Các biên này
là dung sai kỹ thuật, chưa phải khoảng tin cậy thống kê hoặc bảo đảm an toàn.

Gói tại thời điểm t được lấy **trước** lệnh phát tại t. Tích phân dùng khoảng
`[bắt đầu, kết thúc)`, tránh dùng lệnh tương lai cho gói cũ. Khi gói trễ, vị trí
đến thời điểm hiện tại được ngoại suy từ lịch sử lệnh; bộ dự báo dùng tốc độ
trên biên bảo thủ riêng, không ghi đè nó thành vận tốc đã đo.

Giới hạn TRACK dựa trên tổng quãng đường lệnh và thời gian tối đa, tránh lỗi
chia quãng đường cho tốc độ mới nhất khi tốc độ đã thay đổi hoặc đang bằng 0.
Việc căn tâm tại cảm biến xi lanh đẩy cũng tính từ dấu thời gian nguồn ở chế độ mới.

## 3. Các dấu hiệu có thể quan sát

| Mã nhật ký | Ý nghĩa và giới hạn |
|---|---|
| `telemetry_silence` | Không nhận được dữ liệu quá hạn; chưa biết do nguồn hay mạng. |
| `observation_sequence_gap` | Thiếu số thứ tự tại bên nhận; có thể mất gói, đảo thứ tự hoặc gộp bản tin. |
| `observation_time_gap` | Khoảng thời gian giữa hai mẫu nguồn vượt ngưỡng. |
| `stale_observation` | Dữ liệu quá cũ để dùng cho quyết định hiện tại. |
| `required_signal_unusable` | Tín hiệu cần thiết đang thiếu hoặc cũ. |
| `nonmonotonic_observation` | Thứ tự số gói/thời gian không tăng. |
| `contradictory_switches` | Hai công tắc hành trình cùng báo hai đầu. |
| `prolonged_high_while_commanded` | Báo có phôi quá lâu khi vẫn có lệnh chạy: có thể cảm biến kẹt 1, phôi đứng hoặc mô hình sai. |
| `unmatched_pickup_observation` | Có báo tại điểm gắp nhưng chưa có cặp neo hợp lệ. |
| `expected_edge_missing` | Cả biên ước lượng đã vượt vùng cảm biến mà chưa có cạnh: có thể cảm biến, chuyển động hoặc mô hình sai. |

Tín hiệu 0 khi chưa có phôi là bình thường. Không dùng nó để tự kết luận cảm
biến kẹt 0. Home và Vacuum_OK chưa được triển khai phản hồi thật vẫn giữ trạng
thái unavailable; không tạo giả dữ liệu xác nhận. Trạng thái
`no_rule_triggered` chỉ có nghĩa chưa quy tắc nào kích hoạt.

Các cảnh báo của mô-đun sức khỏe hiện **chỉ ghi nhật ký**. Bộ điều khiển và bộ
giám sát dự báo vẫn quyết định HOLD theo các kiểm tra sẵn có; cảnh báo biến mất
không tự xóa HOLD đã chốt.

## 4. Chạy thử trên máy hiện tại

Mở PowerShell tại `C:\Users\Admin\Documents\ChatGPT\plc`:

```powershell
# Demo bình thường, không mở cửa sổ đồ họa
.\scripts\docker_dt.ps1 -Mode demo

# Chạy 13 kịch bản và ghi toàn bộ kết quả
.\scripts\docker_dt.ps1 -Mode observer-check

# Giả lập cảm biến tại điểm gắp luôn bằng 0
.\scripts\docker_dt.ps1 -Mode fault

# Không cho phép bỏ qua các phản hồi chưa được triển khai
.\scripts\docker_dt.ps1 -Mode strict
```

Docker Engine đang ở WSL Ubuntu-24.04, wrapper tự gọi nó. Nếu chép dự án sang
máy khác, xem thêm `docs/docker.md`; cần build candidate trên máy đó.

Mỗi lệnh in thư mục kết quả riêng dưới `output/docker`. Đọc:

1. `summary.json`: DONE/HOLD, lý do, kết quả đặt phôi, cảnh báo đầu tiên.
2. `controller.jsonl`: từng quyết định, lệnh và ước lượng.
3. `health.jsonl`: dấu hiệu tại từng nhịp; trạng thái có thể trở lại bình thường.
4. `issued_commands.json`: thời điểm và tốc độ thực sự đã phát cho băng dài.
5. `prediction.jsonl`: các dự báo và thời gian tính; đây là mô hình 1D CONTINUE/HOLD.
6. `manifest.json`, `effective_config.json`, `parameters.json`: nguồn, cấu hình
   và trạng thái tham số để chạy lại. Ground truth nằm ở file riêng để đánh giá.

## 5. Thay tham số mà không sửa mã

Sao chép `mujoco/configs/observable_cell_20261030.json` thành `my_observer.json`
trong cùng thư mục. Tốc độ dùng m/s, thời gian dùng s, kích thước dùng m.
Ví dụ thay trường `motion.long_speed_schedule` bằng:

```json
[
  {"track_time_s": 0.6, "speed_m_s": 0.22},
  {"track_time_s": 1.0, "speed_m_s": 0.10},
  {"track_time_s": 1.2, "speed_m_s": 0.16}
]
```

Thời gian này tính từ khi vào TRACK, không tính từ lúc bật chương trình. Danh
sách là kịch bản thử lệnh đã biết, chưa phải bộ tối ưu tự tìm tốc độ. Lệnh chỉ
được phát nếu còn ở TRACK; vào HOLD thì không tiếp tục lịch tăng tốc.

```powershell
.\scripts\docker_dt.ps1 -Mode demo -Config my_observer.json
```

Các trường mới có thể chỉnh:

| Trường | Mặc định | Ý nghĩa |
|---|---|---|
| `estimator.command_history_enabled` | true | Bật tích phân lịch sử lệnh. |
| `estimator.command_gain_range` | [0.8, 1.2] | Biên hệ số lệnh/chuyển động; phải bao gồm gain ban đầu 1. |
| `estimator.command_response_uncertainty_s` | 0.04 | Dung sai đáp ứng khi thay tốc độ; chưa đo. |
| `health.enabled` | true | Bật ghi nhận dấu hiệu. |
| `health.max_high_running_s` | 1.0 | Thời gian báo 1 kéo dài khi có lệnh chạy. |
| `health.edge_slack_m` | 0.01 | Dung sai thêm trước khi báo thiếu cạnh dự kiến. |

CSV mới `observer_measurements_to_fill_20261030.csv` có **199 trường số**, gồm
cả thiết lập thiết kế; không có nghĩa phải đo 199 đại lượng vật lý. Các ô giá
trị để trống cho tới khi có dữ liệu. Cách nhập theo `docs/parameterized_core.md`.
Thêm/sửa lịch tốc độ trực tiếp trong JSON; lịch rỗng không có hàng CSV.

## 6. Đọc kết quả kiểm tra đúng phạm vi

Bộ `observer-check` gồm 13 ca: bình thường; deadline vận hành 20 ms; tăng tốc;
giảm tốc; dừng/chạy lại; đổi tốc độ kèm trễ 40 ms; thiếu từng neo; kẹt 1 sau
khởi động; báo có phôi ngay từ đầu; mất toàn bộ dữ liệu; gói cũ; mất gói có seed.

Các ca đúng chức năng dùng ngân sách tính 1 s để không nhầm việc hệ điều hành
tạm dừng tiến trình với lỗi thuật toán. Riêng ca runtime giữ 20 ms như profile
mặc định: DONE hoặc HOLD có phôi được hỗ trợ đều là hành vi chấp nhận cho ca đó.
Không suy ra từ đó rằng deadline 20 ms đã được bảo đảm.

Ca trễ 40 ms có thể HOLD vì bất định tại điểm gắp vượt 10 mm; không nới ngưỡng
để buộc chạy tiếp. Các kết quả này là thử một phôi và các fixture xác định,
không phải độ chính xác phát hiện lỗi trên máy thật, hoặc chứng minh lỗi nào
cũng được phát hiện. Một số lỗi chỉ thấy qua kiểm tra trình tự/timeout.

Lượt phát triển đầu được giữ lại tại `output/observer_dev_20261030_a`: có deadline
miss và ca admission trễ không đạt tiêu chí hỗ trợ phôi. Sau khi bù thời điểm
nguồn và tách phép thử chức năng/thời gian thực, lượt b qua 13 ca. Không xóa lịch
sử lỗi để diễn giải thành hệ thống luôn đạt.

CAD V5 và mô hình chức năng MuJoCo vẫn chưa đồng bộ toàn bộ. Động lực học, chân
không và sai số cảm biến chưa hiệu chuẩn vật lý. Bước kế tiếp sau khi bạn duyệt
hạng mục này là chính sách tái cấu hình có điều kiện và cơ chế quay lại vận hành
có kiểm soát, dựa trên những dấu hiệu và biên bất định đã có.

## 7. Kết quả Docker của phiên bản này

Kiểm tra ngày 30/10/2026, trên máy hiện tại:

| Bộ kiểm tra | Kết quả |
|---|---|
| Logic trong image | 57/57 |
| Biên đóng gói trên host | 2/2 |
| Kịch bản observer mới | 13/13 |
| Kịch bản dự báo legacy | 10/10 |
| Mô hình tham số, budget vận hành 20 ms | 17/18; tốc độ thấp HOLD vì deadline miss |
| Cùng 18 ca, chỉ đổi budget tính thành 1 s để kiểm tra chức năng | 18/18 |
| Demo mặc định | DONE, đặt phôi đạt, thời gian mô phỏng 13,92 s |
| Chế độ strict | HOLD vì thiếu xác nhận XY/A2 trung gian/chân không |

Không gộp hai dòng 18 ca thành tuyên bố thời gian thực đạt. Bản 20 ms ban đầu và
cấu hình đối chiếu 1 s được giữ riêng trong hồ sơ. CI mới dùng cấu hình đối chiếu
1 s cho bộ 18 ca; ca runtime của observer vẫn giữ 20 ms và yêu cầu HOLD đúng khi
quá hạn. Chưa chạy CI trên GitHub.

Ví dụ quan sát trong 13 ca mới: mất toàn bộ telemetry được báo tại t≈0,10 s;
thiếu cạnh pickup được báo ở t≈6,96 s rồi controller HOLD tại t≈7,58 s. Đây là
thời gian của fixture từ lúc bắt đầu mô phỏng, không phải độ trễ phát hiện chung
cho mọi lỗi. Cảnh báo thiếu cạnh không tự gửi lệnh dừng.

Nguồn đầy đủ: `docker/evidence/candidate-20261030-observer-health.json` và
`output/docker/qualification_20261030_observer_health/`.
