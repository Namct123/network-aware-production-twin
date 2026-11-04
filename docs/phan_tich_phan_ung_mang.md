# Nghiên cứu phản ứng khi dữ liệu bị trễ, mất hoặc sai

## Mục tiêu

Trả lời ba câu hỏi: bao lâu lõi phát lệnh giảm tốc/dừng; dựa vào tín hiệu nào;
có đủ thông tin để xác định nguyên nhân không. Đây là nghiên cứu trên thời gian
mô phỏng, không phải phép đo độ trễ PLC hoặc độ chính xác chẩn đoán máy thật.

## Bộ dữ liệu và cách so sánh

Dùng sáu tình huống: bình thường; trễ 40 ms; trễ 120 ms; mất gói 300 ms;
một gói lặp; một gói sai phiên. Tình huống bắt đầu ở nhịp ngay sau lần dự báo đầu,
khi phôi đã được quan sát. Mỗi tình huống lặp ba lần và phát lại hai lần.
Đây là lặp cùng mô hình/lịch thử, không phải 18 hệ vật lý độc lập.

`mujoco/audit_response.py` chỉ đọc nhật ký. Nó đối chiếu cấu hình, bảng tín hiệu,
số lượng gói/nhịp và mã băm toàn bộ Python của bên sinh dữ liệu với đúng bảng
nguồn của ảnh Docker đó. Không chạy lại dữ liệu cũ bằng mã mới rồi gọi là bản gốc.
`passed` trong báo cáo nghĩa là hồ sơ qua các phép kiểm tra nhất quán, không phải
mọi lỗi đã được xử lý tốt hoặc đã đạt chuẩn an toàn.

Các mốc được tách rõ:

- Mốc áp dụng tình huống: nhịp đầu bắt đầu trễ/mất/gói sai.
- Lệnh giảm tốc đầu tiên: tốc độ lệnh dương thấp hơn trước mốc, không nhầm với dừng.
- Gói bị chặn đầu tiên: bộ kiểm tra phiên/thứ tự không nhận gói đó.
- Dừng chờ đầu tiên: trạng thái HOLD (dừng và chờ xử lý), kèm đúng lý do.
- Thời gian từ gói hợp lệ cuối trước mốc: giúp tránh nhầm độ dài khoảng im lặng
  với thời gian tính từ gói đầu bị mất.

## Phát hiện về cách so thời gian

Bộ thử cũ cho thấy một số khoảng im lặng 100 ms chưa kích hoạt dừng ở đúng biên.
Ví dụ máy tính lưu `0.6 - 0.5` thành số hơi nhỏ hơn `0.1`. Với nhịp 20 ms,
phép so có thể đợi thêm một nhịp. Thử sáu mốc đồng hồ trong ảnh sinh dữ liệu gốc:
ba mốc chưa dừng đúng biên, cả sáu dừng khi qua thêm 20 ms.

Đã sửa bằng `clock_checks.elapsed_at_least`, dùng chung cho Sequence và SignalHealth.
Dung sai tính toán tuyệt đối là 1 ns (một phần tỷ giây), nhằm xử lý sai số số thực.
Ngưỡng im lặng 100 ms giữ nguyên. Dung sai này không phải độ chính xác đồng hồ,
không làm cho hệ thống đạt thời gian thực và không phải tham số vật lý được hiệu chuẩn.
Phản ứng có thể sớm hơn biên tối đa 1 ns, thay vì chậm cả một nhịp 20 ms.

## Giới hạn phân biệt nguyên nhân

So cặp trễ dài và mất gói bằng cùng mốc thời gian, dữ liệu và lệnh. Chỉ chuẩn hóa
tên phiên thí nghiệm; không bỏ khác biệt giá trị cảm biến, tuổi dữ liệu hoặc quyết định.
Nếu hai chuỗi giống nhau tới lúc dừng, không thể dùng riêng bằng chứng đó để khẳng
định đã tách được nguyên nhân. Dừng do im lặng dữ liệu không đồng nghĩa cảm biến hỏng.

Gói lặp/sai phiên bị chặn ở cùng nhịp nhận có thể có chỉ số 0 ms theo đồng hồ mô phỏng.
Điều đó không có nghĩa CPU xử lý trong 0 giây. Dữ liệu trở lại không tự xóa HOLD.
Dừng vì chưa xác nhận trục XY/đầu hút là giới hạn phản hồi, không phải phát hiện lỗi mạng.

## Cách chạy lại bộ đọc

Trong môi trường Python của dự án:

```text
python mujoco/audit_response.py --input <thu_muc_nghien_cuu> --source-manifest <source_manifest_cua_ben_sinh_du_lieu.json> --output <thu_muc_moi>
```

Thư mục xuất phải mới. Đọc `report.md`, `timing.csv` và `response_audit.json`.
Bảng nguồn phải của đúng bên sinh dữ liệu, không lấy bảng nguồn hiện tại thay cho
bản gốc. Kết quả cũ và mới được lưu riêng; mọi cấu hình đều giữ nguyên để đối chiếu.
