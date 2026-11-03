# Tiến độ lõi Digital Twin — cập nhật 31/10/2026

**Muốn đọc ít thuật ngữ hơn:** [báo cáo tiến độ dễ hiểu](bao_cao_tien_do_de_hieu.md).

## Bổ sung: gửi yêu cầu đặt lại và bắt đầu một lượt mô phỏng mới

- Đã tách yêu cầu đặt lại, xác nhận và lệnh bắt đầu thành ba bước. Mỗi bước
  kiểm tra mã phiên, mã yêu cầu, số lần khởi tạo và bộ thông số.
- Chặn gửi nhầm, gửi lặp, xác nhận cũ/quá hạn và thiếu xác nhận của người kiểm tra.
  Không có xác nhận đến thì vẫn kiểm tra thời gian chờ để chuyển sang bị chặn.
- Có phép thử nối toàn bộ quy trình với hai cảnh MuJoCo: cảnh cũ giữ nguyên ở
  HOLD (dừng chờ), cảnh mới chỉ chạy sau đúng trình tự. Không tiếp tục phôi cũ.
- Bộ thử tách 15 tình huống bản tin khỏi hai lượt mô phỏng chuyển động. Các xác
  nhận của người kiểm tra là giả lập, chưa phải phản hồi từ PLC thật.

[Hướng dẫn dễ hiểu và chức năng từng phần](dat_lai_chu_trinh_moi.md).
Docker đã kiểm tra lại: 88 phép kiểm tra chương trình, 15 tình huống bản tin và
hai lượt mô phỏng chuyển động trong phép thử đặt lại đều đạt yêu cầu tương ứng.
Các bộ kiểm tra cũ đạt; 78 nhật ký điều khiển giữ nguyên. Bản thử mới vẫn chờ
người dùng kiểm nghiệm, chưa được tự coi là đã nghiệm thu.

## Bổ sung: phân loại HOLD và đánh giá điều kiện xem xét khôi phục

- Ghi `hold_context` ngay lần HOLD đầu: công đoạn, thời gian, lý do, ước lượng
  và lệnh trước dừng; không ghi đè bằng dữ liệu tốt về sau.
- Thêm `RecoveryAssessment` chỉ đọc, chuỗi mẫu hậu HOLD, trạng thái chờ dữ liệu/
  can thiệp thủ công/operator review, blockers và checklist. Mọi trạng thái đều
  không cấp quyền restart; controller vẫn HOLD.
- Thêm fixture outage có thời điểm phục hồi và bộ 10 ca MuJoCo để kiểm tra rằng
  telemetry trở lại không tự chạy máy. Profile/CSV review có 205 trường số riêng.
- Lượt phát triển qua 10/10 ca; mất telemetry ngắn có thể sang OPERATOR_REVIEW,
  thiếu cảm biến hoặc thiếu feedback chuyển động vẫn yêu cầu can thiệp thủ công.

[Chức năng, giới hạn và cách thử](hold_recovery.md). Chưa có reset/request-ack,
tái đồng bộ phôi/XY thật hoặc tự resume; đây là bước đánh giá trước khôi phục.
Docker đã qua 82 kiểm tra logic, 10 ca review, 78 ca robustness, 9 adaptive smoke
và 15 ca fixed. Không có restart; 78 nhật ký controller trùng hash bản trước.
Candidate hold-review vẫn chờ kiểm nghiệm; chưa đổi bản accepted.

## Bổ sung: cap thích nghi theo tuổi dữ liệu và bất định

- Thêm `speed_policy.py`: trần từ ngân sách bắt cạnh/gắp và trần từ vị trí,
  bất định hiện tại, lịch sử lệnh, khoảng dừng còn lại.
- Tích hợp ở chế độ thử nghiệm riêng; chốt cap chỉ giảm, giữ nguyên các kiểm tra
  gắp/HOLD và chân không. Không đọc vị trí thật hoặc biết trước fault/mạng.
- Thêm profile/CSV 205 trường số và kế hoạch 117 lượt so ba chính sách; log giải
  thích ngân sách và từng trần. Cấu hình demo mặc định vẫn là cap cố định.
