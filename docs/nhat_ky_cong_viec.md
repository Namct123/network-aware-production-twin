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

### 014 — Dọn phần không còn dùng (01/11/2026)

- Theo yêu cầu người dùng, gỡ cầu nối Factory I/O, scene mẫu và bảng địa chỉ,
  ba script dựng/kiểm tra cầu nối, cùng kiểm tra riêng và pyproject chỉ phục vụ cầu nối.
- Gỡ bước cài mcp/pymodbus/pytest và chạy cầu nối khỏi GitHub Actions; các kiểm tra
  lõi hiện dùng unittest có sẵn, thư viện MuJoCo giữ trong tệp yêu cầu Docker.
- Dọn hướng dẫn cũ trong README, cập nhật liên kết nguồn CAD V5 và cách chạy kiểm tra.
- Giữ mã PLC tương lai, mô hình CAD, Unity, MuJoCo, tài liệu bài báo và bằng chứng
  kiểm tra vì còn liên quan trực tiếp đến hệ thống. Không viết lại lịch sử Git.
- Chuẩn bị gói nguồn mới và cập nhật Releases để không tiếp tục phát gói nguồn
  chứa cầu nối cũ. Bản Docker lõi không đổi vì phần vừa gỡ chưa nằm trong ảnh đó.

### 015 — Kiểm tra sau khi dọn

- 93 kiểm tra lõi DT, 8 kiểm tra web và 2 kiểm tra đóng gói đều đạt trong WSL.
- Rà lại mã chạy không còn import, địa chỉ hoặc lệnh gọi cầu nối đã gỡ.
- Các tệp lõi DT, cảnh Unity và STEP CAD V5 vẫn có đủ. Chưa đổi thuật toán,
  tham số vật lý hoặc nguồn đóng ảnh Docker nên giữ nguyên ảnh lõi hiện tại.
- Nguồn công khai mới dùng gói ProductionTwin_Focused_Source_20261101.zip;
  gỡ gói nguồn công khai cũ có chứa cầu nối khỏi Releases và cập nhật mã kiểm tra tệp.
- Các commit cũ vẫn là lịch sử; thao tác dọn không xóa bằng chứng kiểm tra hay
  đổi các tag Docker đã được nghiệm thu.

### 016 — Đợt đánh giá có đối chứng (02/11/2026)

- Chốt ba mục: N01 đo thời gian hai nhánh dự báo; N02 ma trận lỗi từng yếu tố;
  N03 ghép báo cáo, trang tổng quan và Docker thử nghiệm. Viết đủ trước khi chạy.
- N01: thêm qualify.py, ghi thời gian ngoài hàm và bên trong, lượt làm nóng riêng,
  khởi tạo riêng, trung vị/p95/lớn nhất và số lượt thiếu kịch bản/quá hạn.
- N02: dùng lại bộ thử check_robustness, không viết một bộ điều khiển khác.
  Có 6 tình huống × 2 seed × 2 chính sách = 24 lượt. So bật/tắt giới hạn tốc độ
  cố định, không gọi là so với PLC tuần tự. Giữ kết quả không đạt để điều tra.
- N03: ghép báo cáo tiếng Việt, bảng thời gian lên trang tổng quan, lựa chọn
  qualification-check và tài liệu. Chuyển nhãn Docker xuống cuối tệp dựng để
  phiên bản mới không bắt cài lại thư viện chỉ vì đổi nhãn.
- Đến mốc này mới hoàn thiện triển khai và mã kiểm tra; chưa chạy thử đợt mới.

### 017 — Kết quả đợt đánh giá

- Kiểm tra logic đạt 97/97; web 8/8; đóng gói 2/2; cú pháp JavaScript đạt.
- WSL và Docker cùng chạy đủ 24/24 lượt đối chứng, không vi phạm tiêu chí.
  Trong mỗi ma trận: 18 lượt hoàn tất, 6 lượt dừng; không coi dừng là phôi đã sản xuất.
- Đo đúng hạn cấu hình 20 ms: nhánh MuJoCo không tính đủ 15/15 lượt đo sau làm nóng.
  Khi dùng hạn chức năng riêng 1 giây, tính đủ 15/15; không áp hạn rộng vào điều khiển.
- Báo cáo tiếng Việt và bảng số đo gốc: docs/bao_cao_danh_gia_20261102.md,
  output/docker/qualification-check_local_20261102 và đường dẫn trong docker/RELEASES.md.
- Chưa đổi ngưỡng điều khiển; các số chỉ mô tả ma trận và môi trường lần này.

### 018 — Môi trường và Docker thử nghiệm

- Ổ C gần đầy làm WSL báo không khởi động/không tìm thấy root khi bắt đầu đóng Docker.
- Dùng nén tại chỗ NTFS cho output và .venv: giữ nguyên tên/đường dẫn/nội dung,
  tiết kiệm khoảng 1,11 GB; không xóa kết quả hoặc ảnh Docker cũ. WSL chạy lại được.
- Ảnh candidate-20261102-qualification đã dựng; kiểm tra trong ảnh đạt và dấu kiểm tra
  nguồn khớp bản đang làm. Mã ảnh và bằng chứng lưu trong docker/RELEASES.md.
- Ảnh vẫn chờ người dùng nghiệm thu. Chưa có thay đổi hình học/hiệu chuẩn máy thật.
- Sau khi dựng ảnh, ổ C vẫn chỉ còn vài chục MB; cần giải phóng thêm trước đợt chạy lớn.

### 019 — Phát triển bài báo theo bằng chứng (03/11/2026)

- Dùng scientific-writing để rà phạm vi và nguồn, giữ xác nhận tác giả ở trạng thái chờ.
- Chuyển paper/ thành bản đang viết: main.tex ghép title_abstract.tex và body.tex.
- Viết lý thuyết thời gian dữ liệu, ước lượng theo lịch sử lệnh, dự báo/dừng, giảm tốc;
  bổ sung nghiên cứu trước, phương pháp và kết quả ảo dựa trên bằng chứng ngày 02/11.
- Sinh bảng từ hồ sơ JSON đã lưu; 24 lượt gồm 18 hoàn tất và 6 dừng, không phải
  24 phôi hoàn tất. Giữ kết quả MuJoCo chưa đạt hạn 20 ms, không điền hiệu năng tối ưu chưa chạy.
- Bốn mục kiểm chứng vật lý chỉ có tiêu đề/khoảng trống. Tên tác giả, đơn vị, tài trợ,
  xung đột lợi ích và phần công bố AI để người chịu trách nhiệm xác nhận.
- Thay bộ xuất abstract cũ bằng biên dịch LaTeX cho bản đang viết; xuất PDF sau khi kiểm tra bố cục.

### 020 — Rà soát bản thảo và PDF

- Làm rõ đối chứng bật/tắt cả mô đun tái cấu hình, gồm giới hạn tốc độ và dừng theo
  dấu hiệu bất thường; không mô tả là thí nghiệm chỉ thay riêng tốc độ.
- Kiểm tra nguồn/nhận định, 7 khóa tài liệu tham khảo, số bảng và phương trình;
  abstract 207 từ; thông tin tác giả và bốn mục vật lý chưa điền.
- Biên dịch LaTeX thật bằng Tectonic, khổ A4 một cột, 9 trang. Đã dựng ảnh các trang
  để xem bố cục; không có tham chiếu bỏ ngỏ hoặc khung chữ tràn lề trong log.
- PDF: reports/dt_cppps_manuscript_virtual.pdf; nguồn chuẩn đang viết: paper/.
  Bảng kết quả sinh từ bằng chứng đã lưu, không thay dữ liệu hay chạy lại để chọn số đẹp.
- Để trạng thái chờ tác giả xác nhận và chưa sẵn sàng nộp. Chưa ghi kết quả tối ưu
  MuJoCo mới vì hạng mục đó chưa có phép chạy hoàn tất bổ sung trong đợt viết bài này.
- Chỉ cập nhật bài báo/tài liệu; không thay mã điều khiển, hồ sơ vật lý hoặc ảnh Docker lõi.

### 021 — Viết đủ hạng mục tối ưu MuJoCo trước khi chạy (03/11/2026)

