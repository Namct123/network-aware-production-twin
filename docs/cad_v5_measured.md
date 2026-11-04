# Mô hình 3D V5 theo số đo sơ bộ ngày 28/10/2026

## Sửa vị trí quang theo xác nhận mới nhất

**Đính chính cuối:** 50 mm là **dịch chuyển của PS3 so với chính vị trí cũ**,
không phải khoảng cách PS2–PS3. PS1 nằm trên đầu đẩy. PS2 giữ vị trí quang đầu
trên băng của bản V5 gốc: **Y = −215 mm**. PS3 từ **Y = −5 mm** dịch sâu thêm
50 mm thành **Y = +45 mm**. Khoảng tâm PS2–PS3 sau dịch là **260 mm**.
Không thêm cảm biến thứ tư.
**Hướng quét PS1 đã sửa:** trục quang **+Y**, trùng phương và cùng chiều đẩy A1.
Thân cảm biến nằm phía sau mặt đầu quét, không còn nằm ngang theo +X như hai
cảm biến bên băng. Tâm mặt quang giữ tại (−150, −385, 152,5) mm; chỉ hướng lắp
và gá sơ bộ thay đổi. PS2/PS3 giữ nguyên vị trí và hướng hiện tại.
Các tên PS1/PS2/PS3 trong CAD chỉ nhận diện hình học, không tự đổi địa chỉ PLC.

Khoảng 50 mm của cảm biến đầu được biểu diễn theo phương băng ngang: tâm mặt quang
X = −150 mm, đầu băng ngang hữu dụng X = −200 mm. Tâm mặt quang cùng Y = −385 mm
với đầu đẩy, nằm trên mặt trên tấm đẩy. Kích thước gá và cao độ cụ thể vẫn ước lượng.

**Các mô tả hai quang cách tâm 210 mm và PS1 tại Y = −215 mm ở bản đầu bên dưới
đã được thay thế.** Số đo bao ngoài 235 mm vẫn được giữ trong hồ sơ gốc nhưng không
ép vào cặp mới: cần nhận diện lại cặp và phương đo trước khi áp vào bộ ước lượng.

Đã xuất ba bộ STEP/GLB trong `output/cad/`:

- `production_twin_v5`: đầu hút thu, điểm tiếp xúc ở Z = 230 mm.
- `production_twin_v5_pick`: đầu hút hạ 70 mm, chạm mặt trên phôi ở Z = 160 mm.
- `production_twin_v5_extended`: đầu hút hạ hết 100 mm, Z = 130 mm. Tư thế này
  đi vào vùng phôi cao 60 mm nếu phôi còn ngay dưới; chỉ dùng để đối chiếu hành trình,
  không dùng làm đích gắp mặc định.

Mốc Z = 0 là **mặt trên đế máy**; tấm đế nằm dưới mốc đó. Đơn vị CAD là mm.
STEP có thể nhập vào Fusion. GLB là xuất từ CAD, dùng để xem/nhập phần mềm 3D.

Đã áp hình học: khung bọc tiết diện 20 × 20 mm, lòng 465 mm ngang × 460 mm dọc
băng; mặt dưới thanh di chuyển 325 mm; băng dọc 530 × 80 mm và ngang 470 × 80 mm,
mặt băng cao 100 mm; phôi 60 × 60 × 60 mm. PS1 trên đầu đẩy; PS2 giữ nguyên;
PS3 dịch +50 mm từ vị trí cũ, như tọa độ nêu đầu tài liệu. Mặt quang mô hình rộng 25 mm.

**Giả định bố trí có công bố:** +Y là chiều băng dọc. Băng dọc từ Y = −265 đến
+265 mm. Mép trong thanh ngang trước Y = −5 mm, nên đầu +Y cách mép này 270 mm.
Nếu người dùng chỉ đầu băng còn lại, cần đổi bố trí theo mốc đó; đây chưa phải
tọa độ world được đo độc lập. Hai cảm biến đặt tại Y = −215 và −5 mm theo thứ tự
đi vào từ đầu −Y. Gốc trục X và vị trí các hộp vẫn ước lượng.

Rãnh tiết diện nhôm, kiểu con trượt, chân băng, gá cảm biến thứ ba và kích thước
xi lanh chưa đo đủ: bản này dùng hình bao giản lược có tên chi tiết. Chưa xác nhận
cảm biến thứ ba thuộc địa chỉ PLC nào. Hành trình đầu hút suy ra 100 mm không tự
chứng minh xi lanh mang mã hành trình 100 mm.

Nguồn bố trí Fusion: `fusion/ProductionTwin_V5/ProductionTwin_V5.py`.
Nguồn xuất CAD: `scenes/production_twin_v5.py`. Chạy script này với môi trường
Python có cadgen/build123d đã cài để dựng lại. Script Fusion có thể chạy trong
Fusion để tạo tài liệu mới và xuất `.f3d`; lần cập nhật này đã xuất STEP/GLB,
không khẳng định đã chạy hoặc lưu tài liệu native Fusion.

Kiểm tra kích thước: `scenes/check_production_twin_v5.py`; kết quả lưu tại
`output/cad/production_twin_v5_checks.json`. Kiểm tra hợp lệ từng solid STEP
không thay thế kiểm tra va chạm toàn hành trình hoặc kiểm chứng máy thật.

**Phạm vi:** cập nhật CAD 3D. CAD V5 và lõi MuJoCo đang chạy chưa đổi đồng
bộ sang V5; không dùng các nhật ký cũ để chứng minh chu kỳ chạy với hình học mới.