- Lượt phát triển: disabled 16 DONE/23 HOLD, fixed 19/20, adaptive 15/24. Adaptive
  nhanh hơn fixed 0,34 s trong ca trễ 20 ms, nhưng HOLD nhiều hơn khi jitter/mất mẫu.
  Chưa có bằng chứng để thay chính sách mặc định.

[Công thức, tác dụng, tham số và cách kiểm tra](adaptive_speed.md).
Docker xác nhận lại cùng kết quả: 74 ca logic, 117 lượt ma trận, 9 adaptive smoke,
6 robustness smoke và 15 ca hồi quy fixed đều đạt tiêu chí. Demo vẫn dùng fixed;
candidate adaptive-speed chờ kiểm nghiệm, chưa thay accepted. Các kiểm tra gắp,
estimator và plant giữ nguyên hash nguồn; không nới giới hạn để làm số DONE tăng.

## Bổ sung ngày 31/10: ma trận kiểm chứng và báo cáo tái lập

- Thêm công cụ ghép cặp bật/tắt chính sách theo 13 scenario, 3 seed: 78 lượt;
  có plan kiểm tra nhanh 6 lượt. Tham số plant/mạng thay bằng JSON, không sửa lõi.
- Tổng hợp riêng DONE, HOLD, exception, vi phạm cap, hỗ trợ phôi và sai số trong
  biên ước lượng. Không tính thời gian HOLD vào trung bình chu kỳ hoàn tất.
- Tự sinh Markdown/CSV/JSON và giữ cấu hình/hash/log từng ca để thành viên đọc,
  kiểm tra lại, so sánh trước và sau khi thay thuật toán.
- Giữ cả kết quả jitter bất lợi; không tuyên bố chính sách giảm tốc luôn tốt
  hơn hoặc các seed là các thử nghiệm độc lập. Budget chức năng 1 s được ghi rõ.

Chi tiết chức năng, cách chạy và giới hạn: [ma trận kiểm chứng](robustness.md).
Ma trận đầy đủ trong Docker: 78/78 đạt tiêu chí hỗ trợ/đặt phôi và cap; tắt chính
sách có 16 DONE/23 HOLD, bật có 19 DONE/20 HOLD. Jitter vẫn có ca bất lợi khi bật.
Đây là đếm trên fixture được chọn, không phải tỷ lệ thành công máy thật.
Docker candidate mới cũng qua 68 kiểm tra logic, 6 lượt smoke, 15 ca hồi quy
tái cấu hình, demo và strict; hash lõi điều khiển không đổi. Bản mới vẫn chờ
người dùng kiểm nghiệm. Chi tiết image/hash trong [sổ Docker](../docker/RELEASES.md).
Các bảng ngày 30/10 bên dưới mô tả nền tảng đã có trước hạng mục này.

## Trạng thái hiện tại và chức năng đã làm

Đây là chỉ mục tiến độ của dự án. Các phần mô tả ngày 27/10 ở phía dưới là lịch
sử baseline, không thay thế trạng thái hiện tại trong bảng này.

