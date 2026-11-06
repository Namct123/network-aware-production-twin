# Điều kiện xác nhận thay thế khi PS3 không báo

## Material Passport

- Origin Skill: Ponytail; đối chứng và truy vết theo nguyên tắc ARS.
- Origin Date: 2026-11-06
- Version Label: model_confirmation_v2
- Verification Status: xem receipt Docker; chưa đo/hiệu chuẩn vật lý.

## Công việc và điều kiện

Thêm bộ đánh giá chỉ đọc, không cho PLC hoặc robot bỏ qua PS3. Để vị trí được
coi là phù hợp theo mô hình, phải đồng thời có xung dùng được, lịch sử cạnh
đầy đủ, lệnh dừng đã duy trì đủ 0,3 s, dữ liệu còn hợp lệ và toàn bộ khoảng vị
trí tại thời điểm đánh giá nằm trong cửa sổ cho phép. Tích phân các lệnh đã ra
và sai số độ trôi/đáp ứng/dừng đưa khoảng nguồn tới hiện tại; không đọc pose.

Hai mức được tách rõ:

- `conditional_position_ok`: khoảng phù hợp **trong các giả định của mô hình**.
- `release_eligible`: còn cần các điều kiện mô hình và chuyển động được kiểm
  chứng từ nguồn phù hợp. Trong bộ thử này luôn để chưa kiểm chứng; không lấy
  lệnh RUN hoặc gain chèn của MuJoCo để tạo bằng chứng giả.

Tham số sai số hiện chưa hiệu chuẩn vật lý; flag kiểm chứng là giao diện nội
bộ cho điều kiện bổ sung sau này, không phải bằng chứng đã có. Test với flag
True chỉ kiểm tra nhánh logic bằng dữ liệu tổng hợp.

## Thử thách thêm vào phép thử kín

72 lượt dùng tốc độ đặt 0,16 m/s, gain 0,9/1,1, trễ 0/80 ms, ba tình huống
(bình thường, PS3 không báo, băng dọc mất chuyển động sau PS2), ba chính sách
và hai vùng hẹp/rộng giữ nguyên từ bước trước. Chỉ thêm mất chuyển động vào
plant: lệnh bộ điều khiển và lệnh thực áp dụng được tách riêng. Không thay vùng
hoặc thu nhỏ sai số để làm điều kiện xác nhận đạt.

Mỗi cặp PS3 không báo/băng đứng được so toàn bộ khung quan sát và quyết định;
chỉ bỏ trường thời gian tính khi so logic, vẫn giữ trạng thái vượt deadline.

## Kết quả đúng sau kiểm tra biên

- **24/24 cặp** cùng quan sát và quyết định logic, nhưng vị trí cuối khác nhau
  khoảng **191–271 mm**. Cùng lệnh, cùng mô hình không tự phân biệt được hai
  chuyển động thật này. Đây là phản ví dụ trên mô phỏng, không suy thành tỷ lệ
  chẩn đoán chung cho mọi lỗi.
- **0/72** khoảng sau dừng nằm trọn trong vùng, tất cả từ chối với
  `interval_outside_zone`. Chưa có ca nào đủ điều kiện xác nhận thay thế.
- Số xác nhận sai là 0 vì **không phát hành xác nhận nào**; không được gọi đó
  là độ chính xác 100% hoặc tính an toàn đã chứng minh.
- Không thay điều kiện finished của bộ điều khiển cũ và không cấp lệnh cho
  robot/PLC từ kết quả chấm. Đây là kiểm tra đủ điều kiện, chưa phải chính sách
  hồi phục được kích hoạt.

## Lỗi phát hiện và sửa trước kết luận

Bộ kiểm tra ban đầu dùng max_speed của CommandHistory trên khoảng từ thời điểm
ra lệnh dừng. Giá trị này có cả tốc độ bên trái biên, ngay trước lệnh dừng,
nên đã từ chối cả 72 ca với stop_not_maintained. Đây là lỗi bộ chấm, không phải
kết quả nghiên cứu. Đã sửa phép kiểm tra thành quãng lệnh thực trong khoảng và
lệnh cuối; thêm test từng chạy rồi dừng đúng biên, đồng thời vẫn từ chối chạy
lại trong thời gian chờ. Không sửa CommandHistory chung vì các nơi khác cần
biết thay đổi tốc độ ở biên để lượng hóa đáp ứng.

Pilot/audit và ảnh candidate đầu được giữ riêng. Sau sửa, 72 ca vẫn từ chối,
nhưng vì khoảng ngoài vùng — lý do đúng. Hai kết luận phải được phân biệt,
không dùng kết quả ban đầu để củng cố kết luận sau sửa.

## Kết luận thực dụng

Chưa được bật chế độ gắp tiếp chỉ từ mô hình xung hiện tại. Thu hẹp khoảng bằng
tay có thể làm gate nhận, nhưng không tạo thêm thông tin và không giải quyết
phản ví dụ băng đứng. Cần nguồn quan sát độc lập hoặc điều kiện chuyển động
thực được kiểm chứng, rồi mới đánh giá cấu hình tiếp tục.

Bước tiếp theo nên mô phỏng một nguồn quan sát bổ sung có nhiễu, trễ và mất
mẫu (ví dụ đo vị trí phôi), so các phương pháp với cùng nguồn đó, sau đó mới
chọn cơ chế triển khai camera/feedback thật. Không giả định camera hiện đã lắp,
không đưa pose MuJoCo trực tiếp vào DT mà gọi là dữ liệu đo thực.

## Mã và tái lập

- model_confirmation.py: kiểm tra khoảng và tiền điều kiện; test_model_confirmation.py kiểm tra dừng đúng biên, khoảng và flag.
- study_closed_loop_segment.py: thêm drive_stall ở phía plant; các ca cũ giữ hành vi.
- study_confirmation.py: khôi phục bộ quan sát theo từng nhịp, chỉ dùng mốc dừng đã thấy trong log; pose chỉ chấm sau quyết định.
- experiments/confirmation_20261106.json: kế hoạch nhập sửa được.

```bash
python mujoco/study_closed_loop_segment.py --plan mujoco/experiments/confirmation_20261106.json --output output/confirmation_new
python mujoco/study_confirmation.py --source output/confirmation_new --output output/confirmation_new_audit.json
```

Không ghi đè thư mục cũ. Bản đúng dùng candidate-20261106-confirmation-v2,
output/docker/confirmation_20261106_final_v2 và confirmation_20261106_audit_v2.json.
Các tệp không hậu tố v2 là pilot kiểm tra, không lấy làm bằng chứng gate đã đúng.
Các thay đổi chưa được người dùng nghiệm thu; ảnh accepted và CAD vẫn giữ nguyên.