- O01: giữ ReferenceMuJoCoBeltPredictor làm bản gốc. Bản mới dùng rollout có sẵn
  trong MuJoCo để gom vòng lặp theo thời điểm dừng, một luồng, không thêm thư viện.
- Giữ XML, lưới vật lý, số kịch bản, cách chuyển sang băng dừng và thông số hiện tại;
  không đọc trạng thái thật của cảnh đang chạy. Kiểm tra thời gian trước/sau mỗi nhóm.
- O02: viết đối chiếu 12 trường hợp, thêm kiểm tra quỹ đạo từng bước, đầu vào lỗi,
  thời gian mô phỏng không tiến và quá hạn. Chưa chạy thử tại mốc ghi này.
- O03: ghép physics-check, tài liệu và kế hoạch Docker candidate mới. Chưa tự kết
  luận đạt 20 ms hoặc cập nhật thành tích vào bài báo khi chưa có kết quả.

### 022 — Đối chiếu bản gom một luồng và bổ sung thử số luồng

- 102 kiểm tra logic đạt. 12 trường hợp so bản gốc/bản gom một luồng có cùng
  hành động, số bước và biên; sai khác biên quan sát bằng 0. Quỹ đạo từng bước
  trong kiểm tra riêng cũng khớp trong ngưỡng so số học.
- Ở lượt đo WSL đầu tiên, trung vị tính đủ giảm khoảng 395 xuống 138 ms,
  nhưng 15/15 lượt đo với hạn 20 ms vẫn không tính đủ. Độ trễ khi trả dừng của
  bản gom cũng lớn hơn bản gốc vì không ngắt được giữa nhóm mã máy; không che hạn chế này.
- Bổ sung native_threads có thể nhập (1–16, mặc định 1). Viết kiểm tra bốn luồng
  và đối chiếu cả 1/4/8 luồng; chỉ đổi cách dùng CPU, không đổi vật lý hoặc giảm kịch bản.
- Hồ sơ 8 luồng là lựa chọn riêng; nhánh mặc định tính một chiều giữ nguyên.

### 023 — Kết quả bản có số luồng nhập được

- 103 kiểm tra logic đạt. Đối chiếu 12 đầu vào cho mỗi bản 1/4/8 luồng, không thấy
  sai khác biên và hành động trong ngưỡng đã định; không suy thành độ chính xác máy thật.
- Trong phép đo WSL kế tiếp, trung vị đầy đủ của bản gốc khoảng 408 ms; bản gom
  1/4/8 luồng lần lượt khoảng 134/49/44 ms. Các mẫu và p95 được giữ trong report.
- Ở hạn 20 ms, vẫn không có lượt đo nào tính đủ; không tăng hạn, không chọn xóa
  các lượt quá hạn. Đây là cải tiến tốc độ tính, chưa hoàn thành mục tiêu 20 ms.
- Bổ sung chặn quá hạn ngay khi tạo kết quả trả về; không tự ghi CONTINUE nếu
  thời gian tính nội bộ tại điểm tạo kết quả đã vượt hạn.

### 024 — Lỗi ghép hồ sơ và sửa tại nguồn

- Bộ đo/đối chiếu và 24 lượt hồi quy trong ảnh đầu đều đạt, nhưng chu trình dùng
  hồ sơ 8 luồng bị chặn trước khi chạy: bảng tham số chưa biết đơn vị native_threads.
- Bổ sung native_threads là thiết lập thiết kế không thứ nguyên trong bộ khai báo
  tham số chung, không đánh dấu là số đo vật lý. Thêm kiểm tra phân loại này.
- Giữ nguyên log lần lỗi; dựng lại ảnh và chạy lại các kiểm tra liên quan trước
  khi bàn giao. Không tính lần chu trình lỗi là một lượt hoàn tất hay dừng đạt tiêu chí.

### 025 — Bàn giao bản native sau kiểm tra lại

- Trong ảnh cuối: 103 kiểm tra lõi, bộ tích hợp, 12 trường hợp đối chiếu từng bản
  1/4/8 luồng và 24 lượt hồi quy đều đạt. Hồ sơ native 8 luồng ghép được vào chu trình.
- Chu trình native dừng do dự báo quá hạn, phôi còn hỗ trợ theo bộ chấm; không
  tính thành phôi hoàn tất. Hạn 20 ms vẫn chưa được đáp ứng.
- Báo cáo dễ đọc: docs/bao_cao_toi_uu_20261103.md. Các kết quả chưa đạt, lỗi ghép
  đầu tiên và các mức luồng đều được giữ. Mã ảnh/nguồn/bằng chứng ở docker/RELEASES.md.
- Không thay ảnh đã được người dùng nghiệm thu. Ảnh mới vẫn là candidate.

### 026 — Cập nhật bài báo theo bằng chứng tối ưu mới

- Bổ sung Native Rollout Optimization và bảng sinh từ ảnh cuối đã kiểm tra.
  Bảng 02/11 giữ nguyên, bảng 03/11 tách riêng; không trộn thời gian các đợt.
- Abstract 225 từ, PDF hiện 10 trang A4 một cột. Nêu cả việc cải thiện thời gian
  tính đầy đủ và chưa có lượt native tính đủ trong 20 ms. Bốn mục vật lý vẫn trống.
- Tác giả/đơn vị/công bố cần xác nhận vẫn chưa điền. Các nhận định mới gắn E004,
  nguồn API gắn E107; chưa tự đánh dấu được tác giả thẩm định hoặc sẵn sàng nộp.

### 027 — Viết đủ bộ dự báo nền trước khi thử (03/11/2026)

- B01: tạo một tiến trình MuJoCo riêng, chỉ một yêu cầu đang xử lý; hàng đợi có
  giới hạn. Bước điều khiển không đợi khởi tạo, kết quả, kết thúc hoặc đặt lại tiến trình.
- B02: gắn phiên/lượt khởi tạo, mã hồ sơ, ảnh chụp đầu vào, thứ tự mẫu và lần đổi lệnh;
  kiểm tra tuổi theo đồng hồ mô phỏng và theo đồng hồ cha riêng biệt. Chỉ nhận để quan sát.
- B03: ghép sau chặn lệnh của RuntimeCore, thêm log riêng và đảm bảo đóng tiến trình
  kể cả khi mô phỏng/đọc lại tệp bị lỗi. Nhánh nhanh vẫn quyết định; chưa áp lời khuyên nền.
- B04: viết kiểm tra giả lập định danh/tuổi/trạng thái, hàng đợi và lỗi; bộ thử chu trình
  có nhịp thời gian, đối chứng không chạy nền và trường hợp nền tính thiếu. Chưa chạy tại mốc này.
- Hồ sơ và thời gian giới hạn đều nhập được; không đổi hình học, ma sát, tốc độ máy
  hoặc hạn 20 ms của nhánh điều khiển. Kết quả nền chưa có quyền điều khiển/reset.

### 028 — Thử đối chứng tại WSL sau khi viết đủ các mục

- Đạt 110 kiểm tra logic và 2 kiểm tra ranh giới đóng gói.
- Ba chu trình có nhịp thời gian (tắt nền/bật nền/nền tính thiếu) đều đặt phôi;
  dấu vết thời gian mô phỏng, pha, lệnh và ước lượng giống nhau, mỗi chu trình 697 mẫu.
- Lần WSL: nhận 27 kết quả nền để quan sát; trường hợp ép tính thiếu có 81 kết quả
  bị loại vì thiếu. Bước lõi khi bật nền có p95 3,187 ms, lớn nhất 4,151 ms;
  không mẫu nào vượt 20 ms trong lần đo này. Không suy thành bảo đảm thời gian thực.
- Dừng cưỡng bức tiến trình nền trong bộ thử vẫn gọi được bước nhánh nhanh;
  các tiến trình đều đóng khi kết thúc. Tệp gốc ở output/docker/background-check_local_20261103.

### 029 — Kiểm tra trong Docker và lưu hồ sơ bản giao