| Hạng mục đã triển khai | Chức năng / tác dụng | Trạng thái và hướng dẫn |
|---|---|---|
| Tín hiệu và replay | Phân biệt false, unavailable, stale; ghi số thứ tự và thời điểm để kiểm tra dữ liệu. | Có kiểm tra logic; xem phần lịch sử bên dưới. |
| Máy trạng thái và ước lượng | Gắp thả một phôi theo tín hiệu/ước lượng, timeout và HOLD có lý do. | [Trình tự](dt_estimator_sequence.md); XY/A2 giữa hành trình/chân không chưa có phản hồi xác nhận thật. |
| Cấu hình và nhập số đo | Gom thông số vào JSON, nhập CSV có đơn vị/nguồn gốc, tạo mô hình riêng mỗi lượt. | [Lõi mô-đun](modular_twin.md); chưa tự chứng nhận hiệu chuẩn. |
| Plant tham số hóa | Áp kích thước bao đã báo, phôi 60 mm, ba vai trò cảm biến quang, hai băng tải và gắp thả hữu hạn lực. | [Tham số/cơ học](parameterized_core.md); chưa đồng bộ đầy đủ CAD V5 và động lực học. |
| Mạng giả lập | Thử trễ, jitter, mất bản tin và thứ tự nhận có seed. | Chỉ chung đồng hồ mô phỏng; chưa phải mạng PLC thật. |
| Predictor và supervisor | So sánh CONTINUE/HOLD bằng các kịch bản dừng 1D, dừng khi tính quá hạn. | [Dự báo](predictive_core.md); chưa rollout MuJoCo toàn hệ thống. |
| Lịch sử lệnh và observer | Ước lượng được khi đổi tốc độ hoặc dừng/chạy lại, không đọc vị trí thật để điều khiển. | [Observer](observer_health.md); gain và biên bất định chưa hiệu chuẩn. |
| Theo dõi sức khỏe tín hiệu | Ghi dấu hiệu thiếu cạnh, kẹt mức cao nghi ngờ, mâu thuẫn và gián đoạn telemetry. | Phân biệt dấu hiệu nghi ngờ với nguyên nhân lỗi đã xác định. |
| **Tái cấu hình phần mềm mới** | NORMAL → DEGRADED để giới hạn tốc độ khi mạng xấu; HOLD khi không đủ thông tin. | [Quy tắc, tham số, log và cách thử](reconfiguration.md); chưa tự bỏ qua cảm biến hoặc reset HOLD. |
| Docker và bằng chứng | Candidate riêng từng hạng mục, snapshot/hash nguồn, cấu hình hiệu lực, log và image cũ để đối chiếu. | [Docker](docker.md), [sổ phiên bản](../docker/RELEASES.md); chỉ core-v1 đã accepted. |

### Nội dung cập nhật trong đợt tái cấu hình

- Thêm `reconfiguration.py`, tích hợp vào thứ tự phát lệnh và thêm log
  `reconfiguration.jsonl`: biết chính sách đổi chế độ lúc nào, dựa trên dấu hiệu
  gì và đã giới hạn lệnh bao nhiêu.
- Thêm profile riêng và CSV 202 trường số, gồm thiết lập thiết kế; tham số chưa
  đo vẫn để trống và không sửa cố định trong thuật toán.
- Thêm kiểm tra latch, không tăng tốc khi có cap, không mất lệnh hút khi HOLD,
  không tự restart sau gói tốt, và 15 kịch bản đối chứng MuJoCo.
- Giữ các profile/image trước. Câu “tiếp tục đi” là cho phép phát triển, không
  thay cho việc người dùng đã trực tiếp kiểm nghiệm một candidate.

### Kết quả kiểm tra của đợt tái cấu hình ngày 30/10

Kiểm tra Docker của hạng mục mới: **63 ca logic, 15 ca tái cấu hình, 13 ca observer,
18 ca plant tham số với budget chức năng 1 s và 10 ca dự báo legacy đều đạt**.
Hai kiểm tra biên đóng gói trên host cũng đạt. Demo mặc định đặt phôi thành công;
strict HOLD đúng vì chưa có đủ xác nhận. Hồ sơ và hash nằm trong
[sổ Docker](../docker/RELEASES.md). Các ca runtime 20 ms hoàn tất trong lượt này
không xóa giới hạn deadline đã ghi nhận ở candidate observer trước.

### Những giới hạn vẫn còn

Chưa kiểm chứng máy thật; chưa đồng bộ đồng hồ PLC; chưa có feedback thật cho
XY/A2 trung gian/vacuum; chưa phục hồi HOLD tự động, cảm biến thay thế hay ML/RL.
Giới hạn thời gian thực 20 ms chưa được bảo đảm trên host hiện tại. Các ca chức
năng dùng budget 1 s phải được phân biệt với ca kiểm tra runtime 20 ms.

## Lưu trữ: nền tảng ngày 27/10/2026

**Cập nhật mới nhất:** [kiến trúc mô-đun và nhập số đo](modular_twin.md).
Đã có profile JSON, mô hình riêng theo profile và mô-đun mạng giả lập;
các mục dưới mô tả nền tảng tín hiệu và baseline trước bước mở rộng này.

Đã hoàn thành bước A4 của lộ trình: tạo lớp tín hiệu cảm biến, dấu thời gian,
chất lượng dữ liệu, ghi cạnh đổi trạng thái và phát lại dữ liệu. Đây là nền
tảng để xây bộ ước lượng và bộ điều khiển theo trạng thái ở bước tiếp theo.

