# DT Explorer — giao diện giải thích lõi Digital Twin

## Chạy mô phỏng mới từ web — cập nhật 28/10/2026

Đã có biểu mẫu **Thí nghiệm**: đổi tốc độ, lỗi quang/công tắc A1, mạng, seed,
hộp và profile; chạy một lượt hoặc cặp nền/dự báo rồi mở kết quả mới trên sơ đồ.
Phần này cần MuJoCo/NumPy trong WSL đã cấu hình. Mở `START_SIMULATION_EXPLORER.cmd`
thay cho launcher chỉ xem. Xem `docs/live_experiments.md` trong checkout gốc để đọc
cách chạy và các giới hạn; hướng dẫn tương tự đi kèm bản ZIP ở thư mục `docs/`.
Chế độ mặc định vẫn nghiêm ngặt, chưa tự cho phép giả định hở vòng.

## Mở trên Windows

1. Máy cần Python **3.10 trở lên**; không cần cài MuJoCo hoặc thư viện pip để xem giao diện này.
2. Nhấp đúp `START_EXPLORER.cmd` trong thư mục này. Giữ cửa sổ máy chủ mở.
3. Mở **http://127.0.0.1:8765** bằng Chrome, Edge hoặc trình duyệt trong Codex.
4. Khi dùng xong, nhấn Ctrl+C trong cửa sổ máy chủ. Đóng tab web không tự tắt máy chủ.

Nếu cổng 8765 đã có chương trình khác, chạy `python server.py --port 8766` rồi mở cổng tương ứng.
Máy chủ chỉ lắng nghe localhost. Thành viên khác giải nén bản đóng gói và chạy trên máy của họ.

## Trình bày cho thầy hướng dẫn trong 5 phút

1. **Bình thường:** bấm Phát chu kỳ. Theo dõi phôi xanh từ băng ngang, qua A1, PS1 và PS2, tới thao tác gắp/thả. Bấm Tạm dừng, +1 mẫu hoặc kéo thanh thời gian. Các nút trạng thái nhảy đến thời điểm chuyển trạng thái thực trong log.
2. **Lỗi PS2:** chọn PS2 kẹt thấp có dự báo rồi bấm HOLD. Bộ dự báo dừng vì biên dừng xấu nhất không còn cho phép đi thêm một tick. So với PS2 kẹt thấp điều khiển nền: trong fixture đã chạy, HOLD sớm hơn 40 ms mô phỏng; không suy rộng thành tỷ lệ phát hiện lỗi chung.
3. **Trễ mạng:** xem tuổi mẫu và vị trí ước lượng. Khung nét đứt là ước lượng tại nguồn, phôi xanh là trạng thái MuJoCo ở hiện tại. Đồ thị phía dưới đối chiếu tại cùng thời điểm nguồn để tránh so sánh sai.
4. **Thiếu phản hồi:** lượt nghiêm ngặt dừng trước khi gắp vì chưa xác nhận XY, A2 trung gian và chân không. Các lượt hoàn tất đã bật giả định hở vòng, không phải đã có cảm biến vật lý đầy đủ.
5. **Phòng dự báo:** thử “Còn xa mép” → Chạy; “Gần mép” → Chạy; “Dữ liệu cũ” → Chạy. Các nút chỉ đặt giả thiết; bấm Chạy mới gọi `predictor.py` thật. Biên dừng âm có nghĩa có ít nhất một quỹ đạo vượt giới hạn trong mô hình.
6. **Cách hoạt động:** bấm từng khối để thấy trách nhiệm và dữ liệu của mô phỏng, mạng, ước lượng, trình tự, supervisor và bộ đánh giá riêng.

## Ba loại thông tin cần phân biệt

- **Phát lại MuJoCo:** 10 lượt acceptance đã chạy ngày 27/10/2026, lấy từ `output/dt_predictive_acceptance_20261027_final`. Giao diện không chạy lại vật lý khi chọn kịch bản hoặc tăng tốc phát. Tốc độ phát 4× chỉ là tốc độ xem.
- **Dự báo tương tác:** máy chủ Python gọi đúng `mujoco/predictor.py` với dữ liệu thanh trượt. 54 tổ hợp = 3 vị trí × 3 vận tốc × 3 trễ phản ứng × 2 hành động. Chân trời 0,5 s, bước 20 ms. Thời gian tính hiển thị là thời gian tính predictor, không phải độ trễ toàn hệ thống.
- **Sơ đồ giải thích:** hình chiếu bằng vẽ theo cấu hình và vị trí từ log, không phải bản CAD hay mô hình 3D để kiểm tra va chạm. Phản hồi XY/vacuum chưa được đo, các thông số chưa hiệu chuẩn vật lý.

Phòng dự báo độc lập với replay và không truyền lệnh đến PLC. Không có điều khiển phần cứng trong ứng dụng này. Các đường dự báo là mô hình động học dừng 1D, chưa phải 54 lần chạy MuJoCo tiếp xúc toàn hệ thống.

## Tệp và khả năng kiểm chứng

- `server.py`: máy chủ stdlib và API dự báo chỉ nhận bốn số trong miền cho phép.
- `index.html`, `style.css`, `app.js`: giao diện chạy không cần build và không tải tài nguyên ngoài Internet.
- `data/*.json`: nhật ký đóng gói, cấu hình, kết quả, manifest và SHA-256 các tệp nguồn. Nút tải JSON xuất toàn bộ dữ liệu của lượt đang xem.
- `build_replays.py`: tạo lại dữ liệu khi còn thư mục output nguồn trong checkout dự án; không cần chạy trong bản đóng gói đã có dữ liệu.
- `test_explorer.py`: kiểm tra API, công thức biểu đồ và nhật ký.

Từ thư mục gốc dự án, chạy `python web/test_explorer.py` để kiểm tra hoặc `python web/build_replays.py` để xuất lại log nguồn. Nếu chỉnh lõi predictor, replay cũ vẫn là kết quả của phiên bản có hash trong manifest, không tự biến thành kết quả phiên bản mới.

## Thiết kế

Áp dụng skill UI UX Pro Max từ https://github.com/nextlevelbuilder/ui-ux-pro-max-skill (truy xuất 27/10/2026): bố cục dashboard vận hành, nền slate, trạng thái xanh, tập trung vào độ rõ dữ liệu và khả năng dừng/tua. Dùng font hệ thống thay font trực tuyến để hoạt động ngoại tuyến, điều khiển native, nhãn văn bản ngoài màu sắc, focus bàn phím và bố cục đáp ứng. Bản skill tạm đã bỏ khỏi cây làm việc trong đợt dọn 2026-11-05; giao diện đã sinh không phụ thuộc thư mục skill này.


## Hình tương tác Anatomy (2026-11-05)

Mở `anatomy.html` trực tiếp hoặc qua máy chủ web hiện có. Chọn ca, bấm **Phát lại**, **Tới HOLD**, bật đối chiếu và bấm từng bộ phận hoặc sáu bước phía dưới.
Dữ liệu là lượt 01 của bảy ca `sensor_drive_20261104_v2`, không phải dữ liệu trực tiếp. Đọc `docs/truc_quan_anatomy.md` để biết nguồn, giới hạn và cách dựng lại.
