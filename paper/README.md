# Bản thảo bài báo đang phát triển

Bản hiện tại chỉ viết lý thuyết, phương pháp đã triển khai và kết quả ảo có bằng
chứng. Mục kiểm chứng vật lý để trống; chưa có dữ liệu máy thật để điền.
Đây là bản làm việc, chưa phải bản được tác giả duyệt hoặc sẵn sàng nộp.

## Các tệp cần sửa

- title_abstract.tex: title, abstract và từ khóa; tên tác giả/đơn vị để trống.
- body.tex: toàn bộ phần thân bài, gồm Introduction/Related Work, mô hình và
  lý thuyết, phương pháp ảo, kết quả ảo, phần vật lý trống, thảo luận, kết luận.
- main.tex: tệp ghép bài theo class LNCS một cột, không tự đổi lề/cỡ chữ.
- generated/: bảng số liệu và giá trị sinh từ bằng chứng, không sửa tay.
- evidence/: bản chụp dữ liệu, dấu kiểm tra nguồn, các nhóm nhận định và kiểm tra nhất quán.

Bản cũ trong docs/ giữ làm lịch sử; paper/ là bản đang viết tiếp. File paper/export_pdf.py
đã thay bộ xuất abstract cũ bằng biên dịch LaTeX thật của bản mới.

## Biên dịch

Cài Python và Tectonic hoặc pdfLaTeX, tại thư mục gốc dự án chạy:

```text
python paper/prepare.py
python paper/export_pdf.py --engine /duong/dan/tectonic
```

Có thể bỏ --engine nếu chương trình đã ở PATH. Tệp class llncs.cls được sao
chép nguyên bản từ template đã có trong dự án. Không bắt buộc dùng trình biên
dịch nằm ở tmp/; đó chỉ là đường dẫn dự phòng trên máy phát triển hiện tại.
Xuất: output/pdf/dt_cppps_manuscript_virtual.pdf và reports/dt_cppps_manuscript_virtual.pdf.
Có thể tải thư mục paper lên công cụ LaTeX do chính tác giả cho phép; người dùng
phải tự quyết định việc gửi bản thảo chưa công bố ra dịch vụ bên ngoài.

## Phân biệt các loại bằng chứng

- Số liệu lấy từ Docker candidate-20261102-qualification, không phải phép đo máy thật.
- 24 lượt đạt tiêu chí nghĩa là 18 đặt phôi và 6 dừng còn được hỗ trợ trong mô phỏng;
  không phải cả 24 đều sản xuất thành công.
- So bật/tắt giới hạn tốc độ tái cấu hình, không phải PLC tuần tự đối đầu DT.
- Nhánh MuJoCo chưa đạt hạn 20 ms; kết quả không đạt vẫn được nêu trong bài.
- Mô hình toán là mô tả thuật toán/giả thiết; chưa chứng minh ổn định hoặc an toàn vật lý.
- Tối ưu MuJoCo là hạng mục tiếp theo; chưa ghi nhận một kết quả tối ưu mới trong bài.

## Các phần cố ý chưa điền

Thiết lập và hiệu chuẩn máy thật; đồng bộ PLC/mạng thực; lỗi và độ chính xác đặt
phôi vật lý; so sánh PLC tuần tự. Tác giả, đơn vị, tài trợ, xung đột lợi ích và
công bố dùng AI cũng cần người chịu trách nhiệm xác nhận; không sao chép từ bài mẫu.

## Rà soát của tác giả trước khi nộp

Đã đối chiếu nguồn và dữ liệu bằng trợ lý, chưa có xác nhận của tác giả chịu
trách nhiệm. evidence/claims.csv liên kết nhóm nhận định với nguồn; các trường
human_verification giữ pending. evidence/audit.json không tự cấp chứng nhận.
Chuẩn định dạng phải rà lại theo hội nghị cụ thể, kể cả giới hạn trang, thông
tin tác giả, tài liệu tham khảo, khả năng tiếp cận và yêu cầu công bố dùng AI.
Không suy việc dùng template LNCS thành bài đã được Springer chấp nhận.


Bổ sung 03/11: body.tex có phần tối ưu native rollout. Bảng cũ 02/11 được giữ riêng; bảng mới lấy từ candidate-20261103-native-physics. Không biến thể nào tính đủ trong hạn 20 ms ở các mẫu mới; các mục vật lý vẫn trống.
