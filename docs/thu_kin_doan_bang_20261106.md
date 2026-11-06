# Thử kín chọn tốc độ và dừng trong vùng — 2026-11-06

## Material Passport

- Origin Skill: Ponytail; nguyên tắc đối chứng và giới hạn bằng chứng ARS.
- Origin Date: 2026-11-06
- Verification Status: xem receipt Docker; chưa kiểm chứng vật lý.
- Version Label: closed_loop_segment_v1

## Điểm mới

Đây là thử kín: quyết định tốc độ thay đổi chuyển động MuJoCo và dữ liệu cảm
biến tiếp theo, không chỉ phát lại bản ghi. Bộ chọn không được đọc pose hoặc
hệ số thực của băng; pose chỉ vào bộ chấm. Vẫn chỉ là đoạn vận chuyển một phôi,
không phải toàn bộ dây chuyền gắp–thả hoặc điều khiển PLC thật.

## Kế hoạch và đối chứng

Có 144 lượt: hai tốc độ đặt 0,14/0,20 m/s × hai hệ số plant 0,9/1,1 × ba mức
trễ tín hiệu 0/40/80 ms × bình thường/PS3 không báo × ba chính sách × hai vùng dừng.
Lỗi PS3 bắt đầu sau cạnh xuống PS2 vật lý, không dùng vị trí thật làm mốc chèn.

- Tuần tự: tốc độ đặt, dừng khi nhận PS3, timeout danh định.
- Quy tắc thích nghi: giảm xuống tối đa 0,12 m/s khi tuổi dữ liệu từ 20 ms;
  dùng ước lượng điểm theo xung PS2 và tích phân lệnh để timeout đúng khi giảm tốc.
- Predictive DT: dùng cùng khung tín hiệu, xung và lịch sử lệnh, thử các tốc độ
  0,20/0,12/0,08 (không vượt tốc độ yêu cầu) bằng Predictor hiện có. Miền nguồn
  được đưa tới thời điểm hiện tại bằng tích phân lệnh trước khi dự báo, không
  giả định lệnh mới đã có hiệu lực trong khoảng trễ đã qua. Không có tốc độ được
  dự báo là phù hợp thì dừng. Đây là mô hình dừng 1D gần đúng, không chứng nhận an toàn.

Hai cửa sổ tâm phôi: hẹp 10–35 mm, rộng 0–60 mm theo trục dọc băng. Chúng là
**ràng buộc thí nghiệm giả định**, không phải dung sai gắp đã đo. Có cả hai từ
kế hoạch đầu để kiểm tra độ nhạy, không chọn lại vùng sau khi xem số liệu.
Các giá trị ban đầu/drift/guard/timeout đã dùng trong pilot được chuyển vào JSON
để sửa được; không đổi giá trị nhằm cải thiện kết quả.

Chỉ mô phỏng trễ đường tín hiệu về máy tính; lệnh tới băng có hiệu lực cục bộ
ngay. Không gọi đây là kiểm chứng trễ hai chiều hoặc PLC/mạng thực.

## Kết quả chính

| Vùng / chính sách | Bình thường: có PS3 và dừng trong vùng | Mất PS3: vượt mép trên | Mất PS3: thực tế dừng trong vùng (chưa xác nhận) |
|---|---:|---:|---:|
| Hẹp — tuần tự | 11/12 | 9/12 | 3/12 |
| Hẹp — quy tắc thích nghi | 12/12 | 12/12 | 0/12 |
| Hẹp — dự báo | 2/12 | 0/12 | 12/12 |
| Rộng — tuần tự | 12/12 | 6/12 | 6/12 |
| Rộng — quy tắc thích nghi | 12/12 | 12/12 | 0/12 |
| Rộng — dự báo | 12/12 | 0/12 | 12/12 |