- Ảnh candidate-20261103-background-observer đạt 110 kiểm tra lõi, bộ tích hợp,
  đặt lại (15 trường hợp bản tin, 2 lượt MuJoCo) và 24 lượt hồi quy, không lỗi tiêu chí.
- Ba chu trình Docker đều đặt phôi, dấu vết đối chiếu giống nhau. Nhận 34/35 yêu cầu
  nền để quan sát; 1 kết quả bị loại vì trạng thái vận hành đã đổi. Nền ép tính thiếu
  có 81 dự báo thiếu bị loại và 1 kết quả bị loại vì trạng thái đã đổi.
- Bước lõi bật nền p95 3,505 ms, lớn nhất 12,629 ms, 0/697 mẫu vượt 20 ms.
  Chỉ là số đo một lần chạy, không gồm cơ học/I/O/khởi tạo và không bảo đảm thời gian thực.
- Giữ nguyên mã ảnh đã nghiệm thu và các candidate trước. Mã băm nguồn khớp ảnh;
  RELEASES.md lưu mã ảnh và bằng chứng. Ảnh mới vẫn chờ người dùng nghiệm thu.
- Có báo cáo dễ đọc, hướng dẫn chạy, tham số sửa được, và thêm chế độ kiểm tra vào
  GitHub Actions. Chưa kết luận một lượt CI từ xa đã đạt nếu chưa đọc kết quả từ xa.

### 030 — Bổ sung bản thảo và tài liệu bàn giao

- Giữ nguyên tệp title/abstract riêng. Bổ sung mục dự báo nền chỉ quan sát và bảng
  sinh từ hồ sơ Docker mới, gắn nguồn E005. Bản PDF hiện 11 trang A4, abstract 225 từ.
- Các mục kiểm chứng máy thật vẫn trống. Nêu rõ mỗi điều kiện chỉ có một chu trình;
  697 bước không phải 697 lượt sản xuất độc lập. Chưa ghi tốc độ/độ chính xác vật lý.
- Đã kết xuất và xem bố cục các trang; sửa dòng tràn lề, kiểm tra tham chiếu LaTeX.
  Tác giả/đơn vị và xác nhận học thuật vẫn chờ người chịu trách nhiệm điền.
- Gói nguồn kèm hồ sơ, báo cáo, hướng dẫn và mã băm; không thay ảnh đã nghiệm thu.

### 031 — Thay hai nguồn không phải bài báo bằng tài liệu đã công bố

- Theo yêu cầu người dùng, bỏ mục 7 cũ (kho mã dự án) và 8 cũ (hướng dẫn API MuJoCo),
  gỡ trích dẫn tương ứng trong nội dung. Hồ sơ mã nguồn và bằng chứng nội bộ vẫn giữ.
- Thêm 6 bài đã công bố của Negri, Uhlemann, Cimino, Jones, Fuller và Rasheed;
  danh mục mới 12 bài. Đối chiếu DOI/tác giả/năm/trang bằng Crossref và nguồn gốc.
- Viết thêm ba đoạn tổng quan: đồng bộ/cảm biến; đặc tính và độ chi tiết mô hình;
  dịch vụ và tích hợp điều khiển. Nêu phạm vi phát triển cụ thể, không tự nhận cả
  lĩnh vực chưa có ai giải quyết. Abstract và số liệu thử nghiệm giữ nguyên.
- Lưu nguồn và phạm vi hỗ trợ E108-E113; các mục vật lý vẫn trống, tác giả vẫn chờ điền.

### 032 — Viết bộ đối chiếu dự báo ngoại tuyến trước khi thử

- Đọc ảnh đầu vào đã ghi của từng yêu cầu nền, đối chiếu phiên, hồ sơ, thời điểm,
  số mẫu và số kịch bản. Tính lại mô hình 1D với cùng dữ liệu; không đọc đáp án vật lý.
- Tách kết quả nhận/loại khi chạy, bản ghi sai và dự báo thiếu. Không coi HOLD do
  hết hạn là một dự báo hoàn chỉnh đồng ý với mô hình còn lại.
- Xuất bảng dễ đọc, từng cặp và mã băm tệp. Không thay nhánh điều khiển hoặc tham số.
- Viết kiểm tra định danh, kết quả thiếu, bất đồng, tệp sai và không sửa nguồn;
  ghép vào background-check. Mốc này chưa chạy kiểm tra các mục mới.

### 033 — Kiểm tra đối chiếu và lưu kết quả có giới hạn

- Lần chạy kiểm tra Windows bị chặn quyền thư mục tạm (8 lỗi; 6 kiểm tra cần MuJoCo
  bị bỏ qua). Không tính là đạt. Chạy trong WSL và trong Docker đều đạt 116 kiểm tra.
  Hai kiểm tra đóng gói Windows đạt khi dùng thư mục tạm trong workspace.
- Đọc lại nhật ký Docker trước được 35 cặp; lần Docker mới có 24 cặp (22 nhận,
  2 bị loại khi chạy), cùng khuyến nghị ở cả 24. Hai đợt được ghi riêng.
- Lượt ép tính thiếu có 82 dự báo không được đưa vào mẫu số so khuyến nghị.
  Không gán tỷ lệ này thành độ chính xác vật lý hoặc số lượt sản xuất độc lập.
- Ba chu trình mới đều đặt phôi và có dấu vết điều khiển giống nhau; bộ tích hợp đạt.
- Giữ mẫu vượt hạn: lượt ép tính thiếu có 1/697 bước lõi trên 20 ms, lớn nhất
  32,749 ms. Chưa bảo đảm thời gian thực. Không thay thuật toán/hạn để làm số đẹp.
- Docker model-audit vẫn candidate. Nguồn khớp mã băm trong ảnh, các ảnh cũ giữ nguyên.

### 034 — Tài liệu và bản thảo theo kết quả mới

- Bổ sung mục Offline Model-Decision Audit, nguồn E006, phân biệt đọc lại mô hình
  với quyết định thật khi chạy. Nêu đủ 24 cặp, 82 kết quả thiếu và mẫu vượt 20 ms.
- Giữ 12 trích dẫn bài báo đã công bố, không khôi phục hai nguồn số 7/8 cũ.
  Title/abstract riêng không đổi; các phần kiểm chứng vật lý và tác giả vẫn chưa điền.
- Xuất lại PDF, kiểm tra tham chiếu và sửa dòng tràn lề; lưu nhật ký và gói nguồn
  mới cho việc kiểm nghiệm. Chưa tự đánh dấu người dùng đã nghiệm thu.

### 035 — Chốt và viết bộ nghiên cứu giới hạn trước khi chạy

- Kế hoạch 144 đầu vào cố định: khoảng cách cuối băng, tốc độ, tuổi dữ liệu và
  hệ số nhân ma sát trượt. Giá trị giả định tách khỏi hồ sơ máy, không hiệu chỉnh tự động.
- Tách chấm biên dọc khỏi chấm dọc/ngang/cao trong hai bản cùng động lực học tiếp xúc;
  đối chiếu với 1D để không lẫn hai nguyên nhân khác biệt. Không đổi predictor điều khiển.
- Viết bộ chạy, giữ từng kết quả và lỗi, tổng hợp có mẫu số rõ; kiểm tra bất biến
  biên đầy đủ không lớn hơn biên chỉ dọc. Viết kiểm tra kế hoạch và phân loại kết quả.
- Mốc này chưa chạy lưới; không giả định trước có bất đồng hoặc mô hình nào đúng.

### 036 — Đợt thăm dò đầu tiên và kế hoạch kiểm tra độ nhạy

- Đợt WSL tính đủ 144 đầu vào, không lỗi bất biến; có 138 cặp cùng khuyến nghị,
  3 cặp 1D chạy/MuJoCo dừng và 3 cặp ngược lại. Hai cách chấm tiếp xúc chưa làm đổi
  hành động trong lưới này; không suy thành ngang/cao luôn không cần thiết.
- Sau khi thấy 6 bất đồng, ghi riêng kế hoạch lưới con 24 đầu vào ở khoảng 15/20 mm,
  tốc độ 0,08/0,24 m/s, giữ các tuổi dữ liệu và ma sát. Chạy bước 1/2/4 ms, giữ
  chu kỳ điều khiển 20 ms. Đây là kiểm tra sau khi xem kết quả, không phải xác nhận độc lập.
