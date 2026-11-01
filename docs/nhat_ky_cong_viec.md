# Nhật ký hoàn thiện phần mềm — 31/10/2026

## Cách làm theo yêu cầu mới

Hoàn thiện bản triển khai đầu tiên của cả sáu mục bên dưới, sau đó mới chuyển
sang chạy thử. Không vừa làm một mục vừa thay thông số để tối ưu mục đó.
Trong lúc viết chỉ đọc mã, kiểm tra cấu trúc và ghi nhật ký. Các số đo thật
chưa có không được tự gán thành số đo đã xác nhận.

Phạm vi đợt này là **bản tích hợp phần mềm số 1** cho một phôi mỗi chu trình.
Các mục cần máy thật, mô hình khí nén đã hiệu chuẩn, nhiều phôi đồng thời hoặc
tiếp tục một phôi đang dang dở được ghi riêng, không gọi là đã hoàn thành.

## Danh sách công việc

| Mã | Mục cần hoàn thiện trước khi thử | Trạng thái triển khai |
|---|---|---|
| M01 | Chặn dữ liệu/lệnh thuộc sai phiên hoặc lần khởi tạo cũ | Đã viết và ghép |
| M02 | Nhận dữ liệu theo bảng tín hiệu và quy tắc thời gian rõ ràng | Đã viết và ghép |
| M03 | Ghép các phần thành một đường chạy chung và lưu dấu vết đầy đủ | Đã viết và ghép |
| M04 | Thêm nhánh dự báo chuyển động phôi bằng MuJoCo, tách khỏi máy mô phỏng chính | Đã viết và ghép |
| M05 | Trang theo dõi bằng tiếng Việt, đọc kết quả mới và nhật ký | Đã viết và ghép |
| M06 | Cấu hình tổng, hướng dẫn mở, bản bàn giao và sổ kiểm tra | Đã viết và ghép |

“Đã triển khai” chỉ có nghĩa đã viết và ghép mã; khác với “đã chạy kiểm tra”,
“đã đo trên máy thật” và “đã được người dùng nghiệm thu”.

## Các việc vẫn cần làm ở giai đoạn sau

- Ghép và kiểm chứng với PLC thật (bộ điều khiển máy), gồm nguồn thời gian của máy.
- Xác nhận vị trí trục, chân không, liên động và vị trí phôi thật sau dừng.
- Đo/hiệu chuẩn động lực học, khí nén, ma sát và sai số cảm biến.
- Đồng bộ đầy đủ bản CAD V5 và mô hình chuyển động.
- Sản xuất liên tục với nhiều phôi đồng thời và khôi phục phôi đang dang dở.
- Chọn/điều chỉnh chính sách bằng kết quả thử, sau khi bản tích hợp đã hoàn tất.

## Ghi chép theo thứ tự

### 001 — Chốt phạm vi và thứ tự

- Đã đọc lại cấu trúc lõi, giao diện, cấu hình và các phần còn thiếu.
- Chốt sáu mục cần viết/ghép trước khi chạy thử; giữ nguyên số đo và ngưỡng cũ.
- Chưa chạy thí nghiệm mới trong đợt này.

### 002 — M01: mã phiên và lần khởi tạo

- Viết `session.py`: bọc tín hiệu/lệnh với mã phiên, lần khởi tạo, số thứ tự và
  loại đồng hồ; loại bản tin nhầm phiên, nhầm lượt hoặc đã nhận rồi.
- Có kiểm tra lệnh băng, trục, cờ dừng và giữ lệnh dừng dự phòng; chưa có hàm ghi
  lệnh tới thiết bị thật. Đang chờ ghép vào đường chạy chung ở M03.
- Chưa chạy thử hoặc đổi tham số.

### 003 — M02: chuẩn hóa dữ liệu ghi từ ngoài

- Viết `io_adapter.py`, bảng tên tín hiệu và quy tắc đổi thời gian.
- Tệp dùng cho máy thật để trống địa chỉ PLC và chưa xác nhận cảm biến/đồng hồ.
  Dữ liệu thiếu hoặc chưa xác nhận giữ trạng thái chưa có nguồn, không tự biến
  thành tín hiệu “không có vật”. Có tệp ví dụ giả lập riêng để thử sau.
- Mô-đun không gửi lệnh ra PLC. Chưa chạy thử hoặc hiệu chỉnh.

### 004 — M03: ghép đường chạy chung

- Tách `runtime.py` để mô phỏng và đọc lại tệp dùng cùng trình tự điều khiển,
  ước lượng, dự báo, giới hạn tốc độ, đánh giá sau dừng và chặn lệnh.
