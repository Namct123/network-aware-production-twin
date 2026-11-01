# Đặt lại để chạy một chu trình mới — hướng dẫn dễ hiểu

Ngày cập nhật: 31/10/2026.

**Kết quả của bước này:** đã làm được quy trình gửi yêu cầu đặt lại, nhận xác
nhận và chờ một lệnh bắt đầu riêng trong mô phỏng. Chưa nối quy trình này với
PLC (bộ điều khiển máy thật), và chưa tiếp tục phôi đang làm dang dở.

## 1. Vì sao phải có bước này?

Máy đang HOLD, tức là dừng chờ. Dữ liệu trở lại chưa có nghĩa máy được phép
chạy ngay. Một yêu cầu cũ có thể đến muộn hoặc bị gửi lặp. Nếu không phân biệt
được các yêu cầu, chương trình có thể khởi động nhầm một lượt mới.

Quy trình mới buộc các phần chương trình phải thống nhất: **đang nói về lần
dừng nào, yêu cầu nào, bộ thông số nào và lượt khởi tạo nào**.

## 2. Trình tự hoạt động

1. **Lượt cũ dừng chờ.** Chương trình lưu lại lý do và công đoạn đã dừng.
2. **Có đủ dữ liệu mới để xem xét.** Đây vẫn chưa phải lệnh cho phép chạy.
3. **Người kiểm tra xác nhận đã chuẩn bị lại.** Các việc cần kiểm tra gồm
   nguyên nhân dừng, phôi, trục/xi lanh, chân không/tải và liên động.
4. **Gửi yêu cầu đặt lại.** Yêu cầu có mã riêng và gắn với lần dừng hiện tại.
5. **Phía mô phỏng chuẩn bị cảnh mới rồi trả xác nhận.** Xác nhận phải đúng mã
   yêu cầu và bộ thông số. Đến đây băng tải vẫn chưa chạy.
6. **Có lệnh bắt đầu riêng.** Lệnh này phải gắn đúng xác nhận vừa nhận.
7. **Chạy lượt mới một lần.** Cùng một quyền chạy không được lấy lại lần thứ hai.

Trong phép thử hiện tại, các xác nhận của người kiểm tra **được tạo giả lập**.
Chưa có màn hình đăng nhập, người vận hành thật hoặc phản hồi xác nhận từ PLC.

## 3. Có phải tự khôi phục phôi đang dang dở không?

**Không.** Phép thử dùng hai cảnh mô phỏng độc lập:

- Cảnh A chạy tới khi mất dữ liệu rồi dừng chờ. Sau đó nó được giữ nguyên.
- Cảnh B được tạo mới, phôi được đặt tại vị trí ban đầu đã biết của mô hình.
  Cảnh B chỉ chạy sau đúng trình tự xác nhận và lệnh bắt đầu.

Cấu hình mất dữ liệu của cảnh A được bỏ khỏi cảnh B và ghi rõ vào hai tệp
thông số. Đây là cách giả lập việc đã xử lý sự cố và chuẩn bị lại máy; không
phải chương trình tự sửa đường truyền hay tự biết phôi cũ đang ở đâu.

Muốn tiếp tục phôi đang dang dở cần xác định lại vị trí phôi, trục và trạng thái
cơ cấu trên cùng máy. Những nguồn xác nhận đó hiện chưa đủ để kiểm chứng.

## 4. Chương trình chặn những trường hợp nào?

| Trường hợp | Cách xử lý |
|---|---|
| Chưa đủ điều kiện xem xét sau HOLD | Không nhận yêu cầu đặt lại |
| Thiếu một mục xác nhận của người kiểm tra | Không nhận yêu cầu đặt lại |
| Bản đánh giá đã cũ | Yêu cầu kiểm tra lại bằng dữ liệu mới |
| Xác nhận thuộc phiên/yêu cầu/bộ thông số khác | Không dùng xác nhận đó |
| Xác nhận dùng số lần khởi tạo cũ | Không dùng cho lượt hiện tại |
| Chưa có xác nhận mà đã gửi lệnh bắt đầu | Không cho lấy quyền chạy |
| Xác nhận đến quá muộn hoặc không đến | Chuyển sang bị chặn, cần xem xét lại |
| Bên nhận báo đặt lại thất bại | Giữ bị chặn |
| Lệnh bắt đầu gửi lặp | Không tạo quyền chạy lần thứ hai |

