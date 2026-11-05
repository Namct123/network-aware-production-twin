# Xem hệ thống bằng hình tương tác Anatomy

Ngày: 2026-11-05. Đây là bản candidate để người dùng xem thử.

## Mở và thao tác

1. Nhấp đôi `web/anatomy.html`: dữ liệu và mã vẽ đã nằm trong tệp, không cần Internet, Node hay Docker để xem.
2. Chọn tình huống rồi bấm **Phát lại**. Thanh trượt tua từng mẫu 20 ms.
3. Bấm **Tới HOLD** để đến đúng lần đầu phần mềm giữ chu trình; phần cuối nhật ký còn có thời gian phôi ổn định sau dừng.
4. Chọn **PS1 không báo có phôi**, bật **So với ca có cùng tín hiệu cảm biến**. Khối mờ là ca băng cấp phôi đứng ở cùng thời điểm. Chênh lệch tại HOLD là khoảng 35,4 cm; tới cuối nhật ký khoảng 35,5 cm vì phôi còn chuyển động sau lệnh dừng.
5. Chọn PS3 không báo để xem cặp băng dọc đứng; tại HOLD chênh khoảng 24,8 cm.
6. Bấm vào máy hoặc từng bước dưới hình để đọc lời giải thích. Có nền sáng/tối và hỗ trợ điện thoại.
7. Đặt tiêu điểm vào hình: phím cách phát/dừng; mũi tên đổi một mẫu, Shift+mũi tên đổi 25 mẫu; Home/End về đầu/cuối; Escape dừng.

Với thiết bị bật giảm chuyển động, không tự chạy hoạt ảnh; thanh tua và các phím vẫn xem được từng mẫu.

Có thể chạy `python web/server.py --port 8766` rồi mở http://127.0.0.1:8766/anatomy.html để dùng cùng trang tổng quan dự án. Máy chủ mặc định chỉ nghe trên chính máy này.

## Trang này giải thích gì?

Hình có 67 khối SVG (đồ họa véc tơ), gồm hai băng tải, khung, robot, đầu đẩy, ba mốc quang, sáu hộp và các chi tiết minh họa. Bảng bên phải đọc đúng mẫu dữ liệu với phôi đang hiển thị. Sáu bước giải thích khung tín hiệu, kiểm tra mạng, ước lượng vị trí, dự báo, kiểm tra bất thường và quyết định.

Hai góc nhìn được tách rõ:

- Vị trí phôi và tốc độ áp dụng ở MuJoCo là dữ liệu dành cho người đánh giá.
- Bit cảm biến, ước lượng, lệnh và quyết định là những gì lõi nhận/ghi. Vị trí thật không được cấp ngược vào lõi bằng trang này.

Bảy ca đều không chèn lỗi mạng; mục Mạng giải thích chức năng của mô đun, không tuyên bố những ca này đã đo độ trễ mạng. Ca bình thường ở chế độ nghiêm ngặt cũng HOLD trước gắp vì thiếu xác nhận XY/A2/chân không. Không biến điều đó thành lỗi cảm biến hoặc tuyên bố đã hoàn thành chu kỳ.

## Nguồn và giới hạn

- Nguồn duy nhất: `output/docker/sensor_drive_20261104_v2/01_*`; chỉ lượt 01 của bảy ca, tổng 1.973 mẫu. Không sinh mới kết quả điều khiển.
- `scripts/export_anatomy.py` ghép đúng thời gian giữa observations, decisions và truth_evaluator_only; ghi SHA-256 của 30 tệp đầu vào. `web/anatomy_data.json` chứa dữ liệu chọn lọc; HTML nhúng lại đúng JSON này.
- Hình học hộp lấy từ `01_nominal/effective_model.xml`, tư thế khớp tham chiếu bằng không. Giá đỡ, vít và ký hiệu đầu hút là minh họa, không phải số đo bổ sung.
- Không có vị trí khớp thực hoặc góc quay phôi trong nhật ký này. Robot, đầu hút và đầu đẩy giữ tư thế tham chiếu; phôi chỉ hiển thị tọa độ tâm bằng khối song song trục. Không lấy lệnh làm phản hồi vị trí.
- CAD V5 và mô hình MuJoCo vẫn khác hình học. Hình này không đồng bộ chúng.
- Sắp khối theo mặt phẳng tách và miền chồng hình chiếu để vẽ; không phải bộ kiểm tra va chạm hoặc chứng nhận hình học lắp ráp. Không dùng kiểm tra hình vẽ để suy ra an toàn vật lý.
- Khối đối chiếu cố ý bán trong suốt. Hai cặp đã có bằng chứng cùng chuỗi quan sát/quyết định tới HOLD đầu tiên; ngoài miền đó trang chỉ hiển thị dữ liệu của từng ca, không mở rộng kết luận.
- HOLD không tự xóa; trang chỉ đọc dữ liệu, không nhận lệnh PLC, không sửa lõi, profile hoặc dữ liệu nghiên cứu cũ.

## Dựng lại và kiểm tra

```powershell
python scripts/export_anatomy.py
node scripts/build_anatomy.mjs
python -m unittest discover -s web -p test_anatomy.py -v
```

Bước xuất cần còn nhật ký nguồn trên D. Node chỉ cần khi dựng lại, không cần khi mở HTML. Dùng thư viện chuẩn Python và Node; không thêm npm package.

Skill được cài ở `C:/Users/Admin/.codex/skills/anatomy/SKILL.md`. Bộ vẽ được lưu tại `scripts/anatomy/iso-kit.mjs` để không phụ thuộc đường dẫn skill khi chuyển máy; giấy phép MIT kèm theo và nhúng trong HTML. Nguồn: https://github.com/wheresryan22/anatomy (main, tải 2026-11-05). Mã băm của bản bộ vẽ và các nguồn dự án ghi trong bằng chứng Docker candidate.

Kiểm tra trình duyệt dùng `capture.mjs`, `drive.mjs` của Anatomy và `scripts/anatomy/check_actions.json`: 21 tư thế đại diện không có vòng thứ tự vẽ; phát/dừng, thanh tua, tới HOLD, hai nền, bảng giải thích và so sánh được kiểm tra. Đã đọc ảnh điện thoại 390 px và ảnh phóng to 4×; không có lỗi JavaScript hoặc tràn ngang ở ảnh đã kiểm tra. Kiểm tra đầu đường nét báo 0/0 vì không dùng đường trang trí rời; đây không phải kết quả kiểm định cơ khí.

## Docker

Bản `candidate-20261105-anatomy` chứa trang và dữ liệu nhúng. Chỉ tạo candidate để xem thử, không đổi bản accepted. Người dùng chưa nghiệm thu phiên bản này; ảnh không đẩy lên registry.
