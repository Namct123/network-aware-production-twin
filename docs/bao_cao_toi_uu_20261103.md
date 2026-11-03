# Kết quả tối ưu dự báo MuJoCo — 03/11/2026

Giữ mô hình và các thông số vật lý; thay cách thực hiện vòng lặp và số luồng phần mềm. Mặc định điều khiển vẫn dùng nhánh 1 chiều.
Đã giữ bản gốc làm đối chứng và chạy trong ảnh Docker cuối sau khi sửa lỗi ghép bảng tham số.

## Độ khớp giữa các cách tính

12 trường hợp, mỗi trường hợp đối chiếu 1/4/8 luồng với bản gốc. Tất cả có cùng hành động, số bước và số kịch bản;
biên lệch quan sát lớn nhất bằng 0 trong các lượt này. Ngưỡng đối chiếu là 1e-9 m, chỉ để phát hiện khác cách tính, không phải sai số máy thật.
Có thêm kiểm tra quỹ đạo 30 bước, đầu vào không hợp lệ, thời gian mô phỏng không tiến và quá hạn.

## Thời gian tính đầy đủ trong Docker

15 mẫu sau làm nóng cho mỗi hàng, dùng hạn chức năng riêng 1 giây. Ba trạng thái giống đợt đánh giá trước.
Khởi tạo được ghi riêng. Đo lần lượt, không phải thử nghiệm ngẫu nhiên hóa hay chứng minh thời gian lớn nhất.

| Cách tính | Trung vị (ms) | p95 (ms) | Tính đủ với hạn chức năng | Tính đủ với hạn 20 ms |
|---|---:|---:|---:|---:|
| Vòng lặp gốc | 398.449 | 446.997 | 15/15 | 0/15 |
| Bản gom: 1 luồng | 137.371 | 151.622 | 15/15 | 0/15 |
| Bản gom: 4 luồng | 56.393 | 62.516 | 15/15 | 0/15 |
| Bản gom: 8 luồng | 50.288 | 54.653 | 15/15 | 0/15 |

Tỷ số trung vị gốc/8 luồng quan sát được: 7.92 lần. Đây là thời gian tính dự báo; chưa đo tăng tốc chu trình gắp thật.
Không biến thể nào tính đủ trong 20 ms. Trả dừng chờ sau khi nhóm tính xong có thể vượt hạn nhiều hơn vòng lặp cũ vì không ngắt giữa nhóm mã máy được.
Không tăng hạn hoặc giảm số kịch bản để đổi kết quả thành đạt.

## Kiểm tra tích hợp và bàn giao

- 103 kiểm tra lõi trong Docker đạt, cùng bộ tích hợp và 24 lượt hồi quy.
- Hồ sơ native_physics_cell_20261103.json dùng 8 luồng được ghép vào chu trình: dự báo quá hạn nên dừng chờ; phôi còn được hỗ trợ trong mô phỏng.
- Đã sửa lỗi bảng đơn vị không nhận native_threads; phân loại trường này là thiết lập thiết kế, không phải phép đo.
- Ảnh candidate-20261103-native-physics chờ người dùng kiểm nghiệm; giữ ảnh đã nghiệm thu.
- [Cách mở và thay số luồng](toi_uu_du_bao_mujoco.md); [nhật ký từng mục](nhat_ky_cong_viec.md).

Nhánh tiếp theo cần giải quyết hạn 20 ms hoặc tách dự báo nặng khỏi vòng quyết định nhanh với kiểm tra hạn dùng kết quả. Chưa kết nối PLC hoặc xác nhận vật lý.