- Không điều chỉnh hệ số dừng 1D hoặc hệ số ma sát để làm hai mô hình khớp nhau.

### 037 — Kiểm tra Docker và độ nhạy bước tính

- Docker đạt 119 kiểm tra lõi, lưới 144 đầu vào và bộ tích hợp; 2 kiểm tra đóng gói đạt.
  Lần WSL/Docker có cùng hành động và biên trong dung sai 10⁻⁹ m, sai khác lớn nhất 0.
- Lưới con 24 đầu vào chạy đủ ở 1/2/4 ms. Sáu bất đồng đầu vẫn có; thêm một trường
  hợp đổi dấu: biên tiếp xúc −0,140/+0,035/+0,422 mm theo ba mức bước.
- Không gọi đây là chứng minh hội tụ: lượng tử hóa thời điểm phản ứng cũng thay đổi,
  mô hình tiếp xúc chưa hiệu chuẩn. Không dùng mức bước nhỏ nhất làm đáp án máy thật.
- Lưu kế hoạch bổ sung, từng đầu vào và mã băm; báo cáo dễ đọc có ví dụ tính 1D.
  Ảnh mới vẫn candidate, không thay ảnh đã nghiệm thu hoặc đưa ảnh lên registry.

### 038 — Viết kết quả nghiên cứu vào tài liệu

- Báo cáo tiếng Việt ghi đủ sáu bất đồng, ví dụ tính khoảng dư 1D, lưới con và
  đầu vào đổi dấu theo bước tính. Không chuyển 138/144 thành độ chính xác mô hình.
- Bổ sung mục Exploratory Boundary and Step-Size Sensitivity, bảng sinh từ bằng
  chứng E007. Ghi rõ lưới con được chọn sau khi xem kết quả và chưa chứng minh hội tụ.
- Giữ title/abstract riêng, 12 trích dẫn bài báo; phần kiểm chứng vật lý vẫn trống.
  PDF bản thảo hiện 14 trang A4, đã kiểm tra bảng mới và tham chiếu, không tràn lề.
- Đóng gói mã và kế hoạch sửa được cùng hướng dẫn; các kết quả và ảnh cũ được giữ.

### 039 — Viết đủ bản phần mềm chuẩn bị đo máy trước khi thử

- S01/S02: cổng UDP loopback dùng bảng ánh xạ và RuntimeCore, tự ghi thời điểm nhận;
  chặn gói lỗi/sai phiên/lặp, vẫn gọi kiểm tra im lặng. Chỉ ghi lệnh tệp.
- S03: bộ gửi gói thử thực trên cùng máy; mất dữ liệu rồi trở lại, gói lỗi/lặp,
  bảng chưa xác nhận. Không giả có trình đọc S7 hay phản hồi máy thật.
- S04: trang tổng quan đọc thêm báo cáo dữ liệu mẫu, đối chiếu và kiểm tra tổng hợp.
- S05/S06: bảng sáu mục, kiểm kê trước khi chạy mọi nhóm kiểm tra; giữ cấu hình,
  tham số chỉnh được và hướng dẫn. Mốc này chưa chạy kiểm tra bản mới.
- Phần đo/hiệu chuẩn vật lý để sau theo yêu cầu người dùng; không tự nâng candidate
  thành ảnh nghiệm thu hoặc thay vai trò điều khiển của MuJoCo nền.

### 040 — Kiểm tra v2 và sửa dữ liệu thử

- Lần WSL chạy đủ tám nhóm nhưng kiểm tra lõi có một lỗi: dữ liệu thử gói hỏng
  dùng nhiều lần cùng thời điểm, trái yêu cầu thời gian tăng dần của tái cấu hình.
  Sửa dữ liệu thử; không sửa ngưỡng hoặc bỏ phép kiểm tra. Giữ thư mục lần chưa đạt.
- Năm kiểm tra riêng cổng mẫu đạt sau sửa. Ba thử UDP loopback thật đạt cả ở WSL
  và Docker: mất dữ liệu rồi trở lại, gói sai/lặp, bảng chưa xác nhận.
- Docker cuối đạt toàn bộ tám nhóm: 126 kiểm tra lõi, 8 kiểm tra web, stream,
  tích hợp, đặt lại, nền, lưới biên và 24 lượt đối chứng. Không suy thành máy thật đã đạt.
- Xem trực tiếp trang tổng quan: sáu mục mới, báo cáo mới đạt và lần cũ chưa đạt
  đều hiển thị đúng. JavaScript qua kiểm tra cú pháp; 2 kiểm tra đóng gói đạt.
- Chưa có trình đọc S7 và kết nối/ghi PLC thật. Các số đo, địa chỉ và xác nhận ngoài
  máy tính vẫn để sau; hồ sơ đầu vào giữ trạng thái chưa xác nhận.

### 041 — Hồ sơ bàn giao và bản thảo phần mềm v2

- Lưu ảnh candidate, mã băm nguồn, tám nhóm kiểm tra và lần chưa đạt trong bằng chứng.
  Mọi ảnh đã có giữ nguyên; chưa cấp nhãn accepted/stable/latest.
- Bổ sung phần Pre-Hardware Software Rehearsal vào bài báo, gắn E008; không gọi UDP
  là trình đọc S7 hoặc đồng bộ PLC. Giữ title/abstract và 12 trích dẫn đã công bố.
- Cập nhật hướng dẫn người mới, danh mục mô đun, GitHub Actions và gói nguồn.
  Các phần đo bên ngoài để sau; chưa đánh dấu toàn bộ hệ thống đã nghiệm thu.

### 042 — Người dùng chấp thuận bản phần mềm v2

- Ngày 03/11/2026, người dùng xác nhận: “ok tất cả mọi thứ đều ổ, hãy cập nhật vào docker”.
  Áp dụng cho bản phần mềm v2 vừa bàn giao, không suy thành đã kiểm chứng vật lý.
- Chuẩn bị nhãn accepted-20261103-software-v2 trỏ đúng ảnh đã được xem; chạy lại
  tám nhóm trong container và đối chiếu mã băm trước khi gắn nhãn.
- Lệnh chạy chọn bản accepted; lệnh build và CI vẫn chỉ dựng candidate. Giữ ảnh
  đã nghiệm thu trước đây, các candidate và hồ sơ nguồn gốc, không dựng lại v2 để đổi mã ảnh.

### 043 — Đã cập nhật Docker sang bản chấp thuận

- Chạy lại tám nhóm trong đúng ảnh v2: 126 kiểm tra lõi, 8 web, ba trường hợp UDP,
  tích hợp, đặt lại, nền, 144 đầu vào biên và 24 lượt đối chứng đều đạt.
- Đã ghi lời chấp thuận, mã ảnh, mã băm nguồn và kiểm tra trước khi tạo nhãn
  accepted-20261103-software-v2; sau đó kiểm tra nhãn trỏ đúng mã ảnh đã được xem.
- Các ảnh cũ, kể cả accepted-20261030-core-v1, giữ nguyên. Không đẩy ảnh ra registry.
- Thử lệnh PowerShell mặc định sau khi gắn nhãn: demo hoàn tất và chấm đặt phôi đạt
  trong mô phỏng có giả định vòng hở. Không chuyển thành kết quả vật lý.
- Nhãn tại thời điểm dựng vẫn ghi candidate như lịch sử; trạng thái chấp thuận
  hiện tại và mã băm được lưu riêng ở docker/evidence/accepted-20261103-software-v2.json.

### 044 — Hai hạng mục phần mềm tiếp theo (04/11/2026)

- Phát lại phiên UDP qua chính StreamCore, dùng thời điểm nhận và từng nhịp đã lưu,
  kể cả im lặng; so kết quả logic và lệnh cuối, bỏ riêng thời gian tính toán khỏi phép so.
- Chặn nguồn khác mã băm, gói không có nhịp tương ứng, thiếu lệnh cuối và cấu hình
  dự báo nền bất đồng bộ chưa hỗ trợ. Khác kết quả được báo và lưu, không tự sửa.
