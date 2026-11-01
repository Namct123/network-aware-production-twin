# Dự báo nhiều kịch bản 1D và giám sát theo ngân sách tính toán

Ngày 27/10/2026. Đây là bước tiếp theo của lõi mô phỏng, không phải bài báo
và chưa phải bản Digital Twin vật lý đã hiệu chuẩn.

## Phần vừa bổ sung

- `mujoco/predictor.py`: chạy các quỹ đạo phản thực từ vị trí, vận tốc,
  khoảng sai số và thời điểm nguồn của bộ ước lượng. Không nhận plant,
  vị trí thật của phôi hoặc nhãn lỗi được chèn.
- `mujoco/supervisor.py`: chọn tiếp tục một tick hoặc HOLD dựa trên biên
  dừng xấu nhất; ghi lý do, số kịch bản, thời gian tính và deadline miss.
- `mujoco/check_prediction.py`: so sánh baseline và predictive với cùng
  cấu hình máy, có ca mất PS2, trễ, mất toàn bộ mẫu, giới hạn quan sát và
  ngân sách tính toán cố tình quá nhỏ.
- `mujoco/test_prediction.py`: kiểm tra công thức, deadline, dữ liệu không
  hợp lệ và ranh giới không đọc đáp án. Các kiểm tra chạy bằng thư viện chuẩn.

`experiment.py` đã nối supervisor trước khi áp lệnh. Lệnh vận tốc đưa
vào estimator nay được ghép theo **sequence nguồn** của mẫu trễ, không dùng
nhầm lệnh mới hơn cho khoảng thời gian đã xảy ra. Đây là lịch sử lệnh đã
phát, không phải vận tốc thật/encoder hoặc vị trí phôi được đọc lén.

## Dự báo gì và không dự báo gì?

Mô hình hiện chỉ dự báo dọc băng tải trong TRACK, sau ít nhất một mốc quang.
Nó dùng động học 1D với vận tốc hằng và quãng trôi dừng giả định, không
gọi một bản sao MuJoCo để giải tiếp xúc trong từng kịch bản. Chưa dự báo
tụt áp, tuột giác hút, va chạm robot hoặc tự tạo lại chu trình gắp.

Hai chính sách ứng viên:

1. **HOLD**: ra lệnh dừng ngay, có thời gian phản ứng giả định rồi quãng trôi.
2. **CONTINUE**: chạy thêm đúng một chu kỳ điều khiển rồi dừng trong quỹ
   đạo dự báo. Trên máy mô phỏng, chỉ thi hành hành động đầu tiên rồi tính
   lại ở tick tiếp theo; không phát trước cả chuỗi lệnh.

Nếu mọi kịch bản của CONTINUE giữ được biên mô hình thì tiếp tục; nếu không,
chọn HOLD. Nếu ngay HOLD cũng vượt biên, ghi rõ không còn phương án tiếp
tục được chấp nhận theo mô hình. HOLD khi đó không phải bảo đảm giữ được
phôi ngoài thực tế.

## Cấu hình và ý nghĩa của 54 kịch bản

Nhóm `prediction` nằm trong profile JSON; mặc định tắt để giữ baseline.
`mujoco/configs/predictive_demo.json` bật chế độ này cho mô phỏng.

| Thông số mặc định | Giá trị |
|---|---|
| Khoảng dự báo | 0,50 s |
| Bước quỹ đạo 1D | 0,020 s |
| Ngân sách wall-clock mỗi lần tính | 0,020 s |
| Vị trí ban đầu | Ước lượng trừ khoảng sai số; ở giữa; cộng khoảng sai số |
| Sai lệch vận tốc | -0,020; 0; +0,020 m/s |
| Thời gian phản ứng dừng bổ sung | 0; 0,010; 0,020 s |
| Biên bổ sung so với mép đỡ phôi | 0 m, chưa hiệu chuẩn |

3 mức vị trí × 3 mức vận tốc × 3 mức phản ứng × 2 chính sách = **54**
tổ hợp tham số/hành động mỗi lần tính. Không phải 54 kiểu lỗi độc lập.
Mỗi quỹ đạo có 26 điểm, kể cả điểm ban đầu: 1.404 điểm trạng thái 1D/lần.

Gọi a là tuổi ước lượng, b là khoảng sai số, dv là sai lệch vận tốc và
o thuộc {-1,0,+1}. Mô hình dùng:

```text
v = max(0, v_hat + dv)
y0 = y_hat + o * (b + drift_rate * a) + v * a
cutoff = reaction_delay + (0 nếu HOLD, một tick nếu CONTINUE)
y(t) = y0 + v * min(t, cutoff) + phần quãng trôi dừng
margin = mép băng - nửa chiều dài phôi - stop_margin - y(t)
```

