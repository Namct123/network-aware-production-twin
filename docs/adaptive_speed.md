# Cap tốc độ theo tuổi dữ liệu và bất định — 31/10/2026

**Kết luận hiện tại:** đã triển khai và thử được quy tắc cap thích nghi, nhưng
chưa có bằng chứng nó tốt hơn cap cố định trên toàn ma trận. Vì vậy đây là chế
độ thử nghiệm riêng; demo mặc định vẫn dùng profile cap cố định trước đó.

Candidate: `candidate-20261031-adaptive-speed`. Chờ người dùng kiểm nghiệm;
không kết nối PLC thật hoặc đổi image accepted.

## Những gì đã làm, chức năng và tác dụng

| Phần | Chức năng | Tác dụng |
|---|---|---|
| `mujoco/speed_policy.py` | Tính cap từ ngân sách gắp và khoảng dừng còn lại. | Thay mức 0,12 m/s cố định bằng mức phụ thuộc dữ liệu quan sát. |
| `reconfiguration.py` | Chốt cap chỉ giảm trong chu trình; HOLD nếu không còn tốc độ phù hợp trong dải đã cấu hình. | Tránh tăng giảm tốc liên tục; giữ nguyên lệnh dừng và lệnh hút khi HOLD. |
| `experiment.py` | Truyền lịch sử lệnh từ thời điểm ước lượng tới hiện tại cho chính sách. | Tính cả chuyển động đã ra lệnh trong thời gian dữ liệu trễ; không dùng vị trí thật. |
| `config.py` và profile adaptive | Kiểm tra nhóm tham số mới và điều kiện phụ thuộc. | Cho phép thay tham số trước lượt chạy, không sửa thuật toán. |
| `check_robustness.py` | Thêm nhóm thứ ba `adaptive` bên cạnh `disabled` và `enabled` cap cố định. | So sánh cùng kịch bản/seed với hai đối chứng; báo cáo riêng kết quả bất lợi. |
| `test_speed_policy.py` | Kiểm tra công thức, latch, thiếu lịch sử, HOLD và kế hoạch ba chính sách. | Ngăn cap tăng trở lại hoặc dùng dữ liệu thiếu để chạy tiếp. |
| Launcher/Docker/CI | Thêm `adaptive-check`, kế hoạch đầy đủ và smoke riêng. | Nhóm chạy lại cùng một thử nghiệm; không tự chuyển demo mặc định sang thuật toán mới. |

## Quy tắc chọn tốc độ

Mỗi nhịp TRACK tính hai trần tốc độ rồi lấy mức nhỏ hơn. Đây là quy tắc đại số
theo mô hình kỹ thuật, chưa phải MPC đầy đủ, ML/RL hoặc nghiệm tối ưu toàn hệ thống.

### 1. Trần từ ngân sách sai số ở điểm gắp

Gọi:

- `L`: giới hạn bất định được phép gắp, hiện 0,010 m.
- `a`: dung sai neo quang, hiện 0,002 m.
- `c`: lượng trôi dừng giả định, hiện 0,002 m.
- `r`: dự phòng thêm, hiện 0,0003 m.
- `g_min`, `g_max`: biên hệ số lệnh/chuyển động, hiện 0,8 và 1,2.
- `A`: tuổi lớn nhất đã quan sát trong chu trình, cộng guard do người dùng đặt.
- `H`: khoảng lấy mẫu nguồn lớn nhất đã quan sát, ít nhất bằng chu kỳ 0,020 s.

Ngân sách còn lại và trần tốc độ:

```text
B = L - a - c - r
v_pick = B / [g_max × A + (g_max - g_min/2) × H]
```

Thành phần H dựa trên cửa sổ bắt cạnh quang: cạnh cho biết mặt trước phôi đã
đến cảm biến nhưng không cho biết chính xác nó đi qua vào lúc nào giữa hai mẫu.
Thành phần A dành cho chuyển động trong lúc bản tin đang trễ.

Ví dụ A=H=0,020 s: B=0,0057 m; mẫu số 0,040 s; trần 0,1425 m/s. Với bước
chọn 0,01 m/s, làm tròn xuống thành **0,14 m/s**. Khi A=0,040 s, trần này xuống
khoảng 0,089 m/s, thấp hơn tốc độ nhỏ nhất 0,10 m/s đang được phép thử nên HOLD.