- Ghép mã phiên vào tín hiệu qua đường truyền và vào lệnh trước khi áp cho mô
  hình; lượt sau đặt lại dùng cùng mã phiên nhưng số lần khởi tạo mới.
- Thêm `replay_input.py`: đọc dữ liệu đã ghi, xuất lệnh vào tệp để xem xét;
  không có đường ghi ra PLC. Lưu nguồn dữ liệu và ghi chú tín hiệu chưa xác nhận.
- Đang chờ các mục còn lại hoàn tất rồi mới chạy kiểm tra chung; chưa đổi ngưỡng.

### 005 — M04: nhánh dự báo chuyển động bằng mô phỏng cơ học

- Viết `physics_predictor.py`: dựng mô hình băng/phôi riêng từ vị trí và tốc độ
  ước lượng, tính các trường hợp dừng/chạy thêm bằng MuJoCo.
- Không sao chép trạng thái thật của cảnh đang chạy. Nhánh mới chỉ mô phỏng
  băng và phôi, chưa phải toàn bộ robot/khí nén/giác hút đã hiệu chuẩn.
- Thêm lựa chọn trong cấu hình và bộ ghép dự báo; mặc định vẫn giữ nhánh tính cũ.
- Chưa chạy thử hoặc tăng ngân sách thời gian để ép nhánh mới thành công.

### 006 — M05: trang theo dõi và nhật ký

- Viết `web/tong_quan.html`, `tong_quan.js` và bộ đọc chỉ cho xem kết quả.
- Trang dùng tiếng Việt, phân biệt hoàn tất/dừng chờ/không chấm đặt phôi, hiển
  thị sáu mục, nhật ký, mã phiên và số bản tin bị loại từ kết quả đã lưu.
- Có cách chọn tệp ngay trong trình duyệt nếu chưa mở máy chủ cục bộ; không tải
  tệp lên bên ngoài và không có nút gửi lệnh tới PLC.
- Chưa mở trang để chạy thử; đang hoàn thiện mục cấu hình và bàn giao cuối cùng.

### 007 — M06: ghép và bàn giao

- Viết danh mục sáu mục, bộ kiểm tra tích hợp, kiểm tra biên bản tin và lệnh,
  lệnh ghép toàn bộ và công cụ đóng ZIP. Thêm chế độ integration-check cho Docker.
- Viết hướng dẫn tiếng Việt: cách mở, đổi cấu hình, đọc dữ liệu và các giới hạn.
- Đưa mã trang tổng quan vào nguồn ảnh thử nghiệm; trang chạy riêng, không tự điều khiển máy.
- Giữ nguyên ngưỡng đang dùng; nhánh dự báo cơ học vẫn là lựa chọn riêng.

### 008 — Mốc hoàn thành triển khai trước khi kiểm tra

- Cả M01–M06 đã có mã, cấu hình, hướng dẫn và mã kiểm tra cần thiết.
- Đến mốc này chưa chạy kiểm tra tự động hay mô phỏng trong đợt tích hợp.
- Từ đây mới chuyển sang kiểm tra chương trình chung. Nếu lỗi sẽ ghi sửa lỗi;
  không coi sửa chương trình là đo/hiệu chuẩn hoặc tự nghiệm thu.

### 009 — Kiểm tra chung sau khi đủ sáu mục (31/10–01/11/2026)

- Kiểm tra cấu trúc: sáu mục có đầy đủ tệp; phân tích cú pháp Python và JSON đạt.
- Lần đầu đạt 92 kiểm tra logic, hai chu trình chặt chẽ/mở giả định và đọc lại dữ liệu.
- Bổ sung kiểm tra bộ đọc trang và quá hạn dự báo: lần cuối đạt 93 kiểm tra logic.
- Chu trình mở giả định hoàn tất, bộ chấm độc lập xác nhận đặt phôi đạt. Chế độ chặt
  chẽ dừng do chưa xác nhận trục, hành trình giữa xi lanh và chân không, đúng phạm vi.
- Nhánh dự báo MuJoCo tính đủ 54 trường hợp; một lần trên WSL mất khoảng 306 ms.
  Đây chỉ là một phép kiểm tra chức năng với hạn 2 giây, không phải thống kê tốc độ.
  Chưa đạt bằng chứng dùng hạn 20 ms; nhánh này vẫn không phải mặc định. Kiểm tra
  cưỡng bức quá hạn xác nhận trả lệnh dừng chờ. Không đổi các ngưỡng sản xuất.

