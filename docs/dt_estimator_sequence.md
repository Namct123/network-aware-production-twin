# Bộ ước lượng và máy trạng thái - 27/10/2026

**Bản mở rộng hiện tại:** [cấu hình mô-đun, số đo và mạng giả lập](modular_twin.md).
Các giá trị số dưới đây là baseline mặc định, nay được đọc từ profile JSON.

Đã bổ sung baseline một phôi trong MuJoCo. Chưa nối PLC hay máy thật.
Không thay đổi hình học hoặc công tắc để tạo phản hồi giả.

## Thành phần

| Tệp | Chức năng |
|---|---|
| `mujoco/estimator.py` | Ước lượng vị trí dọc băng tải từ các cạnh lên PS1/PS2. |
| `mujoco/sequence.py` | Máy trạng thái nhận `SignalFrame`, không nhận plant hoặc vị trí thật của phôi. |
| `mujoco/run_twin.py` | Nối plant, cảm biến, điều khiển và evaluator; ghi ba log độc lập. |
| `mujoco/test_sequence.py` | Chín kiểm tra không cần cài MuJoCo. |
| `mujoco/check_twin.py` | Bộ nghiệm thu 12 lượt với MuJoCo, lưu bằng chứng từng lượt. |

Commissioning cũ vẫn nằm trong `run_cell.py`. Thêm `Cell.hold()` để dừng
băng tải và giữ các điểm đặt ramp đã phát, đồng thời giữ lệnh hút hiện tại.
Đây là hành vi giữ trong mô phỏng, không phải chức năng dừng an toàn đã được chứng nhận.

## Hai chế độ

**Mặc định:** sau khi cấp, đẩy, thu A1 và theo dõi bằng hai cảm biến quang,
chuyển HOLD trước khi canh gắp vì chưa có phản hồi XY, xác nhận A2 ở hành
trình giữa và Vacuum_OK. Đây là chặn có chủ đích, không phải lỗi cài đặt.

**`--assume-open-loop`: chỉ dùng để thử mô phỏng.** Cho phép dùng thời gian
chuyển động XY/A2 suy ra từ lệnh và khoảng chờ ổn định, đồng thời cho phép
tiếp tục sau lệnh hút chưa được xác nhận. Có thể thử toàn bộ chu trình;
`DONE` chỉ là hoàn thành trình tự giả định. Kết quả đặt phôi phải xem riêng
ở `placement_pass_evaluator_only`.

Các giả định được ghi trong từng tổng kết:

- Một phôi tại vị trí reset đã biết; cấp vào A1 theo thời gian. Chưa xử lý
  phôi đến ngẫu nhiên, trượt băng tải đầu hoặc xác nhận home thực.
- Phôi dài 22 mm, làn chạy ngang cố định; chiều dọc băng tải là +Y.
- Tốc độ băng tải dài không đổi giữa hai mốc. Thử 0,10--0,24 m/s; băng
  tải đầu giữ 0,16 m/s. Chưa đo vận tốc bằng encoder.
- MuJoCo dùng cơ cấu chấp hành vị trí. Đặt đích A2 = 60 mm trong mô phỏng
  không chứng minh van khí nén 5/2 thực có thể dừng tại hành trình giữa.

## Cách ước lượng

PS1 nằm ở Y = -0,065 m, PS2 ở Y = 0,170 m, cách nhau 0,235 m trong mô hình.

```text
v_hat = 0,235 / (t_PS2 - t_PS1)
y_center_at_edge = y_sensor - 0,011 + v_hat * sample_interval / 2
y_hat_next = y_hat + v_hat * elapsed_time
```

Cạnh lên phát hiện mặt trước phôi, nên phải trừ nửa chiều dài để ước lượng
tâm. Nửa khoảng lấy mẫu bù xấp xỉ pha vượt tia chưa biết. Trước PS2, dùng
vận tốc đặt làm tiên nghiệm. Sau dừng, thêm một lần quãng trôi thử 2 mm.
Không đọc vị trí thật để hiệu chỉnh trực tuyến.