Nếu không nhận được xác nhận đúng hạn, không thể biết bên nhận đã đặt lại hay
chưa. Vì vậy chương trình không đoán rằng việc đặt lại đã thành công và không
tự gửi lệnh chạy tiếp.

## 5. Những tệp đã bổ sung và tác dụng

| Tệp/phần thay đổi | Làm gì? |
|---|---|
| `mujoco/reset_protocol.py` | Kiểm tra yêu cầu, xác nhận và lệnh bắt đầu; kiểm tra mã, thời gian và số lần khởi tạo. Không phát lệnh tới PLC. |
| `mujoco/test_reset_protocol.py` | Thử gửi sai, gửi cũ, quá hạn, gửi lặp và việc chỉ lấy quyền chạy một lần. |
| `mujoco/check_reset.py` | Ghép phần kiểm tra bản tin với hai lượt mô phỏng chuyển động và viết báo cáo tiếng Việt. |
| `mujoco/experiments/reset_protocol.json` | Chứa bốn thời gian chờ có thể chỉnh; không phải số đo máy thật. |
| `experiment.run(..., prepared_cell=...)` | Cho phép chạy chính cảnh mô phỏng đã chuẩn bị trước xác nhận; từ chối dùng lại ngay cảnh đã chạy mà chưa đặt lại. |
| `handshake_before_start.json` | Lưu biên bản trước khi bắt đầu lượt mới để điều tra nếu lượt đó gặp lỗi. |
| `receipt.json` | Lưu kết quả cuối của quy trình và liên kết giữa các mã xác nhận. |

Phần kiểm tra thời gian phải được gọi định kỳ, kể cả khi không có bản tin mới.
Hàm `poll` (kiểm tra thời gian chờ) phục vụ việc này. Bộ thử có tình huống không
gửi xác nhận nào để kiểm tra rằng chương trình vẫn chuyển sang bị chặn.

Các mã chỉ dùng để ghép đúng trình tự. Chúng không thay hệ thống xác thực người
dùng, xác nhận an toàn máy hoặc phản hồi thật từ cảm biến.

## 6. Các thông số thời gian

| Tên trong tệp | Nghĩa dễ hiểu | Giá trị đang thử |
|---|---|---:|
| `reset_ack_timeout_s` | Chờ tối đa để nhận xác nhận đặt lại | 0,5 giây |
| `start_window_s` | Sau xác nhận, chờ tối đa để nhận lệnh bắt đầu riêng | 0,5 giây |
| `review_max_age_s` | Tuổi lớn nhất của bản đánh giá sau dừng khi nhận yêu cầu | 0,25 giây |
| `message_max_age_s` | Tuổi lớn nhất của yêu cầu khi nhận | 0,1 giây |

Đây là thông số thiết kế cho phép thử, chưa được đo và chọn cho đường truyền
thật. Trong tệp JSON (tệp lưu dữ liệu có cấu trúc), số thập phân dùng dấu chấm:
`0.5` nghĩa là 0,5 giây.

Các thời điểm gửi/nhận trong phép thử là thời gian giả lập. Chúng không phải
kết quả đo tốc độ truyền dữ liệu hoặc thời gian phản hồi thực của PLC.

## 7. Cách chạy từng bước

Mở PowerShell (cửa sổ chạy lệnh của Windows) và nhập:

```powershell
Set-Location 'C:\Users\Admin\Documents\ChatGPT\plc'
.\scripts\docker_dt.ps1 -Mode reset-check
```

Chương trình in đường dẫn thư mục kết quả mới. Mở **report.md** trước; báo cáo
này viết bằng tiếng Việt. Những tệp còn lại dùng để kiểm tra chi tiết:

- `held_cycle`: nhật ký lượt cũ đã dừng chờ.
- `new_cycle`: nhật ký lượt mới.
- `message_cases.json`: các tình huống gửi/nhận yêu cầu, không phải các lượt máy chạy.
- `receipt.json`: biên bản cuối của quy trình.
- `before_config.json`, `after_config.json`: thông số trước và sau khi chuẩn bị lại.

Muốn thay thời gian chờ, sao chép tệp `reset_protocol.json` trong thư mục
`mujoco/experiments`, sửa các giá trị rồi dùng:

```powershell
.\scripts\docker_dt.ps1 -Mode reset-check -ResetSettings thong_so_dat_lai.json
```

Không dùng tệp thời gian chờ này làm tệp thông số toàn bộ máy. Thông số máy vẫn
truyền qua `-Config`. Nếu đổi nhiều thông số máy, sự cố giả lập có thể không còn
rơi đúng công đoạn của kịch bản; phép thử sẽ báo không đạt thay vì tự đổi kết quả.

## 8. Cách đọc số lượng phép thử

Bộ thử gồm **15 tình huống bản tin** (gói dữ liệu yêu cầu/xác nhận) và **2 lượt
mô phỏng chuyển động**. Không cộng hai loại này rồi gọi là 17 lượt chạy máy.

Lượt phát triển đầu có 14 tình huống bản tin và hai lượt mô phỏng đã đạt; sau đó
bổ sung thêm tình huống không nhận được xác nhận, thành 15 tình huống bản tin.
Phần kiểm tra chương trình có 88 phép kiểm tra. Kết quả của bản đóng gói cuối
đã được kiểm tra lại trong Docker (gói môi trường để dễ chuyển máy).

### Kết quả của bản đóng gói cuối

- 88 phép kiểm tra chương trình: đạt.
- 15 tình huống gửi/nhận yêu cầu và hai lượt mô phỏng chuyển động: đạt yêu cầu
  tương ứng; cảnh cũ giữ nguyên, cảnh mới đặt phôi đúng hộp.
- 10 ca đánh giá sau dừng, 78 ca kiểm tra nhiều tình huống, 9 ca thử nhanh phần
  giảm tốc theo dữ liệu và 15 ca giảm tốc cố định: đạt tiêu chí của từng bộ thử.
- Nhật ký điều khiển của 78 ca cũ trùng mã kiểm tra với bản trước. Trong các ca
  đó, việc thêm quy trình mới không làm đổi các quyết định đã có.

Đạt tiêu chí ở một ca dừng không có nghĩa ca đó hoàn tất sản xuất. Các báo cáo
cũ vẫn đếm riêng số lượt hoàn tất và số lượt dừng chờ.

Báo cáo của lượt đặt lại cuối nằm tại:
`output/docker/reset-check_20261031T105102Z_8fce769a/report.md`.
Hồ sơ mã nguồn và bản đóng gói được lưu ở
`docker/evidence/candidate-20261031-reset-protocol.json`.
Đây vẫn là bản thử chờ bạn kiểm nghiệm; chưa đổi bản đã được giữ làm mốc trước đó.

## 9. Phần chưa hoàn thành

- Chưa nối bộ đặt lại này tới PLC thật.
- Chưa có xác thực người vận hành thật hoặc xử lý nhiều nơi gửi lệnh đồng thời.
- Số lần khởi tạo mới bảo vệ các bản tin đặt lại/bắt đầu; chưa gắn vào toàn bộ
  dòng dữ liệu cảm biến của hệ đang chạy.
- Chưa tiếp tục một phôi đang dang dở, chưa tự khôi phục tải đang treo.
- Bản CAD V5 và mô hình mô phỏng chuyển động chưa đồng bộ đầy đủ.
- Bộ dự báo trong phép thử được cho tối đa 1 giây để tính; chưa chứng minh hệ
  thống đáp ứng đều trong 20 mili giây trên máy thật.

Mặc định chạy dự án vẫn dùng giới hạn tốc độ cố định trước đó. Quy trình mới
chỉ chạy khi chọn phép thử đặt lại; các bản Docker đã được giữ từ trước không
bị thay thế bằng một bản được coi là đã nghiệm thu.
