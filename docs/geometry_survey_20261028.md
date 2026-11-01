# Số đo sơ bộ nhận ngày 28/10/2026

**Đính chính bố trí cảm biến mới nhất:** chiếc đầu tiên nằm trên đầu xi lanh đẩy;
chiếc thứ hai giữ nguyên vị trí ban đầu; chiếc thứ ba dịch thêm 50 mm từ chính
vị trí cũ theo chiều phôi, không phải cách chiếc thứ hai 50 mm. CAD V5 đặt PS2 ở
Y = −215 mm, PS3 từ −5 mm thành +45 mm. Các suy ra
PS1/PS2 lần lượt ở 50/260 mm trên băng dọc bên dưới là lịch sử, không còn được áp
cho bản CAD sửa này. Số đo 235 mm vẫn lưu, cần đối chiếu lại cặp/phương đo trước khi
đưa vào runtime. Xem `docs/cad_v5_measured.md` để biết các tọa độ và giả định dựng.

Đã lưu số liệu gốc trong `mujoco/configs/survey_20261028.json`. Đây là hồ sơ khảo sát,
không phải profile chạy của `config.py`. Chưa có sai số dụng cụ hoặc mốc tọa độ đầy đủ;
không gán sai số bằng 0. Baseline và nhật ký cũ vẫn mang các giả định cũ.

| Hạng mục | Số đo người dùng cung cấp |
|---|---|
| Nhôm định hình | 2020, tiết diện danh nghĩa 20 × 20 mm |
| Lòng khung dọc băng | 460 mm, đã xác nhận phương |
| Lòng khung ngang băng | 465 mm |
| Mặt đế máy đến mặt dưới thanh robot di chuyển | 325 mm, đã xác nhận mốc đế |
| Mặt dưới thanh → giác hút, thu / duỗi hết | 120 / 200 mm |
| Bề rộng băng hữu dụng | 80 mm |
| Băng dưới giác hút / băng còn lại | 530 / 470 mm |
| Đầu băng → mép trong thanh ngang phía trên dóng xuống | 270 mm dọc băng; chưa có tọa độ tuyệt đối |
| Hai điểm ngoài cùng của hai mặt cảm biến | 235 mm |
| Hai điểm xa nhất trên một mặt cảm biến | 25 mm |
| Quang trên đầu xi lanh đẩy | Chiếc thứ ba, độc lập với hai cảm biến trên băng |
| Tâm mặt cảm biến đầu tiên → đầu băng hữu dụng | 50 mm, số đo bổ sung |
| Giác hút thu tối đa → mặt đế | **230 mm**, số đo trực tiếp bổ sung, ưu tiên hơn suy ra cũ |

## Bổ sung mới nhất: mốc cảm biến và cao độ thu

**Phôi thực đã được bổ sung: khối 60 × 60 × 60 mm.** Trên mặt băng Z = 100 mm,
mặt trên phôi ở **Z = 160 mm**. Nếu cao độ đầu hút được đo tại mặt tiếp xúc,
độ hạ hình học từ vị trí thu Z = 230 mm đến mặt phôi là **70 mm**. Đây là đích
tiếp xúc sơ bộ, không phải lệnh chạy đã hiệu chuẩn: còn độ mềm giác hút, sai số
cao độ, phản hồi và điều kiện dừng. Duỗi hết đến Z = 130 mm sẽ xuống thấp hơn mặt
trên phôi 30 mm, vì thế không lấy duỗi hết làm đích gắp phôi này một cách mặc định.

Phôi rộng 60 mm trên băng hữu dụng rộng 80 mm còn **10 mm mỗi bên khi đặt giữa**;
đây là khoảng hình học, chưa phải sai số định vị cho phép. Chưa biết khối lượng
phôi, vật liệu và độ kín mặt hút; không tăng khối lượng theo thể tích một cách tự động.
Kích thước phôi 22 mm trong baseline cũ không còn đại diện cho phôi thực này.
Chưa áp kích thước mới riêng lẻ vào runtime vì phải cập nhật đồng bộ cao độ băng,
đầu hút, giới hạn chuyển động và mô hình tiếp xúc trước khi kiểm chứng lại chu kỳ.

**Cập nhật cao độ mới nhất, ưu tiên các số đo trực tiếp:** mặt băng cao **100 mm**,
giác hút thu hết cao **230 mm**, duỗi hết cao **130 mm**, đều trên mặt đế máy.
Hành trình đầu hút suy ra là **230 − 130 = 100 mm**. Các suy ra 205/125 mm và
150 mm từ số đo trước ở phía dưới chỉ được giữ làm lịch sử, không dùng làm
cao độ đầu hút ưu tiên. Chưa đồng nhất hành trình đầu hút với hành trình xi lanh.

Điểm đo trên giác hút khi duỗi hết vẫn cách mặt băng **30 mm**. Nếu đây là mặt
tiếp xúc giác hút, không có cơ cấu nâng khác và bỏ qua biến dạng, phôi cao 30 mm
mới có mặt trên trùng điểm cuối này; phôi thấp hơn chưa chạm được. Phôi cao hơn
sẽ chạm trước khi duỗi hết, cần kiểm tra độ mềm và điều kiện dừng thực tế.
Baseline giả định phôi cao 22 mm: với mặt băng mới, mặt trên phôi ở 122 mm,
còn cách đầu hút thấp nhất **8 mm**. Đây là bất nhất của baseline với các số đo
mới, chưa phải kết luận máy thật không gắp được vì chưa có chiều cao phôi thật.

