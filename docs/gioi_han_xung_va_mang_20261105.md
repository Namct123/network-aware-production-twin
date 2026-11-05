# Khi nào không được tin ước lượng từ xung PS2?

## Material Passport

- Origin Skill: Ponytail; tiếp tục nguyên tắc đối chứng và nguồn bằng chứng ARS.
- Origin Date: 2026-11-05
- Verification Status: xem receipt Docker; chưa thử mạng/PLC thật.
- Version Label: pulse_network_replay_v1

## Thay đổi thực tế

PulseObserver nay tách rõ một bộ tham số đã từng suy ra với khả năng dùng nó để
kiểm tra hiện tại. Thêm `usable_for_monitoring`, `edge_history_complete`, thời
điểm nguồn của dự đoán và tuổi dữ liệu. **Có pulse_fit không có nghĩa được dùng
để tiếp tục điều khiển**. Các trường mới cũng không cấp quyền điều khiển PLC.

Nếu mất dữ liệu sau khi đã có xung, lịch sử cạnh bị chốt là không đầy đủ cho
chu kỳ đó; dữ liệu trở lại không tự xóa trạng thái này. Tạo phiên/bộ quan sát
cho chu kỳ mới mới bắt đầu lại. Nếu mất mẫu giữa xung, không fit từ xung bị đứt.
Phản hồi dự đoán nằm ở thời điểm nguồn, không được gắn nhãn vị trí hiện tại của
máy khi gói đến trễ.

## Phép thử

Dùng lại 28 bản ghi đoạn băng ở bước trước, chỉ đọc observations và issued_commands;
không đọc pose của MuJoCo để ra cảnh báo. Mỗi bản ghi có sáu lịch truyền:
ngay; trễ 40 ms; trễ 120 ms; mất mẫu nguồn 0,14–0,18 s giữa xung;
mất mẫu 1,00–1,06 s sau xung; ngắt từ 1,00 s trở đi. Tổng **168 phiên phát lại**,
không phải 168 lần chạy mới MuJoCo hoặc 168 thí nghiệm mạng UDP thật.

Nhịp nhận giữ đúng nhịp gốc; gói đuôi trễ chưa nhận khi hết bản ghi được đếm là
bị cắt cửa sổ, không tự thêm dữ liệu hoặc suy ra trạng thái vật lý. Kế hoạch
JSON và manifest lưu hash nguồn/đầu vào. Các thời điểm mất mẫu là lịch cố định,
không phải lỗi được phân loại bởi bộ quan sát.

## Kết quả

| Lịch truyền | Tình trạng xung trên 28 bản ghi | Kết luận cho bộ giám sát |
|---|---|---|
| Ngay | 28 có xung | Có thể dùng mô hình trong giả định đã đặt |
| Trễ 40 ms | 28 có xung | Kết quả phân loại như truyền ngay; dự đoán vẫn ở thời điểm nguồn |
| Trễ 120 ms | 28 không fit vì dữ liệu quá cũ | Cảnh báo vận chuyển, không chẩn đoán cảm biến hỏng |
| Mất mẫu giữa xung | 28 không có xung đầy đủ | Chưa có mô hình dùng được, không coi là hệ khỏe |
| Mất mẫu sau xung | 28 mất tính đầy đủ lịch sử | Không tự dùng lại chỉ vì gói mới quay về |
| Ngắt sau xung | 28 mất tính đầy đủ lịch sử | Không được tiếp tục dựa vào tham số cũ |

Ở truyền ngay và trễ 40 ms: mô hình riêng báo 8/16 ca lỗi; timeout thích nghi
cùng thông tin báo 16/16; bộ ghi kết hợp báo 16/16. Tám ca bổ sung là công của
**timeout**, không phải DT dự đoán tốt hơn. Tám ca bình thường và bốn ca thay
đổi gain không có cảnh báo mô hình/timeout ở hai lịch đó.

Ở mất mẫu sau xung/ngắt sau xung, các cảnh báo được ghi nguồn
`transport_or_edge_history_unusable`, không tính thành phát hiện PS3 hỏng.
Ở mất mẫu giữa xung, bộ ghi kết hợp không tự đưa ra báo lỗi linh kiện; trạng
thái vẫn là `pulse_unavailable`, tất cả dự đoán không đủ điều kiện sử dụng.
Không có cảnh báo không đồng nghĩa đã đủ thông tin để chạy.

Timeout chỉ kết luận thiếu cạnh khi dấu thời gian **nguồn đã nhận** đi qua
mốc cần chờ. Không lấy đồng hồ máy nhận vượt deadline để kết luận một sự kiện
chưa đến trong gói trễ là đã không xảy ra.

## Kết luận giới hạn

Đã sửa ranh giới sử dụng dữ liệu và tách nguồn cảnh báo; chưa chứng minh tăng
năng suất, tự khôi phục hoặc lợi thế so với bộ điều khiển thích nghi tốt.
Việc chốt từ chối sau mất cạnh là bảo thủ, có thể làm giảm tính sẵn sàng;
không gọi nó là tự tái cấu hình thành công. Mô hình xung và timeout vẫn dựa
vào kích thước/hình chiếu, tốc độ và độ trôi giả định, cần kiểm chứng vật lý.

Bước tiếp theo cần tập trung vào một chính sách thử kín có các cấu hình được
phép và dữ liệu quan sát đủ, đo đồng thời sản phẩm hoàn thành, thời gian dừng
và vi phạm ràng buộc. Không tiếp tục tối ưu chỉ riêng số ca báo lỗi hoặc thu
nhỏ khoảng sai số để cho máy chạy. Khi chưa có đủ phản hồi, hệ phải từ chối.

## Tệp và chạy lại

- `mujoco/pulse_observer.py`: sửa gốc, áp dụng cho các nơi dùng bộ xung.
- `mujoco/study_pulse_network.py`: phát lại lịch mạng và gắn nguồn cảnh báo.
- `mujoco/experiments/pulse_network_20261105.json`: sáu lịch cố định sửa được.
- `mujoco/test_pulse_network.py`, `test_pulse.py`: kiểm tra dữ liệu cũ, gãy xung,
  lịch sử đã mất và chặn lịch trễ âm có thể nhìn dữ liệu tương lai.

```bash
python mujoco/study_pulse_network.py --source output/docker/pulse_20261105_final --output output/pulse_network_new
```

Chỉ nhận bản ghi tốc độ lệnh dương cố định; không mở rộng kết luận sang đổi
lệnh/tốc độ trong đoạn này. Không ghi đè thư mục cũ. Pilot giữ riêng; bản cuối
ở output/docker/pulse_network_20261105_final; Docker candidate-20261105-pulse-network.
Các quyết định bản pulse trước có schema cũ và giữ nguyên, không viết lại bằng
chứng lịch sử sau khi thêm cờ hợp lệ mới.
