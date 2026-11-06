# Phạm vi tập trung: phương pháp giám sát sự kiện cho hệ sản xuất

## Material Passport

- Origin Skill: academic-research-suite, experiment-agent (plan), scientific-writing.
- Origin Mode: thu hẹp câu hỏi từ kết quả có sẵn và yêu cầu trực tiếp của người dùng.
- Origin Date: 2026-11-06.
- Verification Status: phạm vi phương pháp đã triển khai; kết quả chỉ từ một bệ thử ảo.
- Version Label: event_monitoring_focus_v1.

## Dự án này giờ nghiên cứu điều gì?

**Khi nào có thể dùng dự báo của DT để nhận ra tiến độ máy không bình thường,
và khi nào phải thừa nhận rằng tín hiệu đang không đủ để kết luận?** Câu hỏi
phụ: thêm ML có giúp báo bất thường tốt hơn một cách bù sai lệch đơn giản không?

Đây là phương pháp dành cho hệ sản xuất có sự kiện quan sát được. Dây chuyền
hiện tại là bệ kiểm thử, không phải giới hạn tên đề tài. Ví dụ ánh xạ:

| Khái niệm của phương pháp | Bệ băng tải đã thử | Ví dụ có thể xây bộ nối sau |
|---|---|---|
| Mốc bắt đầu có bằng chứng | Kết thúc xung PS2 | Bắt đầu hành trình được xác nhận |
| Sự kiện cần đến | Cạnh PS3 | Xi lanh tới cuối hành trình, trục tới vị trí |
| Bộ dự báo | Công thức xung, bù hằng số, Ridge | Mô hình thời gian hành trình/quỹ đạo |
| Dữ liệu hợp lệ | Mẫu mới, đủ lịch sử, quality tốt | Quy tắc tương ứng với thiết bị đó |
| Kết luận | Không khớp, nhất quán với miền, hoặc chưa đủ dữ liệu | Cùng ý nghĩa, không tự suy nguyên nhân |

Những ví dụ xi lanh/trục trên chưa được thử như thiết bị thứ hai. Đổi tên sự
kiện trong kiểm tra phần mềm không phải bằng chứng tổng quát hóa giữa các máy.

## Vì sao đây là hướng khả thi hơn?

| Hướng | Bằng chứng hiện có | Quyết định |
|---|---|---|
| Giám sát có xét tuổi/lịch sử dữ liệu | Có lõi chạy được, đối chứng và log | Trọng tâm bài |
| ML luôn tốt hơn quy tắc | Không; báo lỗi còn muộn hơn bù hằng | Giữ như phép so, không hứa thắng |
| Tự phục hồi cả dây chuyền khi mất cảm biến | Chưa; có cặp lỗi cùng quan sát | Để giai đoạn sau |
| Tăng tốc dự báo vật lý toàn mô hình 3D | Nhánh cũ chưa đạt hạn đã đặt | Không mở rộng trong bài này |

Đây là lựa chọn về khả năng hoàn thành một nghiên cứu rõ ràng, không phải bảo
đảm hội nghị nhận bài. Các vấn đề chất lượng dữ liệu/độ tin cậy DT đã được nghiên
cứu; không thể gọi việc kiểm tra timestamp là phát minh mới. Điểm cần làm tốt
là cách ghép các điều kiện sử dụng dự báo với phép so có cùng thông tin, các chỉ
số quyết định và giới hạn quan sát, rồi kiểm chứng trên dữ liệu chưa xem.

## Cấu trúc giữ lại

1. Lõi dùng chung event_window.py: nhận miền thời gian và bằng chứng sự kiện;
   không biết tên băng tải, vị trí giác hút, PLC hay MuJoCo.
2. Bộ nối và các predictor (bộ dự báo) thay thế được: eta_monitor.py hiện là
   bộ nối cho xung quang. Bù hằng số là đối chứng chính; Ridge là nhánh so sánh.
3. Bệ kiểm thử MuJoCo và các bản ghi: cung cấp quan sát cho lõi, giữ vị trí thật
   và nhãn lỗi ở phía chấm kết quả.
4. Bài báo, bằng chứng, hướng dẫn và gói Docker tập trung.

