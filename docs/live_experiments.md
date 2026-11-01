# Bộ chạy thí nghiệm MuJoCo từ DT Explorer

Cập nhật 28/10/2026. Đây là mô đun thực thi thí nghiệm mô phỏng, chưa kết nối PLC.

## Mở và sử dụng

1. Dừng máy chủ Explorer cũ nếu đang chạy, bằng Ctrl+C trong cửa sổ máy chủ.
2. Mở `web/START_SIMULATION_EXPLORER.cmd`.
3. Truy cập http://127.0.0.1:8765/#experiments.
4. Chọn profile, tốc độ băng dọc 0,10–0,24 m/s, lỗi cảm biến, trễ, jitter, tỷ lệ mất gói, seed và hộp đích.
5. Giữ mặc định nghiêm ngặt để kiểm tra điều kiện thiếu phản hồi. Chỉ bật “Cho phép XY/A2/hút hở vòng trong mô phỏng” khi muốn thử chu kỳ với giả định này.
6. Chọn “Chạy cặp nền / dự báo” để thử cả hai chế độ. Khi đó ô bật supervisor cho một lượt riêng bị vô hiệu vì cặp luôn chứa cả nền và dự báo.
7. Bấm Chạy thí nghiệm. Trạng thái chỉ hiển thị lượt đang chạy, không tạo phần trăm tiến độ giả.
8. Khi hoàn tất, bấm Xem lượt baseline hoặc predictive để đưa nhật ký vừa tính lên sơ đồ, rồi phát/tua như trước. Các lượt DONE vẫn có thể đặt phôi không đạt; giao diện hiển thị đúng bộ đánh giá.

Môi trường trên máy hiện tại: WSL `Ubuntu-24.04`, Python
`/home/admin/dt-cpps-venv/bin/python`, MuJoCo **3.16.0** đã kiểm tra.
Để dùng môi trường khác, chạy từ thư mục gốc:

```powershell
python web/server.py --enable-experiments --wsl-distro Ubuntu-24.04 --simulation-python /home/admin/dt-cpps-venv/bin/python
```

Python Windows chỉ cần thư viện chuẩn để phục vụ web. Python WSL phải có MuJoCo và NumPy.
Script không tự cài môi trường hoặc tải gói. Nếu chỉ muốn xem dữ liệu cũ và phòng dự báo
1D thì tiếp tục dùng `web/START_EXPLORER.cmd`, không cần MuJoCo.

## Luồng mô đun

`Biểu mẫu → kiểm tra yêu cầu → hàng chạy một job → WSL worker → experiment.run → nhật ký → replay → giao diện`

- `web/experiments.py`: kiểm tra tham số, cấu hình các lượt, thực thi worker và so sánh kết quả.
- `web/server.py`: API tạo job, đọc trạng thái, lịch sử và lấy replay; giữ API dự báo 1D cũ.
- `web/build_replays.py`: dùng chung bộ đọc nhật ký cho 10 lượt cũ và các lượt vừa chạy.
- `mujoco/experiment.py`: lõi mô phỏng hiện có; không thay logic điều khiển để đáp ứng giao diện.

Mỗi job có ID riêng và thư mục `output/web_experiments/<id>/`, gồm:

| Tệp | Ý nghĩa |
|---|---|
| `request.json` | Các tham số yêu cầu ban đầu. |
| `job.json` | Trạng thái thực thi, thời điểm UTC, yêu cầu và kết quả. Giao diện đổi thời gian sang giờ Việt Nam. |
| `progress.json` | Lượt đang chạy; cập nhật bằng ghi tệp tạm rồi thay thế để tránh JSON dở dang. |
| `worker.log` | Chẩn đoán WSL/Python nếu quá trình lỗi. |
| `baseline/`, `predictive/` | Cấu hình hiệu lực, MJCF riêng, manifest, tín hiệu nguồn/nhận, điều khiển, dự báo và ground truth. |
| `*_replay.json` | Dữ liệu để vẽ, kèm hash các tệp nguồn và manifest lõi. |
| `result.json` | Kết quả các lượt và so sánh có giới hạn. |