Không cộng toàn bộ bất định đã tích lũy trước neo thứ hai vào B: cạnh quang mới
sẽ neo lại vị trí theo quy tắc estimator hiện có. Bất định hiện tại vẫn phải
tham gia kiểm tra khoảng dừng ở phần tiếp theo và kiểm tra gắp thực tế.

**Giới hạn:** A và H là giá trị đã quan sát, không phải chặn trên chắc chắn của
độ trễ/khoảng mất mẫu trong tương lai. Guard mặc định bằng 0 không bổ sung bảo
đảm tương lai. Không dùng công thức này làm chứng nhận an toàn hoặc deadline.

### 2. Trần từ khoảng dừng còn lại

Dùng vị trí ước lượng tại nguồn, biên bất định tại nguồn, tích phân lệnh đã phát
từ nguồn tới hiện tại, dung sai đổi lệnh và lượng trôi dừng để tính khoảng còn
lại trước mép hỗ trợ cuối băng. Càng bất định hoặc đã di chuyển nhiều khi gói
trễ, khoảng còn lại càng nhỏ.

```text
v_stop = khoảng_còn_lại / [g_max × (chu_kỳ_điều_khiển + trễ_phản_ứng_mô_hình)]
```

Không thay phần chuyển động đã xảy ra bằng tốc độ mới thấp hơn. Không giảm
bất định hiện tại chỉ vì vừa hạ lệnh tốc độ. Predictor 1D sẵn có vẫn chạy sau
chính sách và vẫn có quyền HOLD theo các kịch bản của nó.

### 3. Ghép giới hạn và chốt trong chu trình

Lấy min của `v_pick`, `v_stop` và tốc độ lớn nhất trong dải thử. Làm tròn xuống
theo bước chọn; cap đã chốt không tăng lại trong chu trình. Lệnh cuối sau chính
sách là min của lệnh đang được yêu cầu và cap đã chốt.

- Không tự tăng tốc khi mạng vừa tốt trở lại.
- Lệnh dừng 0 hoặc lệnh chậm hơn cap được giữ nguyên.
- Nếu đang yêu cầu chuyển động mà cap thấp hơn dải thử: HOLD, không tự chạy
  xuống tốc độ chưa nằm trong dải cấu hình.
- Thiếu lịch sử cần thiết hoặc đầu vào không hợp lệ: HOLD.
- Kiểm tra stale, cảm biến, anchor, giới hạn gắp và trình tự vẫn giữ nguyên.
- Đổi tốc độ ở nhịp hiện tại không cứu được một bản tin pickup đã khiến
  controller HOLD trước khi chính sách được gọi.

## Tham số thay đổi được

Profile mới: `mujoco/configs/adaptive_cell_20261031.json`.

```json
"adaptive": {
  "enabled": true,
  "age_guard_s": 0.0,
  "pick_reserve_m": 0.0003,
  "speed_step_m_s": 0.01
}
```

Nhóm nằm trong `reconfiguration`. `degraded_long_speed_m_s` cũ vẫn dùng cho
đối chứng fixed; không phải trần bắt buộc của adaptive. CSV mới
`adaptive_parameters_to_fill_20261031.csv` có **205 trường số**, gồm thiết lập
thiết kế và các trường trước đó; không phải 205 đại lượng đã đo hoặc phải đo.
Không sửa profile trong một chu trình đang chạy.

## Chạy và đọc kết quả

```powershell
Set-Location 'C:\Users\Admin\Documents\ChatGPT\plc'

# 9 lượt smoke: 3 tình huống × 3 chính sách, seed 0
.\scripts\docker_dt.ps1 -Mode adaptive-check -Plan adaptive_speed_smoke.json

# 117 lượt: 13 tình huống × 3 seed × 3 chính sách
.\scripts\docker_dt.ps1 -Mode adaptive-check
```

Budget predictor trong các kế hoạch này là **1 giây để kiểm tra chức năng**.
Các ca không chứng minh đáp ứng 20 ms. `demo` không truyền Config vẫn dùng
profile cap cố định. Muốn xem một chu trình riêng với adaptive:

```powershell
.\scripts\docker_dt.ps1 -Mode demo -Config adaptive_cell_20261031.json
```