### 010 — Trang theo dõi và giới hạn môi trường

- JavaScript qua kiểm tra cú pháp. Bộ đọc kết quả qua kiểm tra tự động.
- Windows sandbox chặn kết nối nội bộ; lần thử ngoài sandbox bị hết thời gian.
- Chạy máy chủ và khách HTTP trong cùng WSL: API tổng quan, HTML và JavaScript
  đều trả mã 200; đủ sáu mục, không kết nối máy thật. Chưa kiểm tra bố cục bằng mắt.
- Việc tải thư viện Docker bị kéo dài qua thời gian máy tạm ngưng; đây không phải
  thời gian tính mô phỏng và không dùng để báo cáo hiệu năng.

### 011 — Docker thử nghiệm và bàn giao (01/11/2026)

- Ảnh candidate-20261031-integrated-core-v1 đã đóng và kiểm tra bên trong:
  93 kiểm tra logic; 5 nhóm kiểm tra tích hợp; 15 tình huống bản tin đặt lại +
  2 cảnh MuJoCo; 15 tình huống tái cấu hình đều đạt.
- Dấu kiểm tra mã trong ảnh khớp tệp hiện tại, giữ nguyên toàn bộ ảnh cũ.
- Chi tiết mã ảnh, tệp nguồn và đường dẫn bằng chứng ghi trong docker/RELEASES.md.
- Đóng gói mã lõi, cấu hình, mô hình MuJoCo, trang theo dõi và hướng dẫn thành ZIP;
  không gộp toàn bộ lịch sử thí nghiệm hay tự sửa bản CAD V5.
- Chưa có nghiệm thu người dùng cho bản này; không gắn nhãn accepted/stable/latest.
- Kết thúc đợt: đã triển khai đủ sáu mục trong phạm vi bản tích hợp. Giai đoạn
  tiếp theo mới thử từng mục và điều chỉnh theo kế hoạch, chưa tuyên bố xong máy thật.

### 012 — Chuẩn bị công khai GitHub (01/11/2026)

- Người dùng yêu cầu công khai toàn bộ dự án lên tài khoản Namct123.
- Kiểm tra đúng kho network-aware-production-twin và quyền quản trị; kho ban đầu riêng tư.
- Bổ sung CAD V5 và các PDF đã xuất, cập nhật trang bắt đầu và đánh dấu bài báo là bản thảo.
- Chuẩn bị các gói bàn giao ở Releases; giữ tệp tạm, môi trường cài đặt, khóa truy cập
  và dữ liệu chạy thô ngoài kho nguồn. Bằng chứng kiểm tra đã chọn vẫn có trong docker/evidence.
- Việc công khai mã không thay thế nghiệm thu kỹ thuật; Docker mới vẫn là candidate.

### 013 — Đã công bố GitHub (01/11/2026)

- Đã đẩy bản tích hợp cùng CAD V5, Unity, mã LaTeX, PDF và tài liệu lên nhánh main.
- Kho https://github.com/Namct123/network-aware-production-twin đã chuyển sang công khai;
  kiểm tra GitHub API không dùng thông tin đăng nhập xác nhận truy cập được.
- Commit công bố: `10c3ccf066a9af8f450c1832e0de4f0eef289756`, tác giả Namct123,
  email namface561@gmail.com theo yêu cầu người dùng.
- Releases: https://github.com/Namct123/network-aware-production-twin/releases/tag/candidate-20261101-public-handoff
- Đã đăng 9 tệp tải xuống: 8 gói ZIP và SHA256SUMS.txt. Gói nguồn đầy đủ chứa
  đúng mã của commit công bố; các gói có tên/ngày cũ là bản lịch sử, không tự đồng bộ.
- Đã kiểm tra các phiên bản Actions được tham chiếu tồn tại trên kho chính thức;
  kiểm tra đóng gói cục bộ đạt 2/2. Có lượt Actions đang chạy tại thời điểm xác minh,
  không coi kết quả cục bộ là bằng chứng lượt trực tuyến đó đã xong.
- Mẫu khóa truy cập không được phát hiện trong các tệp đã rà soát. Không đẩy .env,
  môi trường cài đặt hoặc toàn bộ log thô. Bằng chứng đã chọn và dữ liệu minh họa
  được giữ trong kho; không đăng ảnh Docker nhị phân lên một dịch vụ khác.
- Giữ Docker mới ở trạng thái candidate, việc cho phép công khai không phải nghiệm thu máy thật.