## Đã có những gì?

| Thành phần | Tệp | Vai trò |
|---|---|---|
| Hợp đồng tín hiệu | `mujoco/signals.py` | Snapshot, số thứ tự, thời gian lấy/nhận mẫu, miền đồng hồ và chất lượng từng tín hiệu. |
| Mô hình cảm biến | `mujoco/sensor_model.py` | Tạo hai tín hiệu quang và bốn công tắc cuối hành trình từ trạng thái plant, phát hiện cạnh lên/xuống. |
| Ghi và phát lại | `mujoco/record_signals.py` | Ghi riêng đầu vào cảm biến và đáp án mô phỏng; phát lại không cần cài MuJoCo. |
| Kiểm tra | `mujoco/test_signals.py` | Năm kiểm tra về cách ly dữ liệu, hành trình, độ cũ, dữ liệu không hợp lệ và phát lại. |

`run_cell.py` chỉ được bổ sung callback quan sát trong chu trình. Thuật toán
commissioning, vị trí đích, vận tốc và tiêu chí gắp không thay đổi.

## Hợp đồng dữ liệu

Mỗi snapshot có `sequence`, `source_time_s`, `received_time_s`, `source`,
`clock_domain`, `values` và `quality`. Nguồn là `simulated_io`; cả hai thời
gian đều dùng giây mô phỏng trong miền `simulation`. Hiện thời gian nhận
bằng thời gian lấy mẫu; chưa mô phỏng truyền mạng hay đồng bộ đồng hồ thực.

| Tên tín hiệu | Ý nghĩa | Nguồn/trạng thái hiện tại |
|---|---|---|
| `ps1`, `ps2` | Phát hiện phôi bằng cảm biến quang | Hai rangefinder của mô hình hiện có, chuyển thành nhị phân. |
| `a1_retracted`, `a1_extended` | A1 thu/ra hết | So vị trí khớp với hai giới hạn đọc từ MJCF: 0 và 0,110 m. |
| `a2_retracted`, `a2_extended` | A2 trên/dưới hết | So với 0 và 0,075 m; không coi vị trí hạ 0,060 m là hết hành trình. |
| `home_x`, `home_y1`, `home_y2` | Công tắc home | `null/unavailable`; cần xác nhận phần cứng và cách bố trí. |
| `vacuum_ok` | Xác nhận chân không | `null/unavailable`; lệnh bật hút không phải cảm biến. |
| `belt_speed_front_m_s`, `belt_speed_long_m_s` | Tốc độ băng tải đo được | `null/unavailable`; vận tốc ra lệnh không được coi là phép đo encoder. |

Dung sai công tắc đầu-cuối ban đầu là **2 mm**, có thể cấu hình, chưa hiệu
chuẩn với máy thật. Cửa sổ hai đầu không được chồng lên nhau. Các cảm biến
đang là mô hình lý tưởng; `good` biểu thị mẫu có giá trị trong mô hình này,
không chứng nhận cảm biến ngoài thực tế hoạt động đúng.

Phân biệt ba trường hợp:

- `false/good`: mẫu hợp lệ báo chưa tác động.
- `null/unavailable`: chưa có nguồn đo; không được hiểu là chưa tác động.
- `false/stale` hoặc `true/stale`: vẫn giữ giá trị cũ nhưng phải xét độ cũ.

`frame.aged(now_s, max_age_s)` đánh dấu `stale` khi tuổi tính từ **thời gian
lấy mẫu** vượt ngưỡng, kể cả khi gói tin vừa được nhận. Việc phát lại chỉ
kiểm tra thứ tự và tính số mẫu bị khuyết giữa các số thứ tự; chưa có bộ xử lý
gói tin đến sai thứ tự. Tuổi dữ liệu hiện chưa được dùng để điều khiển máy.

Đầu vào cảm biến không chứa vị trí phôi, vị trí trục liên tục, lệnh hút
hay tên công đoạn của bộ điều khiển. Những thông tin này nằm ở log đáp án
riêng. Bộ tạo cảm biến được phép đọc trạng thái plant ở bên trong ranh giới
mô phỏng; bộ ước lượng và bộ điều khiển tương lai chỉ nhận `SignalFrame`.