Chọn tọa độ cục bộ s = 0 tại đầu băng hữu dụng vừa được đo, s tăng dọc vào băng:
**s1 = 50 mm**, **s2 ≈ 50 + 210 = 260 mm** nếu cảm biến thứ hai nằm tiếp theo
chiều đó và khoảng tâm suy ra 210 mm đúng. Đây là vị trí tâm mặt cảm biến,
chưa phải hiệu chuẩn vùng kích hoạt thực; chưa gán tọa độ world hoặc đổi nhãn PS1/PS2.

Ưu tiên số đo trực tiếp mới **Z đầu hút khi thu = 230 mm trên mặt đế**.
Số đo cũ suy ra 325 − 120 = 205 mm, chênh **25 mm**. Hai phép đo chưa thống nhất;
không lấy trung bình hoặc thay đổi chiều cao thanh để ép khớp. Nếu giữ hành trình
đầu hút suy ra 80 mm thì cao độ duỗi hết sẽ là **150 mm**, nhưng đây chỉ là suy ra
có điều kiện trong lịch sử; số đo trực tiếp mới đã thay thế bằng 130 mm.

## Các hệ quả quan trọng

1. Độ dịch chuyển giác hút theo phương đứng suy ra là **200 − 120 = 80 mm**.
   Đây là hành trình đầu hút quan sát được, chưa tự chứng nhận hành trình xi lanh.
   Mô hình cũ dùng giới hạn A2 75 mm; nhãn TN10×75-S từng thấy trong ảnh cũng là
   lý do cần kiểm tra lại mốc đo, không tự sửa số đo người dùng.
2. **Phép suy ra cũ, đã bị số đo thu trực tiếp mới làm mâu thuẫn:** cao độ khi thu và duỗi là
   **325 − 120 = 205 mm** và **325 − 200 = 125 mm**. Đặt Z = 0 trên mặt đế khi
   dựng bản hình học mới; cần đổi gốc phù hợp với mặt đế trong MJCF cũ. Cần kiểm tra đầu hút
   có chạm được mặt trên phôi bằng cao độ băng cộng chiều cao phôi.
3. **235 mm không mặc nhiên là khoảng cách hai tia quang.** Nếu hai mặt cảm biến
   cùng bề rộng 25 mm theo phương băng và 235 mm là khoảng bao ngoài dọc phương đó,
   khoảng cách tâm là **235 − 12,5 − 12,5 = 210 mm**. Nếu đúng giả thiết này,
   dùng nhầm 235 mm để suy vận tốc từ hai cạnh sẽ làm vận tốc lớn hơn khoảng
   **11,9%** so với khoảng tâm 210 mm. Nếu đo bề mặt nghiêng hoặc mép vỏ, phép trừ
   này chưa xác định đúng hai vị trí phát hiện; cần đo tâm tia/vùng kích hoạt thực.
4. Khoảng hở lòng khung **không bằng hành trình XY**: còn kích thước con trượt,
   đầu nối, động cơ và khoảng tránh va chạm. Không đặt giới hạn XY bằng 460/465 mm.
5. Mô hình băng dọc cũ dài 490 mm, băng ngang vùng mặt băng dài 590 mm,
   rộng 73 mm; các số mới 530 / 470 / 80 mm sẽ thay thế sau khi chốt cùng loại
   kích thước (chiều dài băng hữu dụng hay chiều dài toàn bộ cụm).
6. Đã xác nhận tổng **ba cảm biến quang**: hai trên băng và một trên đầu đẩy.
   Mô hình tín hiệu hiện mới hỗ trợ PS1/PS2; không coi quang thứ ba là công tắc
   hành trình xi lanh. Cần vị trí tia, chức năng và địa chỉ PLC trước khi thêm
   kênh và điều kiện điều khiển. Chưa tự gán địa chỉ I/O còn trống.

## Các mốc cần bổ sung để dựng lại có căn cứ

- Đã có phôi cao 60 mm; còn xác nhận điểm đo trên giác hút là mặt tiếp xúc.
- Đã có tâm mặt cảm biến đầu tiên cách đầu băng hữu dụng 50 mm; cần nhận diện đầu
  này trên bản vẽ để đổi s1/s2 sang hệ tọa độ world và xác nhận thứ tự theo chiều phôi.
- Kiểm tra hành trình xi lanh/điểm gá vì cao độ đầu hút mới suy ra 100 mm,
  khác 80 mm suy ra từ khoảng cách đến thanh và 75 mm danh nghĩa trước đây.
- Cần nhận diện đầu băng trong bản vẽ để gán chiều có dấu cho quan hệ 270 mm;
  ý nghĩa đo dóng từ thanh ngang phía trên đã được xác nhận.

Sau khi chốt mốc: dựng profile hình học riêng, cập nhật chiều cao/đầu hút trong MJCF,
kiểm tra hành trình và khả năng chạm phôi, cập nhật sơ đồ web rồi chạy lại các ca
nghiệm thu. Kết quả cũ không được coi là đã kiểm chứng hình học mới.