Trong thư mục kết quả, mở `report.md`, `groups.csv`, `report.json`. Các chính sách:

- `disabled`: tắt tái cấu hình; vẫn có sequence, estimator và predictor.
- `enabled`: tái cấu hình cap cố định 0,12 m/s.
- `adaptive`: trần tốc độ từ tuổi dữ liệu và biên ước lượng.

`report.json/pairs` ghi `policy`, `reference_policy`, trạng thái mỗi bên và chỉ
tính chênh lệch chu kỳ khi cả hai DONE. Đây là dạng cặp tổng quát mới, thay các
trường đặt tên riêng cho so sánh enabled/disabled của driver trước.

Log `reconfiguration.jsonl` bổ sung: `observed_age_high_s`, `observed_gap_high_s`,
`latched_cap_m_s`, và nhóm `adaptive` có hai trần, ngân sách và khoảng dừng còn
lại. `selected_long_speed_m_s` là lệnh sau chính sách; supervisor sau đó vẫn
có thể HOLD. Đọc `issued_commands.json` để biết lệnh cuối thực sự đã phát.

## Kết quả phát triển và quyết định hiện tại

Docker candidate cũng đã kiểm tra lại: **74 ca logic, 117 lượt ma trận, 9 lượt
adaptive smoke, 6 lượt robustness smoke cũ và 15 ca hồi quy cap cố định đều đạt
tiêu chí tương ứng**. Demo mặc định đặt phôi đạt; strict HOLD đúng lý do. Hai
kiểm tra biên đóng gói trên host đạt. Các kết quả đếm và thời gian bên dưới cũng
được lặp lại trong container; không chỉ là kết quả chạy phát triển.

Image: `sha256:f6e7e1a8cd3cb9c1910cb6687a7be66fdc1a01742c9afb33c07487cc3d6654e7`.
Nguồn, hash và log: `docker/evidence/candidate-20261031-adaptive-speed.json`.
Báo cáo ma trận:
`output/docker/adaptive-check_20261030T174012Z_5eee95a4/report.md`.
Tên lượt chạy dùng UTC, ngày tài liệu dùng Asia/Saigon. Chưa có nghiệm thu cá
nhân của người dùng cho candidate này; các image trước vẫn nguyên vẹn.

Lượt `output/adaptive_dev_20261031_a` hoàn tất 117/117 lượt đạt tiêu chí mô phỏng:
DONE/đặt phôi đúng hoặc HOLD/được hỗ trợ, cap và nhật ký. Điều này không có nghĩa
117 lượt đều hoàn tất sản xuất.

| Chính sách | DONE | HOLD |
|---|---:|---:|
| Disabled | 16 | 23 |
| Cap cố định | 19 | 20 |
| Adaptive | 15 | 24 |

Ở fixture trễ 20 ms, fixed hoàn tất trong 14,60 s còn adaptive trong 14,26 s,
nhanh hơn **0,34 s mô phỏng**. Nhưng ở jitter/mất mẫu, A/H xấu nhất được giữ
suốt chu trình làm cap xuống dưới 0,10 m/s và tăng số HOLD. Do đó **chưa chọn
adaptive làm mặc định**; không tuyên bố cải thiện năng suất hoặc độ tin cậy chung.

Một kiểm tra đơn vị ban đầu kỳ vọng giữ chính xác 0,14 m/s sau bản tin mới đã
báo FAIL: bản tin mới tuy có tuổi 0 nhưng bộc lộ khoảng lấy mẫu nguồn 40 ms nên
cap hạ xuống 0,10 m/s là đúng quy tắc. Kiểm tra được sửa để xác nhận không tăng
tốc, cho phép hạ thêm khi khoảng lấy mẫu xấu đi; không nới công thức vì lỗi test.

Để tiến tiếp cần xác định mô hình dự báo tuổi/khoảng mẫu có kiểm chứng và đánh
giá trade-off giữa số HOLD, sai số và thời gian hoàn tất trên tập seed/điều kiện
khác. Không thay guard hoặc ngưỡng gắp chỉ để thắng ma trận đang xem. Chưa có
reset HOLD tự động, feedback XY/vacuum thật, đa phôi, ML/RL hoặc đồng bộ CAD V5
toàn bộ trong hạng mục này.
