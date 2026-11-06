# Đối chứng thời gian nguồn và tuổi dữ liệu trên bộ điều kiện mới

## Câu hỏi và cách thử

Giữ nguyên bộ dự báo bù hằng số và miền sai số cũ. Tách hai yếu tố:

- So thời điểm sự kiện bằng thời gian phát mẫu ở máy, hoặc bằng thời gian nhận.
- Có kiểm tra tuổi dữ liệu tối đa100 ms, hoặc tắt riêng kiểm tra này.

Mọi phương án vẫn kiểm tra quality (chất lượng), lịch sử cạnh và miền mô hình.
Bộ dùng thời gian nhận cố ý bỏ qua timestamp nguồn sau dự báo để tách yếu tố;
nó không đại diện cho bộ PLC truyền thống được thiết kế tốt nhất. Cũng chưa
có kết nối điều khiển hoặc đo mạng thật.

Kế hoạch khóa ở Git5a39fe5 trước khi chạy: ba tốc độ0,135/0,175/0,215 m/s,
hai gain0,91/1,09 và hai vị trí đầu−255/−245 mm.12 điều kiện chưa dùng trong
lưới học cũ. Mỗi điều kiện có ca bình thường, mất PS3 và băng đứng, thành36
bản ghi. Năm kiểu truyền và bốn phương án tạo720 lượt phát lại, không phải720
thử nghiệm độc lập. Dữ liệu có24 cặp quan sát–lệnh khác nhau;12 cặp mất PS3/
băng đứng giống đầu vào. Giữ toàn bộ ca, không đổi mô hình hoặc ngưỡng theo kết quả.

## Kết quả chính cần đọc đủ mẫu số

Các hàng dưới đều có12 ca bình thường đã lên kế hoạch. Cột đủ đầu vào cho
biết bao nhiêu ca thực sự có thể dùng dự báo; không coi ca bị từ chối là khỏe.

| Trễ | Chặn tuổi | Đủ đầu vào /12 | Báo nhầm: thời gian nguồn | Báo nhầm: thời gian nhận |
|---|---|---:|---:|---:|
|0 ms|Có|6|2|2|
|40 ms|Có|6|2|3|
|80 ms|Có|6|2|5|
|120 ms|Có|0|0|0|
|120 ms|Không|6|2|5|

Sáu ca bắt đầu khi PS2 đã bị che nên không xác định được đầu xung. Bộ dự báo
đúng khi từ chối suy toàn bộ độ dài xung từ dữ liệu thiếu. Đây là giới hạn điều
kiện khởi đầu, không phải phát hiện sáu cảm biến hỏng.

Ngay cả không trễ, trong6 ca còn dùng được có2 ca bình thường bị báo bất thường.
**Miền hiệu chuẩn cũ đã không đạt mục tiêu0 ca báo nhầm đã đặt trước.** Không
công bố tỷ lệ báo nhầm2/12 như thể12 ca đều được đánh giá; trong phần có thể
đánh giá là2/6. Không nới biên sau khi xem kết quả rồi dùng lại bộ này để chứng
minh độ chính xác.

Với24 ca lỗi đã lên kế hoạch, ở0/40/80 ms hai loại đồng hồ đều báo12 ca, còn12
ca không có xung đầu vào đủ. Trong12 ca lỗi có thể đánh giá, dùng thời gian nhận
khi có trễ có thể báo thiếu cạnh trước khi mẫu nguồn mới nhất vượt hạn. Thời
gian nguồn tránh được lỗi diễn giải này, nhưng vẫn không sửa được lỗi hiệu chuẩn.

Khi trễ120 ms, chặn tuổi từ chối toàn bộ36 bản ghi ở mọi loại lỗi. Không còn
báo nhầm, nhưng cũng không có phát hiện lỗi từ mô hình. Mất một đoạn gói sau
xung làm lịch sử không đủ ở mọi phương án. Không gọi việc từ chối là độ chính
xác100% hoặc hệ thống đã phục hồi.

## Những gì kết quả này chứng minh và chưa chứng minh

- Trên phép so một yếu tố đồng hồ, dùng thời gian nguồn tránh các báo sai tăng
  thêm do trễ. Các dự báo/miền ở các phương án có đầu vào đều giống nhau.
- Chặn dữ liệu cũ là một ràng buộc sử dụng, có chi phí mất khả năng đánh giá.
- Giám sát vẫn phụ thuộc xung đầy đủ và hiệu chuẩn đúng điều kiện. Chưa đủ để
  cho DT ghi PLC, tự bỏ phản hồi, hoặc tiếp tục gắp khi mất xác nhận.
- Đây là lưới xác định nhỏ, một bệ thử ảo; không có bảo đảm xác suất, tốc độ phát
  hiện vật lý hoặc chuyển được ngay sang máy khác. Bộ này nay đã được xem.

## Việc cần làm tiếp

Rà mô hình thời điểm cạnh và phần không chắc chắn do lấy mẫu/điều kiện khởi đầu.
Tạo tập hiệu chuẩn khác bao phủ các yếu tố đó, rồi khóa lại trước một tập kiểm
tra chưa xem. Giữ kết quả không đạt hiện tại. Sau đó thêm một bộ nối sự kiện
khác; không chỉ đổi tên cảm biến rồi gọi là đã thử nhiều loại máy.

## Tái lập và trạng thái

```bash
IMG=production-twin-dt:candidate-20261106-network-clock
docker run --rm --network none --read-only -v "$PWD/output/docker:/app/output" "$IMG" mujoco/study_network_clock.py --output /app/output/clock_review
```

Tên đầu ra phải mới. Kết quả gốc: output/docker/network_clock_20261106_final.
Receipt: docker/evidence/candidate-20261106-network-clock.json.171 kiểm tra lõi
WSL và16 kiểm tra Docker tập trung đã đạt;72 hash đầu vào và720 log được xác
nhận. Candidate chưa được người dùng nghiệm thu; bản accepted không đổi.