## Chạy thử từng bước trên máy này

Mở PowerShell và chạy từ thư mục gốc dự án:

```powershell
cd C:\Users\Admin\Documents\ChatGPT\plc
wsl -d Ubuntu-24.04 -- /home/admin/dt-cpps-venv/bin/python /mnt/c/Users/Admin/Documents/ChatGPT/plc/mujoco/record_signals.py --bin 1 --output /mnt/c/Users/Admin/Documents/ChatGPT/plc/output/dt_signals_lan2
```

Đợi dòng `PASS` và bảng tổng kết. Muốn xem chuyển động, thêm `--view`;
sau khi hoàn thành, đóng cửa sổ MuJoCo để chương trình ghi tổng kết cuối.
Mỗi lần chạy phải chọn một thư mục đầu ra **chưa tồn tại**. Chương trình
từ chối ghi đè để giữ dữ liệu cũ, kể cả dữ liệu một lượt chạy bị lỗi.

Thư mục kết quả gồm:

- `signals.jsonl`: mỗi dòng là một snapshot cảm biến.
- `edges.jsonl`: cạnh lên/xuống của các tín hiệu. Mẫu đầu chỉ xác lập trạng thái ban đầu, không tạo cạnh giả.
- `ground_truth.jsonl`: đáp án vật lý và nhãn công đoạn, ghép bằng `sequence`.
- `commissioning.csv`: log commissioning cũ, khoảng 0,1 s/mẫu.
- `summary.json`: tổng kết khi chu trình và phát lại đều thành công. Thiếu tệp này nghĩa là lượt chạy chưa hoàn tất thành công.

Phát lại dữ liệu đã tạo, không cần mô phỏng chạy lại:

```powershell
wsl -d Ubuntu-24.04 -- /home/admin/dt-cpps-venv/bin/python /mnt/c/Users/Admin/Documents/ChatGPT/plc/mujoco/record_signals.py --replay /mnt/c/Users/Admin/Documents/ChatGPT/plc/output/dt_signals_lan2/signals.jsonl
```

Chạy kiểm tra phần tín hiệu, không cần MuJoCo:

```bash
python mujoco/test_signals.py
```

Lệnh kiểm tra này đã được thêm vào workflow GitHub Actions hiện có; chưa
đẩy thay đổi lên GitHub hoặc xác nhận một lượt CI từ xa.

## Kết quả kiểm chứng lần đầu

Lượt chạy không giao diện trong WSL, MuJoCo 3.16.0, đích hộp 1:

| Chỉ số | Kết quả |
|---|---|
| Chu trình chuyển phôi, gắp và đặt hộp 1 | PASS theo tiêu chí commissioning hiện có. |
| Thời gian mô phỏng | 13,58 s. |
| Số snapshot cảm biến | 680, gồm một mẫu tại reset. |
| Khoảng lấy mẫu | 20 ms, tương ứng mỗi 10 bước vật lý 2 ms. |
| Cạnh đổi trạng thái | 10. |
| Khoảng khuyết số thứ tự khi phát lại | 0. |
| Kiểm tra tự động phần tín hiệu | 5/5 đạt. |

Dữ liệu nằm tại `output/dt_signals_bin1_20261027/`. Thời gian trên là **thời
gian mô phỏng**, không phải thời gian thực thi, độ trễ mạng hay độ trễ đồng
bộ Digital Twin. Kết quả một chu trình không chứng minh độ chính xác phát
hiện lỗi hoặc khả năng tăng năng suất.

Hai điểm phát hiện khi đọc log:

1. Chu trình cũ dừng đẩy khi A1 đạt khoảng **106,33 mm**, chưa tới cửa sổ
   công tắc cuối 108--112 mm theo dung sai ban đầu. Vì thế log không có cạnh
   `a1_extended=true`. Đây là hệ quả của điều kiện commissioning, không phải
   bằng chứng cảm biến hỏng.
2. A2 hạ đến đích **60 mm** trong hành trình **75 mm**, nên
   `a2_extended` cũng không tác động. Không sửa ngưỡng để tạo phản hồi giả.
   Cần thống nhất cơ khí, vị trí công tắc và tiêu chí điều khiển trước khi
   dùng tín hiệu dưới làm điều kiện chuyển bước.