Dự báo có ích cụ thể ở giới hạn vùng: không vượt mép trên ở 24 ca mất PS3,
so với 15/24 ca vượt ở tuần tự và 24/24 ở quy tắc đã chọn. Tuy nhiên độ bảo thủ
làm mất tiến độ: vùng hẹp chỉ 2/12 ca bình thường đủ xác nhận, dù phôi có thể
đã dừng trong vùng. Không diễn giải chỉ số không vượt biên riêng thành thành công.

Quy tắc thích nghi chờ lâu hơn khi thực sự chạy chậm, nên mất PS3 có thể đưa
phôi xa hơn trước timeout. Đây là hạn chế của quy tắc được chọn, không chứng
minh mọi PLC truyền thống đều kém: một quy tắc có mô hình biên cũng có thể cải thiện.

Tiêu chí finished bắt buộc đã nhận PS3. Vì vậy 0 lượt finished khi PS3 mất là
hệ quả của ràng buộc xác nhận đã đặt, **không phải bằng chứng không thể tiếp tục
bằng DT**. Cột dừng trong vùng chỉ bộ chấm MuJoCo biết, không được dùng ngược
để tự cho robot gắp. Muốn đo khả năng tiếp tục phải triển khai một điều kiện
xác nhận thay thế có giới hạn và kiểm chứng độc lập, thay vì bỏ tiêu chí này sau kết quả.

## Kiểm soát sai lệch triển khai

Pilot đầu có lỗi đối chứng: timeout thích nghi chưa tính tốc độ đã giảm. Đã
sửa thành tích phân lịch sử lệnh, thêm test giảm tốc và chạy pilot_v2 riêng.
Pilot đầu vẫn giữ, bị loại khỏi kết luận. Không sửa ngưỡng để che lỗi.

Ngân sách Predictor vẫn là 20 ms. Có log toàn bộ dự báo và số lần quá ngân
sách; quá hạn cũng đưa tới dừng. Thời gian tính không được bỏ khỏi quyết định.
Kết quả dừng thực tế vẫn cần đo/hiệu chuẩn lực, trễ và độ trôi ngoài mô phỏng.

## Kết luận và bước tiếp theo

Đã có bằng chứng thử kín về đánh đổi giữa giới hạn vị trí và khả năng tiến
hành công việc. Chưa có bằng chứng tăng năng suất toàn dây chuyền hoặc hồi phục
khi mất PS3, chưa có ML/PLC thật. Không gọi kết quả chặn rủi ro là tự tái cấu hình
để tiếp tục sản xuất đã hoàn thành.

Bước tiếp theo: định nghĩa chế độ xác nhận thay thế từ miền dự đoán sau dừng,
chỉ nhận khi toàn miền nằm trong vùng và các giả định vẫn còn hiệu lực; nếu
không đủ, cần nguồn quan sát độc lập. Phải đo báo hoàn thành sai và tiến độ,
so với quy tắc biên dùng cùng thông tin, giữ nguyên vùng thử và kiểm tra mới.

## Tệp và tái lập

- mujoco/study_closed_loop_segment.py: ba chính sách, ghép với Cell/Network/PulseObserver/Predictor có sẵn.
- mujoco/experiments/closed_loop_segment_20261106.json: tham số thử sửa được.
- mujoco/test_closed_loop_segment.py: timeout thích nghi đúng khi giảm tốc và từ chối ước lượng không dùng được.
- output/closed_loop_segment_20261106_pilot: pilot lỗi đối chứng, chỉ giữ truy vết.
- output/closed_loop_segment_20261106_pilot_v2: pilot đã sửa.
- output/docker/closed_loop_segment_20261106_final: bản Docker, xem receipt để biết số summary khớp pilot và số lần quá ngân sách.

```bash
python mujoco/study_closed_loop_segment.py --output output/closed_loop_new_run
```

Không ghi đè dữ liệu. Bản candidate-20261106-closed-loop chưa được người dùng nghiệm thu;
không đổi ảnh accepted, không đồng bộ giả CAD V5 với mô hình chức năng.