- Đóng gói đúng sáu tệp phiên kèm mã băm; kiểm tra ZIP không giải nén, chặn tên lạ,
  trùng tệp, vượt kích thước, sai nội dung và không ghi đè gói đã tồn tại.
- Bổ sung thử tự động, chế độ stream-archive-check và nhóm thứ chín vào kiểm tra chung.
  Có hướng dẫn người mới tại docs/phat_lai_va_dong_goi_phien.md. Không đổi tham số máy.
- Dùng ponytail, chỉ thư viện chuẩn và lõi có sẵn. Chưa đổi bản Docker đã nghiệm thu.

### 045 — Kiểm tra và bàn giao hai hạng mục mới

- Docker đạt đủ chín nhóm: 132 kiểm tra lõi, 8 web, cổng mẫu, tích hợp, đặt lại,
  nền, lưới 144 đầu vào, 24 lượt đối chứng và phát lại/đóng gói.
- Ba phiên UDP thật trên loopback phát lại 34 nhịp mỗi phiên (102 nhịp), không khác
  kết quả logic; ba ZIP qua kiểm tra. Sáu phép thử mới có cả sửa lệnh, sửa dữ liệu,
  sai mã nguồn, tên ZIP lạ/trùng, không ghi đè, thiếu lệnh cuối và cấu hình chưa hỗ trợ.
- Hai kiểm tra đóng gói nguồn, cú pháp PowerShell/JavaScript và đọc chẩn đoán mới đạt.
  Lần chạy thử trên Windows bị quyền thư mục tạm chặn; WSL và Docker chạy được.
- Lưu hồ sơ candidate-20261104-stream-evidence gồm mã ảnh, mã băm nguồn và kết quả.
  Đối chiếu 16 nhãn cũ vẫn nguyên. Giữ accepted-20261103-software-v2 làm mặc định.
- Chỉ thử ba phiên dữ liệu ngắn, chưa qua TRACK có dự báo. Không tuyên bố độ chính xác
  vật lý, khả năng phát lại mọi cấu hình hoặc đồng bộ CAD/MuJoCo. Không gửi lệnh PLC.

### 046 — Nghiên cứu phát lại khi đã vào pha dự báo

- Nhật ký thêm ước lượng và toàn bộ kết quả dự báo; khi so chỉ bỏ thời gian tính.
  Có danh sách trường khác nhau để truy tìm nhịp bắt đầu lệch.
- Kế hoạch sáu ca, lặp ba lần, phát lại hai lần/phiên. Plant MuJoCo chạy vòng kín
  với tín hiệu số, lịch gói thử và ngưỡng hiện tại; không truyền UDP hoặc đi qua PLC.
- Lần đầu bị lỗi ghi vì C đầy và lỗi đổi giây/mili giây của dữ liệu thử. Giữ lần dở
  trên D. Nguồn thử dùng giây trực tiếp; không nới chặn thời gian của lõi.
- Docker candidate-20261104-predictive-replay đạt chín nhóm và nghiên cứu. Kết quả
  đầy đủ ở D:/DT_CPPS_Experiments/20261104/candidate_predictive_replay; đây là ảnh
  trước khi chuyển bảng CAD và bỏ Unity, không gán kết quả đó cho ảnh dựng sau.

### 047 — Chuyển dữ liệu chính sang D và dọn C

- Sao chép, đối chiếu SHA-256 đủ 26.579 tệp cùng trạng thái Git/chỉnh sửa chưa commit
  từ C:/Users/Admin/Documents/ChatGPT/plc sang D:/Projects/network-aware-production-twin.
- Dọn các bản thư mục lớn cũ sau kiểm tra, tạo liên kết từng thư mục để Codex đang
  mở vẫn hoạt động. Còn tệp gốc nhỏ tương thích và cache bị Windows khóa quyền.
- Xóa riêng cache tải pip/http và npm/_cacache có thể tạo lại; giữ các gói cài và _npx.
  Không dọn bừa dữ liệu Temp/Downloads. Bảng kiểm kê và mã băm lưu ngoài kho nguồn.

### 048 — Bỏ Unity theo chỉ đạo mới

- Bỏ nguồn Unity, scene, C#, vật liệu, script xuất cũ và dự án Unity riêng/Library.
- Giữ bảng hình học 113 chi tiết với SHA-256 không đổi, chuyển sang cad_reference;
  đổi các trình dựng MuJoCo, CAD Viewer, Docker, CI và đóng gói sang đường dẫn mới.
- Thay trình xuất cũ bằng export_cad_parts.py chỉ dùng thư viện chuẩn. Tạo lại bảng
  cho kết quả giống mã băm cũ; hình học chưa tự thay thành CAD V5.
- Bộ duyệt tự động chặn xóa hàng loạt ZIP hỗn hợp; dùng phương án an toàn hơn: chuyển
  nguyên trạng ra kho D:/DT_CPPS_Archives/20261104, giữ CAD/lõi DT và mã băm đối chiếu.
- Không sửa chứng cứ/lịch sử Docker cũ hoặc tự đổi nhãn đã nghiệm thu.

### 049 — Chuyển cả môi trường WSL/Docker và kiểm tra lại

- Di chuyển chính thức Ubuntu-24.04 sang D:/WSL/Ubuntu-24.04, không export/unregister.
  Đĩa đã dừng 20.533.215.232 byte có SHA-256 trùng trước/sau khi chuyển, trước lần boot mới.
- Sau khởi động: 19 ảnh Docker cũ và phiên bản Python 3.12.3/MuJoCo 3.16.0/NumPy 2.5.4
  giữ nguyên. Ổ C có lại hơn 20 GB trống; nguồn/kết quả lớn và môi trường chạy đều trên D.
- Candidate MuJoCo-only đạt đủ chín nhóm, 135 kiểm tra lõi và 8 web; 2 kiểm tra giao hàng
  cũng đạt. Demo sau di chuyển DONE/đặt phôi đạt với giả định vòng hở, 13,92 giây mô phỏng.
- Bộ dựng legacy dùng CSV mới biên dịch được; XML trùng nội dung template gốc, khác
  cách xuống dòng Windows/Linux. Không ghi đè template hoặc chỉnh tham số cơ khí.
- Nguồn ảnh được đối chiếu mã băm. Giữ nguyên nhãn accepted cũ; chưa nghiệm thu ảnh mới.

### 050 — Phân tích phản ứng và khả năng tách nguyên nhân mạng

- Thêm bộ đọc audit_response.py: đối chiếu đủ 18 phiên, mã băm nguồn sinh dữ liệu,
  cấu hình/bảng tín hiệu, số gói/nhịp và mốc HOLD thực tế; xuất JSON, CSV và báo cáo.
- Tách thời gian từ lúc áp dụng tình huống và từ gói hợp lệ cuối; chặn gói cùng nhịp
  không được diễn giải là CPU xử lý mất 0 giây. Chuẩn hóa riêng tên phiên khi so cặp.
- Bộ cũ: giảm tốc sau 20 ms, trễ dài/mất gói HOLD sau 100 ms từ mốc; ba cặp giống
  đầu vào/quyết định tới lúc dừng. Không kết luận đã tách hai nguyên nhân hoặc đạt
  độ chính xác phát hiện lỗi vật lý. Gốc dữ liệu giữ riêng, không sửa để khớp kết luận.

### 051 — Sửa biên thời gian im lặng dùng chung

- Thử đúng ảnh cũ xác nhận ba trong sáu mốc đồng hồ chưa dừng tại ngưỡng do sai số
  số thực; sau thêm một nhịp 20 ms đều dừng. Không coi đây là đo tốc độ phần cứng.
- Sequence.watchdog và SignalHealth dùng cùng elapsed_at_least với dung sai số học
  tuyệt đối 1 ns. Không đổi ngưỡng im lặng 100 ms hoặc tham số cơ khí/profile.
- Ba kiểm tra mới: sáu mốc có cùng phản ứng tại ngưỡng và giữ hút; trước ngưỡng
  một micro giây chưa dừng; dung sai không phình theo trị tuyệt đối của đồng hồ.