## Cập nhật: đã có baseline ước lượng và trình tự

Xem [hướng dẫn và kết quả mới](dt_estimator_sequence.md). Đã bổ sung
ước lượng từ PS1/PS2 và máy trạng thái không dùng vị trí thật của phôi
để canh gắp. A1 chờ đúng công tắc cuối; A2 trung gian, XY và chân không
vẫn là giới hạn quan sát. Mặc định HOLD trước bước chưa xác nhận; chế độ
giả định vòng hở chỉ phục vụ thử trọn chu trình MuJoCo.

## Lộ trình sau lớp tín hiệu (trạng thái từng mục ở tài liệu mới)

1. Thống nhất tiêu chí hoàn thành chuyển động A1/A2, nhất là thao tác gắp
   tại hành trình giữa. Chưa đổi hành trình hay hình học chỉ để làm cảm biến báo đúng.
2. Xây bộ ước lượng phôi từ PS1/PS2 và mô hình vận chuyển; dùng dữ liệu chuẩn
   riêng để đánh giá sai số. Với vùng cấp vào A1 chưa có cảm biến riêng,
   phải công khai giả định một phôi có vị trí ban đầu đã biết.
3. Xây máy trạng thái dùng tín hiệu/ước lượng, có timeout và HOLD với lý do
   rõ ràng; không đọc trực tiếp vị trí thật của phôi. Phải xử lý được hạn chế
   quan sát tại vị trí A2 trung gian, không giả định đã có Vacuum_OK.
4. Sau khi baseline chạy được, bổ sung mô hình mạng, lỗi cảm biến, chẩn đoán,
   dự báo nhiều kịch bản và lựa chọn chính sách tái cấu hình phần mềm.

Đã có bộ ước lượng một phôi, máy trạng thái và ba trường hợp lỗi cảm biến
giả lập. Đã bổ sung mô phỏng trễ/mất mẫu trong bản mô-đun. Chưa có điều
khiển vòng kín hoàn toàn hoặc chẩn đoán nguyên nhân lỗi. Đã bổ sung
[dự báo nhiều kịch bản 1D](predictive_core.md); rollout tiếp xúc MuJoCo còn tiếp tục.

## Cập nhật 28/10/2026: chạy thí nghiệm từ giao diện

Đã nối DT Explorer với bộ chạy MuJoCo WSL, có tham số thí nghiệm, lưu lịch sử,
chạy cặp nền/dự báo và mở nhật ký mới trên sơ đồ. Xem
[hướng dẫn và kết quả nghiệm thu](live_experiments.md). Đây là thực thi lại
toàn bộ plant MuJoCo với cấu hình mới; predictor bên trong vẫn dùng mô hình
dừng 1D, chưa phải nhiều rollout tiếp xúc của plant.


## Bản tích hợp phần mềm số 1 — 31/10/2026

Đã ghép sáu mục trước khi kiểm tra chung. Xem [hướng dẫn](ban_tich_hop_phan_mem.md) và [nhật ký từng mục](nhat_ky_cong_viec.md). Trang theo dõi: `/tong_quan.html`. Chưa nghiệm thu máy thật.


## 02/11/2026 — Bộ đánh giá có đối chứng

Đã bổ sung phép đo hai nhánh dự báo, kế hoạch 24 lượt thử từng yếu tố và bảng thời gian trên trang tổng quan. Không đổi thuật toán điều khiển/giá trị đo. [Chức năng và cách chạy](danh_gia_co_doi_chung.md); [kết quả và giới hạn](bao_cao_danh_gia_20261102.md). Ảnh thử nghiệm mới chờ nghiệm thu.


## 03/11/2026 — Native rollout cho dự báo tiếp xúc

Giữ bản gốc, gom vòng lặp trong MuJoCo và cho nhập số luồng. Đã đối chiếu và chạy tích hợp trong Docker, chưa đạt 20 ms. [Hướng dẫn](toi_uu_du_bao_mujoco.md), [số liệu và giới hạn](bao_cao_toi_uu_20261103.md). Bài báo có bảng mới, phần vật lý giữ trống.