Phần quãng trôi tăng từ 0 đến giá trị cấu hình trong một bước dự báo sau
cutoff. Đây là mô hình thay thế đơn giản, không phải mô hình phanh/ma sát
đã nhận dạng. Khoảng sai số cũng là cận kỹ thuật, chưa là khoảng tin cậy
xác suất. Không có chứng minh an toàn hoặc ổn định cho mọi tình huống.

Nếu hết ngân sách trước khi xét đủ kịch bản, kết quả chưa hoàn tất không
được dùng để chọn tiếp tục. Supervisor chọn HOLD và ghi
`prediction_deadline_exceeded`. Ước lượng không hợp lệ cũng gây HOLD có
lý do; số NaN không được ghi thành một phép đo JSON hợp lệ.

Chỉ phần tính predictor được đo bằng wall-clock; không bao gồm MuJoCo,
mạng, logging và lịch chạy hệ điều hành. Ngân sách này chưa là bảo đảm
thời gian thực cho toàn hệ thống. Trường hợp thử deadline dùng 1 ns có
chủ đích để kiểm tra đường fallback, không phải một mục tiêu hiệu năng.

## Chạy trong PowerShell

```powershell
cd C:\Users\Admin\Documents\ChatGPT\plc
$py = "/home/admin/dt-cpps-venv/bin/python"
$root = "/mnt/c/Users/Admin/Documents/ChatGPT/plc"
$cfg = "$root/mujoco/configs/predictive_demo.json"
wsl -d Ubuntu-24.04 -- $py "$root/mujoco/run_twin.py" --config $cfg --assume-open-loop --view --output "$root/output/predictive_view01"
```

`--assume-open-loop` vẫn chỉ cho phép các giả định XY/A2/chân không của
mô phỏng. Bỏ cờ đó thì chặn giới hạn quan sát vẫn có hiệu lực; predictor
không được phép bỏ qua nó. Mỗi lượt chọn thư mục đầu ra mới.

Chạy so sánh tự động:

```powershell
wsl -d Ubuntu-24.04 -- $py -u "$root/mujoco/check_prediction.py" --output "$root/output/predictive_checks01"
```

Đọc `prediction.jsonl`: mỗi lần tính ghi hành động, lý do, biên xấu nhất
của từng chính sách, số kịch bản hoàn tất và `compute_ms`. `summary.json`
có nhóm `prediction`; `comparison.json` của bộ so sánh ghi chênh thời điểm
HOLD. `effective_config.json` và manifest vẫn lưu cấu hình/mã thực dùng.

Các profile cũ thiếu nhóm prediction được nâng khi nạp với chế độ dự báo
**tắt**; không tự bật thuật toán mới lên bản thông số cũ. Cấu hình mới kiểm
tra khoảng dự báo phải đủ bao trùm tick và dừng, có cả hai cực trị vị trí,
và có giới hạn tĩnh số kịch bản/bước để tránh tải tính toán vô hạn.

## Cách đọc kết quả hiện tại

Ca PS2 kẹt thấp đã cho HOLD ở 6,72 s với supervisor, so với 6,76 s ở
baseline: sớm hơn **0,040 s mô phỏng trong đúng ca ghép này**. Phôi còn
được đỡ sau đoạn kiểm tra dừng. Đây không phải thời gian chẩn đoán từ lúc
cảm biến hỏng, không phải độ chính xác phát hiện lỗi tổng quát và chưa
phải bằng chứng tăng năng suất.

Mất toàn bộ dữ liệu từ đầu chưa có mốc để dự báo; watchdog dừng và số lần
predictor được gọi bằng 0. Mất PS2 vẫn dẫn tới HOLD, chưa chuyển sang gắp
tiếp bằng cảm biến ảo. Không tự phục hồi hoặc thay tốc độ giữa hai mốc vì
bộ ước lượng hiện yêu cầu lệnh vận tốc không đổi trong đoạn đó.

Các ca ở 0,10; 0,16; 0,24 m/s đã được thử riêng. Điều này không bảo đảm
mọi tốc độ trung gian, mọi lịch mất gói hoặc mọi giá trị sai số đều hoàn
thành. Cần hiệu chuẩn mô hình, đo báo sai/bỏ sót và chạy nhiều lịch nhiễu.

## Công việc còn lại sau mô-đun này

Rollout tiếp xúc MuJoCo độc lập từ trạng thái có thể quan sát; xác nhận
XY/giác hút; giám sát nguyên nhân lỗi; lựa chọn các chính sách phục hồi
phong phú hơn; đồng bộ với PLC thật và kiểm chứng bằng số đo vật lý vẫn
chưa hoàn tất. Không dùng kết quả 1D để tuyên bố mô hình robot/khí nén đã
được dự báo đầy đủ.
