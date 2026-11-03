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
