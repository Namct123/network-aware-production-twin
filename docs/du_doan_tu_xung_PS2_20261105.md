# Ước lượng theo xung PS2 — đối chứng cùng thông tin

## Material Passport

- Origin Skill: Ponytail + academic-research-suite (Codex adapter 3.23.2).
- Upstream: https://github.com/Imbad0202/academic-research-skills ; manifest cục bộ ghi commit 863e1c754f0e97062d271dcb42a9483c9ef34aa9. Không cài trùng hoặc giả định bản đã cài là HEAD hiện tại.
- Origin Mode: nghiên cứu thực nghiệm theo ủy quyền tiếp tục của người dùng; không viết/hoàn tất bài báo ở mục này.
- Origin Date: 2026-11-05
- Verification Status: xem receipt Docker; chưa kiểm chứng vật lý.
- Version Label: pulse_observer_v1

## Câu hỏi và giả thuyết

Thời gian phôi che PS2 có thể giúp suy tốc độ của từng chu kỳ trước khi dự đoán PS3, thay cho một miền hệ số chung không? Kỳ vọng là khoảng dự đoán hẹp hơn và vẫn bao phủ chuyển động. Không mặc định việc này làm phát hiện nhanh hơn hoặc tăng năng suất.

Tái sử dụng EventResidual, CommandHistory và simulate; thêm PulseObserver rất nhỏ. Không thêm thư viện, mô hình học sâu, giao diện hoặc kiến trúc mới.

## Phương pháp và ranh giới dữ liệu

- Với phôi dài L, dùng khoảng thời gian cạnh lên → cạnh xuống PS2 và quãng lệnh tích phân D để ước lượng hệ số đáp ứng L/D. Miền hệ số tính thêm sai số chiều dài/chiếu quang ±4 mm và một chu kỳ lấy mẫu cho sai lệch độ rộng xung. Độ trôi vẫn 0,005 m/s; đây là giả định chưa hiệu chuẩn vật lý.
- Chỉ chốt từ một xung đầy đủ, chất lượng tốt, thứ tự/thời gian liên tục. Mất gói, xung bị đứt hoặc xung không phân giải được thì không fit, không tự lấy vị trí thật thay thế.
- Chốt tham số trước khi quan sát PS3; không dùng PS3 để fit rồi kiểm tra ngược PS3. Không nhận gain thật, pose hoặc nhãn lỗi vào bộ quan sát.
- Đối chứng gồm miền chung đã hiệu chuẩn ở bước trước, timeout danh định và timeout thích nghi dùng cùng ước lượng điểm từ xung PS2 + 0,2 s. Chỉ so với timeout danh định sẽ thiên vị lợi ích của thông tin mới.
- Kế hoạch khóa trước khi sinh dữ liệu mới: 8 ca bình thường (tốc độ 0,13/0,19, gain 0,90/1,10, ma sát 0,9/1,3), 16 ca PS3 mất tín hiệu/mất chuyển động sau PS2, 4 ca gain 0,77/1,23 ngoài miền hiệu chuẩn cũ. Không sửa tham số sau kết quả.
- Các giá trị là điều kiện bệ thử MuJoCo, không phải số đo máy thật. Bệ thử chỉ chạy đoạn băng, không phải chu trình gắp–thả hay bộ điều khiển PLC.

## Kết quả

| Phương án | Báo trong 8 ca bình thường | Báo trong 16 ca lỗi | Bao phủ mẫu bình thường | Độ rộng khoảng trung bình |
|---|---:|---:|---:|---:|
| Miền chung đã hiệu chuẩn | 0/8 | 16/16 | 786/786 | 77,4 mm |
| Miền theo xung PS2 | 0/8 | 8/16 | 786/786 | 52,6 mm |
| Timeout thích nghi theo cùng xung | 0/8 | 16/16 | Không có khoảng | Không áp dụng |

Khoảng theo xung hẹp hơn khoảng chung **32,0%** trên tám điều kiện bình thường này. Trên bốn ca thay đổi gain, miền theo xung bao phủ 388/388 mẫu, miền chung 381/388; cả hai không báo. Đây là khả năng thích nghi tham số trên lưới mô phỏng, không phải xác suất hoặc độ chính xác chẩn đoán.

Nhưng miền theo xung chỉ báo tám ca lỗi gain 1,10. Với tám ca gain 0,90, cận dưới bảo thủ chưa vượt mốc trước lúc cửa sổ thử kết thúc; ghi là chưa báo trong cửa sổ, không giả định sẽ không bao giờ báo. Trong tám ca đã báo, nó chậm hơn timeout có cùng thông tin **60–120 ms**. Không kéo dài cửa sổ hoặc thu nhỏ sai số sau khi thấy kết quả để đổi điểm số.

## Ý nghĩa nghiên cứu

Đã có cải thiện đo được về độ rộng và bao phủ ngoài miền cũ, nhưng có suy giảm phát hiện trong cửa sổ. Phương án không trội hơn đối chứng. Không dùng mức giảm 32% để tuyên bố tăng năng suất, hoặc cho PLC bỏ PS3 và tiếp tục gắp: khoảng 52,6 mm trung bình vẫn quá rộng để mặc định đủ chính xác.

Hai nguyên nhân mất tín hiệu PS3 và mất chuyển động sau PS2 vẫn có thể cùng quan sát; xung trước đó không chứng minh băng còn chuyển động sau mốc. Việc thêm AI không tự giải quyết thiếu quan sát này.

## Việc tiếp theo

Kiểm tra biến thiên hình chiếu/phôi, xung lỗi, đổi tốc độ và suy giảm mạng để xác định khi nào ước lượng xung được dùng hoặc phải từ chối. Sau đó mới đánh giá kết hợp khoảng dự báo với điều kiện timeout/hợp lệ thành chính sách vận hành có giới hạn. Không cho bộ mới quyền điều khiển chỉ vì khoảng hẹp hơn.

## Tái lập

- mujoco/pulse_observer.py: bộ ước lượng; test_pulse.py kiểm tra công thức, xung đầy đủ và xung bị đứt.
- mujoco/experiments/pulse_20261105.json: kế hoạch sửa được.
- mujoco/study_pulse.py: dùng lại simulator có sẵn, lưu tín hiệu/lệnh/pose chấm riêng và từng quyết định.
- Bản pilot: output/pulse_20261105_pilot; bản Docker cuối: output/docker/pulse_20261105_final. Không ghi đè dữ liệu.
- Báo cáo này không phải bài báo đã xuất bản. Chưa có bộ ML chẩn đoán huấn luyện hoặc kết quả vật lý.

```bash
python mujoco/study_pulse.py --calibration output/docker/interval_calibration_20261105_final/sealed_calibration.json --output output/pulse_new_run
python -m unittest discover -s mujoco -p test_pulse.py -v
```