Khoảng sai số kỹ thuật khởi tạo bằng 2 mm cộng phần lấy mẫu, tăng 20 mm/s
khi ngoại suy chuyển động và tăng thêm theo quãng trôi khi dừng. Đây không
phải khoảng tin cậy thống kê hoặc cận an toàn đã chứng minh. Tại PS2, chỉ
canh gắp khi khoảng sai số cộng phần trôi không vượt 10 mm.

PS2 thiếu PS1, cạnh đồng thời không hợp lệ, PS1 bị lặp, tốc độ suy ra ngoài
phạm vi thử hoặc thay lệnh tốc độ giữa hai mốc đều bị từ chối. Mẫu cũ hay
unavailable không tạo cạnh mới; tín hiệu đã true ngay khi bắt đầu quan sát
không được mặc định là một cạnh lên.

## Trình tự và giới hạn chờ

`INIT → FEED → PUSH → RETRACT → TRACK → ALIGN → LOWER → GRIP → LIFT → MOVE → LOWER_BIN → RELEASE → RAISE → RETURN → DONE`.

A1 chờ công tắc cuối hành trình 110 mm, sau đó thu về theo công tắc.
LIFT/RAISE cũng chờ công tắc A2 trên. Mỗi bước này chờ tối đa 2 s.
Hạ A2 60 mm chờ 0,75 s theo mô hình; không coi công tắc dưới 75 mm đã tác động.
GRIP chờ 0,25 s, RELEASE chờ 0,40 s. XY dùng thời gian từ quãng đường lệnh,
vận tốc 0,12 m/s và khoảng chờ 0,30 s, chỉ ở chế độ giả định vòng hở.

TRACK chờ tối đa `min(6 s, 0,44 m / tốc độ đặt)`. Giới hạn quãng đường này
thay cho timeout cố định 6 s vốn có thể dừng quá muộn. Nó chỉ phù hợp với
vị trí chuyển phôi và tốc độ trong cấu hình thử, không bảo đảm đúng khi
trượt mạnh hoặc đổi hình học.

Mẫu cũ quá 100 ms, khoảng lấy mẫu lớn hơn 61 ms, mẫu sai thứ tự, tín hiệu
bắt buộc unavailable hoặc các công tắc đầu-cuối mâu thuẫn đều đưa vào HOLD.
HOLD không tự phục hồi và không tự tắt hút khi có thể đang giữ tải.

## Chạy từng bước trong PowerShell

1. Mở dự án và thử chế độ mặc định. Kết quả mong đợi là HOLD do thiếu
   phản hồi chuyển động, sau khi đã ghép hai mốc quang:

```powershell
cd C:\Users\Admin\Documents\ChatGPT\plc
wsl -d Ubuntu-24.04 -- /home/admin/dt-cpps-venv/bin/python /mnt/c/Users/Admin/Documents/ChatGPT/plc/mujoco/run_twin.py --output /mnt/c/Users/Admin/Documents/ChatGPT/plc/output/twin_strict_lan1
```

2. Thử toàn chu trình trong mô phỏng:

```powershell
wsl -d Ubuntu-24.04 -- /home/admin/dt-cpps-venv/bin/python /mnt/c/Users/Admin/Documents/ChatGPT/plc/mujoco/run_twin.py --assume-open-loop --bin 1 --output /mnt/c/Users/Admin/Documents/ChatGPT/plc/output/twin_hop1_lan1 --view
```

Cửa sổ tự chạy; đóng sau khi xong để nhận tổng kết. Kiểm tra `DONE` và
`placement_pass_evaluator_only: true`. Đổi `--bin` thành 1--6; thêm
`--speed 0.10` hoặc `--speed 0.24` để thử tốc độ khác. Mỗi lần chọn một
thư mục đầu ra mới; chương trình từ chối ghi đè dữ liệu.

3. Thử thiếu phản hồi PS2:

```powershell
wsl -d Ubuntu-24.04 -- /home/admin/dt-cpps-venv/bin/python /mnt/c/Users/Admin/Documents/ChatGPT/plc/mujoco/run_twin.py --assume-open-loop --fault ps2_stuck_low --output /mnt/c/Users/Admin/Documents/ChatGPT/plc/output/twin_loi_ps2_lan1
```