Một job tại một thời điểm trong một máy chủ. Worker bị giới hạn **150 s thời gian thực**
cho toàn bộ yêu cầu; máy chủ chờ tối đa 170 s, bao gồm phần khởi động WSL. Đây khác với
giới hạn thời gian mô phỏng trong cấu hình. Nếu máy chủ khởi động lại, job dở dang được
đánh dấu gián đoạn; không tự coi các tệp một phần là kết quả hoàn tất.

## So sánh có điều kiện

Cặp thử giữ nguyên profile, seed, lỗi, tốc độ và giả định; chỉ thay cờ bật dự báo.
Lịch lấy mẫu và seed mạng giống nhau ở phần thời gian chung của hai lượt. Predictor
dùng ngân sách thời gian thực, nên kết quả deadline có thể khác khi tải CPU thay đổi.

- Chỉ báo chênh lệch chu kỳ khi **cả hai DONE và đặt phôi đạt**.
- Chỉ báo HOLD sớm cho cặp lý do `timeout:TRACK:ps2` và `predictive_stop_margin`.
- Các lỗi khác hoặc kết quả không tương đương được giữ nguyên, không đổi thành phần trăm tăng tốc.
- Trạng thái job `completed` chỉ nghĩa là đã tính xong; không đồng nghĩa máy đặt phôi đạt.

## Kiểm chứng ngày 28/10/2026

Bộ kiểm tra thực gọi API localhost, chạy worker WSL MuJoCo thật, đọc lại replay và đối
chiếu hash nhật ký cùng hash mã nguồn. Không dùng kết quả đã lưu để thay cho việc chạy.

| Ca | Kết quả |
|---|---|
| Cặp bình thường, hở vòng | Hai lượt DONE, đặt phôi đạt; cùng 15,46 s mô phỏng. Không có tăng tốc chu kỳ trong ca này. |
| Cặp PS2 kẹt thấp | Nền HOLD 6,76 s; dự báo HOLD 6,72 s; hai lượt giữ phôi được đỡ theo tiêu chí. |
| Một lượt nghiêm ngặt | HOLD 6,66 s vì chưa xác nhận XY/A2 trung gian/hút. |
| Cặp mất 100% gói | Hai lượt HOLD 0,10 s do watchdog; chưa có dữ liệu để dự báo. |

**4/4 ca nghiệm thu**, tổng **7 lượt mô phỏng**; thêm **8 kiểm tra tự động** cho giao diện/API,
đầu vào, cấu hình cặp, so sánh có điều kiện và vòng đời job. Ca PS2 cũng đã được chạy
trực tiếp bằng biểu mẫu trong trình duyệt. Chưa xác nhận GitHub Actions từ xa.

Kết quả kiểm chứng phiên bản cuối: `output/dt_web_acceptance_20261028_final/results.json`.

```powershell
python web/test_explorer.py
python web/test_experiments.py
python web/check_live_experiments.py --output output/my_new_web_acceptance
```

Lệnh cuối cần máy chủ đã bật bộ chạy, WSL/MuJoCo sẵn sàng và thư mục output chưa tồn tại.

## Giới hạn và bước kế tiếp

Chỉ thực hiện chu kỳ một phôi, có reset mô phỏng đã biết. Chèn lỗi kẹt thấp và mạng
được cấu hình trước lượt, chưa phải lỗi xuất hiện ở thời điểm bất kỳ. Dự báo vẫn là
mô hình dừng động học 1D; HOLD giữ chốt, chưa có phục hồi tự động. Không có lệnh phần cứng.

Nền tảng này cho phép bước tiếp theo đo có hệ thống: chạy nhiều seed và thời điểm lỗi,
phân biệt phát hiện bất thường với chẩn đoán nguyên nhân, rồi kiểm chứng chính sách
tái cấu hình. Các thông số máy thật vẫn phải đi qua mô đun hiệu chuẩn trước khi đưa
ra kết luận về năng suất, độ tin cậy hoặc an toàn.