research_scope.json chốt danh sách 35 tệp đưa vào runtime tập trung. Các nhánh
điều khiển toàn chu trình, CAD, giao diện, dự báo toàn mô hình và dữ liệu lịch sử
vẫn giữ trong kho đầy đủ; không đưa vào gói Docker này. Giữ lõi DT, profile thay
đổi được và bản accepted. Không xóa bằng chứng thất bại hoặc sửa lại lịch sử.

## Những gì đã có để viết

- 61 đoạn bình thường, tách32/8/8/9/4; các trùng lặp được công bố.
- 31 bản ghi giám sát,465 lượt phát lại; không gọi là465 thử nghiệm độc lập.
- ML15,4 ms so với bù hằng18,1 ms trên9 ca, nhưng báo bằng hoặc muộn20–40 ms.
- Chín cặp mất PS3/băng đứng có cùng đầu vào, nên không tự xác định nguyên nhân.
- Lõi tổng quát đã tách;13 kiểm tra trong Docker tập trung;168 kiểm tra lõi
  đầy đủ ở WSL. Toàn bộ465 nhật ký quyết định được tái lập đúng sau khi tách.

Bài mới có tên: **A Network-Aware Predictive Digital Twin Framework for
Event-Based Production Monitoring**. Title/abstract vẫn ở file riêng. Phần
kiểm chứng vật lý trống. Bản dài trước khi thu hẹp nằm trong lịch sử Git tại
commit7bbde4a; không dùng nó làm bản thảo hiện hành song song.

## Ba việc tiếp theo, theo thứ tự

1. **Đóng băng bộ thử mới trước khi chạy**: thay đổi có ý nghĩa như pha lấy mẫu,
   điều kiện khởi động và biến thiên động học; tách calibration/test theo điều
   kiện hoặc phiên, không nhân bản các bản ghi xác định. Không chọn ca chỉ vì
   biết trước ML sẽ tốt hơn.
2. **Tách lợi ích của nhận thức mạng**: so bộ dùng source timestamp với một bộ
   không xét tuổi dữ liệu được định nghĩa rõ, cùng bộ dự báo, cùng tín hiệu và
   cùng tiêu chí báo nhầm. Ghi số lần từ chối, báo nhầm, thiếu cửa sổ quan sát,
   độ trễ báo và chi phí tính. Bước này chưa có kết quả, không viết như đã làm.
3. **Thêm một bộ nối sự kiện khác**, ưu tiên công tắc cuối hành trình xi lanh
   trên chính bệ hiện có. Sau đó mới đo vật lý theo kế hoạch riêng. Một bộ nối
   thứ hai vẫn không chứng minh đúng cho mọi loại dây chuyền.

Điều kiện để kết luận tích cực là có lợi ích đo được ở đúng mục tiêu, kể cả
khi ML không thắng. Nếu chỉ giữ được tính minh bạch của giới hạn quan sát thì
bài phải trình bày đúng thành kết quả đó, không đổi tên thành tự phục hồi.

## Cơ sở tham khảo mới

- Shao, Hightower, Schindel (2023), Manufacturing Letters35,24–28,
  doi:10.1016/j.mfglet.2022.11.009. Đã xem tóm tắt tác giả và metadata NIST;
  chưa xác minh toàn văn.
- Lu và cộng sự (2024), IEEE CASE, doi:10.1109/CASE59546.2024.10711607.
  Đã xem tóm tắt tác giả và metadata NIST; chưa xác minh toàn văn.

Các nguồn này ủng hộ yêu cầu kiểm chứng chất lượng/phạm vi sử dụng DT; không
chứng minh phương pháp của dự án là mới hoặc đủ điều kiện được chấp nhận.


## Cập nhật bộ thử mới — 2026-11-06

Đã khóa và chạy phép so đồng hồ/tuổi trên điều kiện mới, xem
[phương pháp và kết quả đầy đủ](doi_chung_thoi_gian_20261106.md). Hai mục chốt
bộ thử và so thời gian nguồn/nhận đã có kết quả thăm dò: 6/12 ca bình thường
thiếu xung, trong 6 ca đủ có 2 báo nhầm dù không trễ. Không nới ngưỡng trên bộ
này rồi gọi là đã kiểm chứng. Ưu tiên tiếp theo là rà mô hình cạnh/lấy mẫu và
hiệu chuẩn trên tập khác, giữ một tập chưa xem; sau đó làm bộ nối sự kiện thứ hai.
Bản bàn giao ngắn ở TOM_TAT_DU_AN.md thay cho việc đọc toàn bộ lịch sử chat.