Lỗi khác: `ps1_stuck_low`, `a1_extended_stuck_low`. Mẫu vẫn báo `good`,
giống lỗi kẹt mức mà đường truyền chưa biết. Controller không nhận nhãn lỗi.
Timeout hoặc thiếu cạnh chưa đủ để phân biệt chắc chắn hỏng cảm biến với
kẹt phôi/lỗi cơ cấu; chưa có bộ chẩn đoán nguyên nhân.

4. Chạy toàn bộ nghiệm thu:

```powershell
wsl -d Ubuntu-24.04 -- /home/admin/dt-cpps-venv/bin/python -u /mnt/c/Users/Admin/Documents/ChatGPT/plc/mujoco/check_twin.py --output /mnt/c/Users/Admin/Documents/ChatGPT/plc/output/twin_nghiemthu_lan1
```

Kiểm tra logic không cần MuJoCo: `python mujoco/test_signals.py` và
`python mujoco/test_sequence.py`. Cả hai lệnh đã có trong workflow CI;
chưa đẩy thay đổi hay xác nhận một lượt GitHub Actions từ xa.

## Kết quả đo trong MuJoCo 3.16.0

Bộ cuối cùng: `output/dt_acceptance_20261027_v2/results.json`.

| Nhóm | Kết quả |
|---|---|
| Sáu hộp, băng tải dài 0,16 m/s | 6/6 đặt đúng; chu trình 15,46 hoặc 17,38 s mô phỏng. |
| Hộp 1 ở 0,10 và 0,24 m/s | 2/2 đặt đúng; lần lượt 17,02 và 14,60 s mô phỏng. |
| Chế độ mặc định | HOLD ở 6,66 s do phản hồi chưa xác nhận. |
| PS1 kẹt thấp | HOLD ở 6,66 s, `ps2_without_ps1`. |
| PS2 kẹt thấp | HOLD ở 6,76 s, `timeout:TRACK:ps2`. |
| A1 cuối hành trình kẹt thấp | HOLD ở 4,38 s, `timeout:PUSH:a1_extended`. |
| Phôi sau HOLD | Cả 4 lượt còn được đỡ trên băng sau ít nhất 0,30 s ổn định. |
| Kiểm tra tự động | 14 kiểm tra logic và 12/12 lượt nghiệm thu đạt. |

Ở các lượt không lỗi, RMSE dọc Y là 0,73--0,91 mm; sai số tuyệt đối lớn
nhất khoảng 1,52 mm trong đoạn đã đánh giá. Tốc độ suy ra ở cấu hình
0,16 m/s là khoảng 0,1588 m/s. Chỉ đo sau PS1 trong TRACK/ALIGN, không phải
sai số XYZ toàn chu trình hoặc độ chính xác trên máy thật.

Mỗi lượt ghi `signals.jsonl`, `controller.jsonl`, `ground_truth.jsonl`
và `summary.json`, ghép bằng `sequence`. File đáp án chỉ dành cho evaluator.
Bộ nghiệm thu kiểm tra cả trạng thái/lý do HOLD và vị trí phôi sau dừng;
không coi nhãn HOLD đơn thuần là đã giữ được phôi. Thời điểm HOLD khác
thời gian mô phỏng kết thúc vì có thêm đoạn kiểm tra ổn định.

Đây là các lượt xác định, không phải thống kê độ tin cậy. Không tuyên bố
đã tăng năng suất, phát hiện mọi lỗi hoặc đạt tự tái cấu hình hoàn chỉnh.

## Tiếp theo

Hiệu chuẩn thông số và làm rõ phản hồi XY/A2/chân không. Trễ/mất mẫu đã
được bổ sung ở bản mô-đun; phát hiện bất thường có phần dư và so sánh chính sách còn tiếp tục. Bản
mô phỏng dự báo tiếp xúc MuJoCo độc lập còn tiếp tục. Đã có
[predictor 1D và chọn CONTINUE/HOLD theo ngân sách](predictive_core.md).