- Hoàn thiện các mục rồi dựng candidate-20261104-time-boundary; chạy lại toàn bộ
  nhóm, nghiên cứu sáu ca và bộ đối chiếu trước/sau. Chưa tự đổi nhãn nghiệm thu.

### 052 — Kết quả đối chiếu trước/sau và bàn giao nghiên cứu

- Candidate time-boundary đạt chín nhóm: 141 kiểm tra lõi, 8 web; nghiên cứu 18 phiên,
  36/36 phát lại cùng kết quả logic; đối chứng ép quá hạn vẫn được phát hiện.
- Trễ dài/mất gói: giảm tốc sau 20 ms; HOLD từ 100 xuống 80 ms tính từ mốc đầu thiếu
  dữ liệu; tương ứng 120 xuống 100 ms tính từ gói hợp lệ cuối. Không đổi ngưỡng 100 ms.
- Ba cặp trễ dài/mất gói có cùng đầu vào và quyết định tới lúc dừng; không gọi đây là
  tách được nguyên nhân hoặc độ chính xác vật lý. Mô hình/profile giữ nguyên mã băm.
- Hai tệp điều khiển cũ thay đổi là sequence.py và health.py, dùng chung clock_checks.py.
  Các tệp còn lại thêm bộ đọc/kiểm tra; ghi đủ nguồn, ảnh và bằng chứng trước/sau.
- Có báo cáo dễ hiểu, CSV từng phiên và hướng dẫn chạy; không tự chấp thuận Docker.

### 053 — Nghiên cứu cảm biến so với mất chuyển động

- Tạo bảy ca, ba lượt mỗi ca: bình thường; PS1 không báo/băng cấp phôi đứng;
  PS3 không báo/băng dọc đứng sau PS2; PS3 luôn báo; PS2 không báo.
- Core chỉ nhận SensorModel frame; nhãn lỗi, ép băng tải ở plant và vị trí phôi
  không đi vào bộ ước lượng. Tách issued command và applied command bằng bản sao.
- Hoàn thiện bộ thử, kế hoạch sửa được và hai kiểm tra ranh giới rồi dựng candidate.
  Lõi/ước lượng/profile cũ giữ nguyên mã băm; không đổi tham số để làm ca đạt.

### 054 — Kết quả và phân tích độc lập

- Đủ 21 ca; sáu cặp cùng quan sát/quyết định tới dừng, nhưng vị trí phôi chênh
  khoảng 35,4 cm ở cấp phôi và 24,8 cm ở cặp điểm gắp. Không khẳng định tách được lỗi.
- Thời gian từ chèn tới dừng: 2,22 s ở cấp phôi, 1,56 s ở cặp điểm gắp, 1,8 s
  khi PS2 không báo. PS3 luôn báo bị chặn cùng nhịp. Đây không phải thời gian CPU.
- Phân biệt mốc chèn với lần đầu cảm biến đưa sai bit so với tia lý tưởng: bộ chấm
  đo thêm 200/320/1.640 ms tương ứng PS1/PS3/PS2; mốc lý tưởng không đưa vào DT.
- 143 kiểm tra lõi, 8 web, tích hợp và 2 kiểm tra giao hàng đạt. Chấm vị trí hỗ trợ
  sau dừng đạt 21/21 trong mô phỏng; không chuyển thành chứng nhận an toàn vật lý.
- scripts/analyze_sensor_drive.py tính lại sáu cặp và kiểm tra hàng/dấu thời gian;
  lưu JSON/hash nguồn và báo cáo tiếng Việt. Docker vẫn candidate, không đẩy ảnh.

### 055 — Khép nhãn trong metadata và chạy lại bản cuối

- Đổi context phiên thử sang UUID mặc định của RuntimeCore để tên phiên không
  chứa loại lỗi. Phiên pilot chỉ dùng ID để chặn sai phiên, nhưng vẫn giữ riêng
  ảnh/dữ liệu cũ thay vì viết đè lịch sử.
- Chạy lại đủ 21 ca bằng candidate-20261104-sensor-drive-v2; xác nhận 21 UUID4
  khác nhau. Cả 21 chuỗi quan sát và 21 chuỗi quyết định logic giữ nguyên so với
  pilot, sau khi bỏ riêng thời gian tính dự báo khỏi phép so.
- Bản cuối đạt 143 kiểm tra lõi, 8 web và tích hợp; chấm vị trí hỗ trợ 21/21 và
  tính lại sáu cặp. Không đổi mã lõi/ước lượng, profile hoặc nhãn accepted.


### 056 — Cài Anatomy và làm hình tương tác giải thích hệ DT (2026-11-05)

- Cài skill Anatomy từ wheresryan22/anatomy bằng công cụ cài skill của Codex; đọc hướng dẫn và ví dụ đồng hồ đo, giữ bộ vẽ MIT trong dự án để chuyển máy không cần cài skill lại.
- Chọn hình cỡ Figure, liệt kê các nhóm đế/khung, băng tải, hộp, robot, cảm biến, chi tiết đỡ; hoàn thành 67 khối SVG. Không thêm bộ máy vật lý mới: lấy hình học hộp từ XML MuJoCo đã đánh giá.
- Xuất đúng 1.973 mẫu của bảy ca lượt 01, kiểm tra thời gian và SHA-256 30 tệp nguồn; phôi thực, bit nhận, ước lượng, lệnh, tốc độ áp dụng và lý do HOLD cùng một mẫu.
- Thêm chọn ca, phát/dừng, tua, tới HOLD lần đầu, đối chiếu hai cặp cảm biến/mất chuyển động, hai nền, phím và chế độ giảm chuyển động. Bấm từng bộ phận hoặc sáu bước đọc giải thích tiếng Việt.
- Tách vị trí thật chỉ phục vụ người xem; không đưa vào DT. Không tự diễn hoạt robot/đầu đẩy bằng lệnh vì nhật ký không có vị trí khớp thực. Ghi rõ ba mốc PS1/PS2/PS3, giới hạn hình học, không chèn lỗi mạng và thiếu xác nhận để gắp.
- Kiểm tra: hai phép kiểm tra dữ liệu mới; tổng 10 kiểm tra web trong Docker đạt. Trình duyệt kiểm tra 21 tư thế đại diện, chức năng và ảnh nền sáng/tối, điện thoại 390 px, phóng to 4×; không lỗi JavaScript/tràn ngang trong ảnh kiểm tra. Sửa lỗi đóng thẻ script nhúng, thanh tua tự trả về mẫu cũ, thứ tự khối che phôi, độ tương phản nền tối trước khi chốt.
- Dựng candidate-20261105-anatomy, ghi ID/hash trong docker/RELEASES.md và bằng chứng JSON. Đối chiếu 113 tệp MuJoCo không đổi; không chạy lại thí nghiệm vật lý hoặc đổi bản accepted. Chưa có nghiệm thu người dùng cho mục này.
- Có hướng dẫn mở ngoại tuyến/dựng lại ở docs/truc_quan_anatomy.md và liên kết từ trang tổng quan. Máy chủ cục bộ cổng 8766 chỉ nghe localhost; trang không điều khiển PLC.


### 057 — Tinh giản và khóa lại mục tiêu nghiên cứu (2026-11-05)

- Viết lại README thành bản đồ ngắn của mục tiêu phát hiện sai lệch, lượng hóa
  bất định và chọn cấu hình; tách rõ phần đã có với phần chưa chứng minh.
- Đã lưu ZIP ngoài dự án, đọc lại và kiểm tra SHA-256 từng tệp trước khi xóa:
  731 tệp, 124.529.752 byte nội dung (~118,8 MiB), gồm bản thảo trùng, bảy PDF
  cũ, script khả thi cũ, gói kiểm tra giải nén/preview/skill tạm và hai tài liệu cá
  nhân. Đã xóa thư mục rỗng của các mục này; không xóa kết quả bất lợi.
- Giữ nguồn bài duy nhất ở paper/, PDF hiện hành và hai hướng dẫn nhập môn;
  giữ công cụ LaTeX/tài liệu trích dẫn còn dùng, CAD, lõi, profile, dữ liệu và
  ảnh Docker lịch sử. Biên bản ở docs/don_du_an_20261105.md.
- Có hướng nghiên cứu hiện tại và các tiêu chí đối chứng, tập hiệu chuẩn/kiểm
  tra riêng. Chưa mặc định dùng camera/RL hoặc coi ML đã triển khai.

### 058 — Bộ sai lệch dự đoán–quan sát độc lập

- Thêm EventResidual: mốc PS2 vật lý, lịch sử lệnh và khoảng gain/drift sửa được
  dự đoán miền vị trí; kiểm tra cạnh PS3 đến sớm/muộn hoặc không đến như dự kiến.
- Không nhận pose, tốc độ thật, nhãn lỗi; không lấy ước lượng đã sửa từ PS3 để
  kiểm tra ngược PS3. Lệnh hiện tại được ghi sau quan sát cùng nhịp.
- Tách trạng thái thiếu mốc/thiếu tín hiệu/dữ liệu cũ; không đổi null thành false,
  không tự bỏ cảm biến, không xóa HOLD, không ghi PLC. Bộ mới chỉ cố vấn ngoại tuyến.
- Bốn kiểm tra mới cho biên thời gian, tham số, miền sai số, thiếu/cũ dữ liệu,
  xác nhận nhiều mẫu và phát hiện cạnh đến sớm. CI chạy thêm bộ này.

### 059 — Kết quả nguyên trạng và candidate

- Phát lại 21 phiên đã có với hai miền giả định khóa trước. Miền hẹp báo cặp
  PS3 không báo/băng dọc đứng ở 6,84 s; timeout một sự kiện +0,2 s ở 6,86 s.
  Miền rộng của profile chưa báo trước HOLD cũ 6,96 s. Đây không phải bằng
  chứng hơn bộ điều khiển truyền thống hoặc tăng năng suất.
- Bình thường có 63/63 mẫu sau mốc nằm trong khoảng; ca PS3 không báo nhưng
  băng vẫn chạy 79/79. Mất chuyển động: chỉ 4/79 hoặc 5/79 mẫu trong khoảng.
  Không đổi các số này thành mức tin cậy 95% hoặc độ chính xác phân loại.
- Docker candidate-20261105-residual-focus đạt 147 kiểm tra lõi, 10 web; hai
  kiểm tra giao hàng trên host đạt. 113 tệp MuJoCo trước đó và bản accepted
  giữ nguyên. Receipt có ID ảnh, mã băm nguồn/đầu vào và kết quả đầy đủ.
- Pilot/final khớp mọi giá trị JSON. Kiểm tra byte ban đầu vướng CRLF/LF; kiểm
  tra đường dẫn vướng ánh xạ volume /app/output sang output/docker. Đã sửa
  phần kiểm tra và ghi nhận, không đổi dữ liệu hoặc chạy lại để chọn kết quả.
- Chưa có ML huấn luyện, can thiệp điều khiển mới, thử kín khôi phục hay đo vật
  lý. Tiếp theo là hiệu chuẩn/kiểm tra miền dự đoán trên điều kiện biến thiên,
  rồi đối chứng chính sách tái cấu hình cùng thông tin và ngân sách tính.


### 060 — Tập hiệu chuẩn và tập kiểm tra riêng cho miền dự đoán

- Tạo bệ thử đoạn PS2→PS3, không để HOLD chu trình cũ cắt ngắn dữ liệu; không
  gọi đây là chu trình gắp–thả hoặc có quyền điều khiển PLC.
- Chín điều kiện bình thường dùng fit miền gain từ khoảng cách mốc và tích phân
  lệnh. Không lấy pose hoặc hệ số thật. Niêm phong JSON/SHA-256 trước 28 ca giữ
  riêng: tám bình thường, 16 lỗi và bốn ca ngoài miền.
- Có hai kiểm tra mới: tách điều kiện, tập hợp ca cố định, fit chỉ từ sự kiện,
  dữ liệu thiếu/không hợp lệ và giới hạn kích thước/thời gian kế hoạch.
- Các tham số và lưới điều kiện nằm trong JSON, không sửa profile điều khiển cũ.

### 061 — Đối chiếu nguyên nhân cải thiện và giới hạn

- Trên tám ca bình thường, các miền đều không báo nhầm, bao phủ 766/766 mẫu sau
  mốc; không gọi đây là độ tin cậy thống kê. Bộ fit báo 16/16 ca lỗi trong cửa
  sổ, nhưng chậm hơn timeout một sự kiện 160–260 ms. Miền profile cũ chưa báo.
- Sau pilot bổ sung phép so cùng drift để tách giả định đặt trước với phần fit.
  Ghi rõ đây là phân tích bổ sung, không sửa fit/test sau khi xem số liệu.
  Khoảng trung bình 76,8 mm so với 80,9 mm khi cùng drift: giảm 5,1%; mức giảm
  30,1% so cả profile cũ không được quy hết cho học từ dữ liệu.
- Ngoài miền, bộ fit chỉ bao phủ 230/377 mẫu. Không cho phép gắp tiếp chỉ vì
  có cảnh báo; khoảng vẫn rộng, hai nguyên nhân lỗi vẫn chưa được phân biệt.
- analyze_calibration.py tính lại đúng 10.164 kết quả mẫu–bộ quan sát, chấm
  pose riêng và ghi hash đầu vào. Có báo cáo tiếng Việt, không thêm ML giả tạo.

### 062 — Tái lập Docker và bàn giao phần hiệu chuẩn

- Candidate-20261105-interval-calibration chạy đủ 37 điều kiện, kết quả và phân
  tích trùng chính xác WSL pilot; 149 kiểm tra lõi và 10 web đạt.
- Giữ nguyên 117 tệp MuJoCo trước đó và ảnh accepted; không đẩy registry hoặc
  tự nghiệm thu. ID và hash tại docker/RELEASES.md và bằng chứng JSON.
- Bước kế tiếp đã chỉ rõ: ước lượng theo độ rộng xung PS2 của từng chu kỳ,
  lượng hóa sai số rồi mới thử kín lựa chọn cấu hình và suy giảm mạng.


### 063 — Ponytail và ARS: ước lượng từ xung PS2

- Xác minh bản academic-research-suite 3.23.2 có nguồn đúng Imbad0202/academic-research-skills
  theo manifest (commit 863e1c754f0e97062d271dcb42a9483c9ef34aa9); đọc router và
  workflow experiment-agent. Không cài trùng hoặc tự nhận là bản upstream mới nhất.
- Tái sử dụng simulator, CommandHistory và EventResidual. PulseObserver suy hệ số
  từ xung PS2 đầy đủ, trước PS3; có guard kích thước và thời gian lấy mẫu sửa được.
  Xung thiếu/đứt không tạo giả phản hồi. Không thêm phụ thuộc hoặc ML chưa cần thiết.
- Khóa kế hoạch 28 điều kiện mới trước sinh dữ liệu; so cả timeout thích nghi dùng
  chính thông tin xung. Dữ liệu cũ không bị ghi đè; nguồn hiệu chuẩn chung giữ nguyên.

### 064 — Kết quả xung và giới hạn

- Tám ca bình thường không báo; 786/786 mẫu trong khoảng. Khoảng trung bình theo
  xung 52,6 mm so với miền chung 77,4 mm, hẹp hơn 32,0%. Bốn ca gain ngoài miền
  cũ: bao phủ 388/388 so với 381/388. Chưa là xác suất bao phủ vật lý.
- Đánh đổi: chỉ báo 8/16 ca lỗi trong cửa sổ (cận dưới bảo thủ ở gain 0,90 chưa
  qua mốc); timeout thích nghi báo 16/16. Các ca đã báo còn chậm hơn timeout
  cùng thông tin 60–120 ms. Không thay ngưỡng hoặc kéo dài thử sau kết quả.
- Không đủ cơ sở cho PLC bỏ PS3/tiếp tục gắp; chưa tách cảm biến hỏng với băng
  mất chuyển động. Báo cáo công bố đủ lợi ích và thất bại ở docs/du_doan_tu_xung_PS2_20261105.md.
- Docker candidate-20261105-pulse đạt 151 kiểm tra lõi, 10 web; 28 kết quả tái lập
  chính xác và 112 tệp ghi tín hiệu/lệnh/pose/quyết định trùng byte. Lõi cũ và
  ảnh accepted không đổi; không đẩy registry hoặc tự nghiệm thu.


### 065 — Ranh giới dùng dữ liệu xung sau suy giảm mạng

- Tái sử dụng bộ quan sát và 28 bản ghi; thêm cờ usable_for_monitoring, lịch sử
  cạnh đầy đủ, thời điểm nguồn của dự đoán và tuổi dữ liệu. Có tham số pulse_fit
  không tự đồng nghĩa được dùng. Sau mất dữ liệu ở chu kỳ đã fit, không tự xóa
  trạng thái lịch sử không đầy đủ khi gói quay lại.
- Không gọi mất mẫu giữa xung là hệ khỏe: bộ quan sát không fit và không đủ
  điều kiện sử dụng. Không gán dự đoán thời điểm nguồn thành vị trí hiện tại.
- Có kiểm tra mới cho trễ cũ, gãy lịch sử, lịch âm nhìn tương lai và tốc độ
  lệnh cố định; CI bổ sung phép kiểm tra này. Các bản ghi cũ không viết lại.

### 066 — 168 phiên phát lại và nguồn cảnh báo

- Sáu lịch: ngay, trễ 40/120 ms, mất mẫu giữa xung, mất mẫu sau xung, ngắt sau
  xung. Đây là lịch giả lập trên bản ghi, không phải thử UDP/thời gian thực.
- Trễ 40 ms vẫn có đủ xung; 120 ms bị loại vì quá cũ. Mất mẫu giữa xung không
  fit; sau xung thì chốt lịch sử không đầy đủ. Gói đuôi chưa nhận khi hết file
  được công bố bị cắt cửa sổ, không kéo dài hoặc tự bổ sung thông tin.
- Khi mạng không lỗi hoặc trễ 40 ms, mô hình báo 8/16 ca lỗi; timeout cùng
  thông tin báo 16/16. Kết hợp báo 16/16 nhưng giữ riêng nhãn model_residual,
  pulse_timeout_only và transport. Không quy tám ca bổ sung thành công của DT.
- 152 kiểm tra lõi và 10 web đạt; candidate-20261105-pulse-network tái lập đủ
  168 kết quả và 168 log tương đương JSON. Hai tệp cũ đổi có chủ đích là
  pulse_observer.py và test_pulse.py; các tệp cũ khác và ảnh accepted giữ nguyên.
- Báo cáo: docs/gioi_han_xung_va_mang_20261105.md. Chưa có quyền ghi PLC,
  kiểm chứng vật lý, năng suất hoặc chính sách hồi phục đã chứng minh.


### 067 — Thử kín ba chính sách trên đoạn băng (2026-11-06)

- Ghép Cell, SensorModel, Network, PulseObserver và Predictor đang có; lệnh
  làm đổi chuyển động/sensor tiếp theo. Pose chỉ vào bộ chấm, không vào chọn tốc độ.
- 144 ca: hai tốc độ, hai gain, ba mức trễ, hai trạng thái PS3, ba chính sách,
  hai cửa sổ dừng giả định. Cửa sổ không phải dung sai gắp đã đo.
- So tuần tự, quy tắc giảm tốc theo tuổi dữ liệu và chọn tốc độ dự báo.
  Đưa miền nguồn tới hiện tại bằng lịch sử lệnh trước khi dự báo, không dùng
  tốc độ mới thay cho lệnh đã chạy trong khoảng trễ.
- Pilot đầu lỗi timeout của đối chứng thích nghi; sửa theo tích phân lệnh và
  thêm test giảm tốc, chạy pilot_v2 riêng. Giữ pilot lỗi để truy vết, loại khỏi
  kết luận. Các giả định được đưa vào JSON mà không đổi giá trị để làm đẹp số.

### 068 — Kết quả giữ vùng và mất tiến độ

- Mất PS3: dự báo không vượt mép trên ở 24/24 ca, tuần tự vượt 15/24, quy tắc
  đã chọn vượt 24/24. Theo pose chấm, dự báo dừng trong vùng ở cả 24 ca này.
- Nhưng vùng hẹp với sensor tốt, dự báo chỉ có 2/12 ca đủ xác nhận; quy tắc
  thích nghi 12/12, tuần tự 11/12. Vùng rộng cả ba 12/12. Không đổi ràng buộc
  sau kết quả hoặc gọi không vượt vùng là đã hoàn thành sản xuất.
- Tiêu chí finished bắt buộc có PS3, nên khi PS3 mất luôn 0. Đây là giới hạn
  thiết kế xác nhận của mục này, không chứng minh DT không thể dùng xác nhận
  thay thế. Chưa cho phép robot tiếp tục chỉ từ pose chấm của MuJoCo.
- Báo cáo dễ hiểu ở docs/thu_kin_doan_bang_20261106.md; bước tiếp là điều kiện
  xác nhận thay thế có giới hạn, đối chứng cùng thông tin và kiểm tra mới.

### 069 — Candidate thử kín và tái lập

- Candidate-20261106-closed-loop đạt 154 kiểm tra lõi và 10 web. Summary của
  144/144 ca khớp pilot_v2; không có lần dự báo quá ngân sách trong bộ đã ghi.
- Manifest/hash và log đầy đủ giữ trong Docker receipt/output; các tệp MuJoCo
  cũ và ảnh accepted giữ nguyên. Chưa có PLC/kiểm chứng vật lý/ML được huấn luyện,
  chưa tuyên bố tăng năng suất toàn dây chuyền. Không đẩy registry/tự nghiệm thu.


### 070 — Điều kiện xác nhận thay thế và mất truyền động

- Thêm bộ đánh giá chỉ đọc: xung/lịch sử hợp lệ, dừng đủ thời gian và toàn
  khoảng hiện tại nằm trong vùng. Tách phù hợp có điều kiện với release_eligible;
  tiền điều kiện mô hình/chuyển động chưa được kiểm chứng nên không phát lệnh.
- Bổ sung drive_stall ở plant, không làm biến đổi issued command hoặc cấp nhãn
  lỗi/pose vào bộ chọn. 72 ca với tốc độ 0,16, hai gain, hai mức trễ, ba tình
  huống, ba chính sách và hai cửa sổ giữ nguyên.
- Audit khôi phục observer theo từng nhịp, dùng mốc dừng đã thấy; chỉ đọc pose
  sau quyết định để chấm. 24/24 cặp PS3 không báo/băng đứng cùng quan sát và
  quyết định, nhưng pose cuối chênh 191–271 mm. Không suy thành tỷ lệ chẩn đoán.

### 071 — Phát hiện lỗi gate và chấm lại nguyên trạng

- Gate đầu dùng max_speed_m_s trong cửa sổ dừng, gồm cả tốc độ bên trái biên
  ngay trước lệnh dừng; đã từ chối sai toàn bộ với stop_not_maintained. Không
  dùng số này như kết quả nghiên cứu.
- Sửa theo quãng lệnh và lệnh cuối thực sự trong khoảng dừng; thêm test từng
  chạy rồi dừng đúng biên, đồng thời từ chối chạy lại. Không sửa CommandHistory
  chung vốn cần giá trị biên cho lượng hóa biến thiên lệnh.
- Chấm lại dữ liệu nguyên trạng: vẫn 0/72 khoảng nằm trọn vùng, nhưng lý do
  đúng là interval_outside_zone. Không có xác nhận sai vì không phát hành xác
  nhận nào; không gọi đây là độ chính xác 100%.
- Giữ candidate/audit đầu riêng. Bản đúng candidate-20261106-confirmation-v2
  đạt 155 kiểm tra lõi, 10 web; 72 summary và audit đúng trùng pilot đã sửa.
  Bản accepted không đổi, không đẩy registry hoặc tự nghiệm thu.
- Báo cáo docs/xac_nhan_thay_the_20261106.md chỉ rõ cần quan sát độc lập hoặc
  tiền điều kiện kiểm chứng, không thu nhỏ khoảng bằng tay để cho robot chạy.
