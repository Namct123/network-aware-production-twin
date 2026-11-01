# Đánh giá sau HOLD — ngày 31/10/2026

**Bổ sung mới của dự án:** đã có [phép thử đặt lại một lượt mô phỏng mới](dat_lai_chu_trinh_moi.md).
Phần này vẫn chỉ đánh giá sau dừng; chưa tự tiếp tục phôi cũ hoặc nối đặt lại với PLC thật.

**Hạng mục đã làm:** phân loại lý do HOLD, lưu bối cảnh dừng, theo dõi dữ liệu
mới sau dừng và xuất checklist để người vận hành xem xét. **Chưa triển khai
reset hoặc tự chạy tiếp.** `OPERATOR_REVIEW` không có nghĩa máy được phép chạy.

Candidate mới: `candidate-20261031-hold-review`, chờ người dùng kiểm nghiệm.
Demo mặc định vẫn dùng profile cap cố định trước đó; đánh giá sau HOLD bật
trong profile thử riêng.

## Những gì đã bổ sung và tác dụng

| Phần | Chức năng | Tác dụng |
|---|---|---|
| `Sequence.hold_context` | Ghi lý do đầu tiên, công đoạn trước HOLD, thời gian, ước lượng và lệnh trước dừng. | Biết hệ thống đã dừng ở đâu trong trình tự, không mất dấu do dữ liệu sau đó tốt trở lại. |
| `mujoco/recovery.py` | Phân nhóm lý do và đánh giá liên tục dữ liệu hậu HOLD. | Phân biệt việc telemetry phục hồi với điều kiện máy thật còn chưa được xác nhận. |
| `recovery.jsonl` và `summary.json` | Ghi trạng thái đánh giá, blockers, số mẫu liên tục, checklist và trạng thái chưa biết. | Thành viên xem được vì sao còn bị chặn và cần kiểm tra gì. |
| `network.outage_windows_s` | Tạo các khoảng mất telemetry có bắt đầu/kết thúc. | Thử mất dữ liệu rồi phục hồi; không cần rút dây hoặc thao tác hệ vật lý. |
| Profile `hold_review_cell_20261031.json` | Bật assessment, cấu hình số mẫu/thời gian quan sát. | Đổi thông số qua JSON/CSV, giữ profile cũ và hành vi chạy cũ. |
| `test_recovery.py` | Kiểm tra bối cảnh, dữ liệu sau HOLD, duplicate, blocker, không sửa controller và khoảng outage. | Chặn việc coi bản tin lặp/cũ là bằng chứng mới hoặc âm thầm xóa HOLD. |
| `check_recovery.py` / `recovery-check` | 10 kịch bản MuJoCo, gồm mất rồi phục hồi telemetry và lỗi cảm biến. | Kiểm chứng trạng thái đánh giá cùng bất biến không restart. |

Mô-đun đánh giá chỉ đọc tín hiệu bên nhận, dấu thời gian và bối cảnh/lệnh của
controller. Nó không nhận vị trí thật của phôi, nhãn lỗi gây ra hoặc lịch outage
từ bộ giả lập. Không có hàm phát lệnh reset/start/resume trong mô-đun này.

## Các trạng thái đánh giá

Trước khi đọc stage, kiểm tra `recovery_assessment.enabled=true`. Khi disabled,
mô-đun không đánh giá; stage mặc định của nó không mô tả trạng thái controller.

| Trạng thái | Ý nghĩa |
|---|---|
| `NOT_HOLD` | Controller chưa HOLD hoặc đã DONE; chưa có đánh giá hậu HOLD. |
| `WAIT_OBSERVATIONS` | Chưa có đủ chuỗi mẫu mới sau HOLD, dữ liệu còn thiếu/cũ, hoặc dấu hiệu sức khỏe chưa hết. |
| `OPERATOR_REVIEW` | Nhóm nguyên nhân telemetry/chất lượng dữ liệu đã qua các kiểm tra quan sát; xuất checklist cho người vận hành. Controller **vẫn HOLD**. |
| `MANUAL_INTERVENTION` | Nguyên nhân khác cần chẩn đoán, có khả năng giữ tải, xi lanh chưa xác nhận thu về, hoặc cửa sổ đánh giá đã quá hạn. |

Tất cả các dòng đánh giá đều ghi:

```json
"automatic_resume_allowed": false,
"restart_command_issued": false
```

Không nối `OPERATOR_REVIEW` trực tiếp với nút Start hoặc lệnh chạy. Các kiểm tra
này không xác nhận an toàn máy và không thay vai trò liên động PLC/E-stop.

## Điều kiện để chuyển sang OPERATOR_REVIEW

1. Lý do đầu tiên thuộc nhóm `telemetry_or_signal_quality`, ví dụ timeout nhận
   dữ liệu, khoảng khuyết mẫu hoặc tín hiệu cần thiết bị stale/unavailable.
2. Có đủ mẫu chất lượng good, số thứ tự/thời gian tăng liên tiếp, được lấy
   **sau thời điểm HOLD**. Mẫu cũ vừa đến không được tính như đã quan sát máy sau dừng.
3. Không có nhịp nhận bị thiếu trong chuỗi; khoảng nguồn không vượt giới hạn.
4. Đã chờ đủ thời gian settle cấu hình, hai lệnh băng bằng 0 và cờ hold vẫn bật.
   Đây là kiểm tra lệnh nội bộ, không phải phản hồi xác nhận dừng từ PLC/encoder.
5. Các cảm biến hai đầu báo nhất quán: A1/A2 thu về, đầu duỗi không báo tác động.
6. Không có lệnh hút đang bật và không còn finding sức khỏe ở nhịp hiện tại.
7. Thời gian HOLD chưa vượt cửa sổ xem xét cấu hình.

Nếu lý do dừng là thiếu cạnh, lỗi trình tự, bất định, vượt deadline tính,
không xác nhận XY/chân không hoặc nguyên nhân chưa phân loại, dữ liệu tốt trở
lại cũng không đưa sang đường review telemetry này. Nhóm lý do là phân loại
**mã dừng phần mềm**, không phải kết luận nguyên nhân hỏng ngoài thực tế.

Khi một nhịp nhận bị thiếu hoặc bản tin lặp/đảo thứ tự, chuỗi mẫu mới bị cắt.
Đánh giá không thay đổi estimator đã dừng để giả tạo vị trí phôi mới.

## Những gì vẫn chưa biết và phải kiểm tra

Ngay cả tại OPERATOR_REVIEW, các mục này vẫn chưa được xác nhận:

- Vị trí/nhận dạng thực của phôi hiện tại, vật có bị lệch hoặc có tải đang treo không.
- Vị trí XY và trạng thái home thực; lệnh đặt vị trí không phải encoder/home feedback.
- Chân không thực; lệnh hút không thay cho Vacuum_OK.
- Liên động cục bộ PLC và E-stop; assessment chưa có nguồn xác nhận các trạng thái này.

Checklist yêu cầu người vận hành xác định và giữ ổn định phôi/tải, xác minh các
trạng thái thực và sử dụng quy trình reset/tái khởi tạo có đồng bộ trạng thái.
Quy trình reset đó **chưa được cài đặt** ở hạng mục này. Không nhả hút tự động
để làm sạch trạng thái và không giả lập các tín hiệu còn thiếu thành good.

## Thông số có thể đổi

Trong profile thử:

```json
"recovery": {
  "enabled": true,
  "fresh_samples": 5,
  "settle_wait_s": 0.1,
  "max_hold_age_s": 2.0
}
```

Đây là thiết lập thiết kế chưa hiệu chuẩn vật lý. `fresh_samples` không phải
số lần xác nhận của người vận hành. `max_hold_age_s` giới hạn đường review,
không phải thời gian được phép giữ tải hoặc timeout an toàn máy.

CSV `hold_review_parameters_to_fill_20261031.csv` có **205 trường số**: 202 trường
của profile cap cố định và 3 trường recovery. Số lượng bằng CSV adaptive nhưng
tập trường khác nhau. Các ô đo vẫn để trống, không có nghĩa đã đo 205 đại lượng.

Fixture outage ví dụ:

```json
"outage_windows_s": [[5.4, 5.56]]
```

Trường này nằm trong `network`, dùng khoảng `[bắt đầu, kết thúc)` theo giây mô
phỏng. Tối đa 20 khoảng có thứ tự, không chồng lấn và nằm trong run budget.
Nếu có gói đang chờ trong hàng đợi trước outage, chúng vẫn có thể tới. Đây là
ngăn gửi các bản tin mới trong khoảng đó, không xóa hàng đợi và không mô phỏng
mọi dạng sự cố mạng thực.

Profile thử đặt `timing.hold_settle_s=0.6` để quan sát sau HOLD lâu hơn. Trường
này chỉ điều khiển lúc kết thúc lượt mô phỏng, không xóa HOLD. Các profile cũ
không tự đổi sang 0,6 s. Outage rỗng thì CSV chưa có hàng thời điểm outage;
thêm hai trường số mỗi khoảng nếu xuất lại template từ một profile có khoảng đó.

## Chạy thử và đọc kết quả

```powershell
Set-Location 'C:\Users\Admin\Documents\ChatGPT\plc'
.\scripts\docker_dt.ps1 -Mode recovery-check
```

Launcher in thư mục `output/docker/recovery-check_...`. Mở `results.json` trước.
Trong từng ca:

1. `summary.json/hold_context`: lý do và công đoạn trước dừng, lệnh trước dừng.
2. `summary.json/recovery_assessment`: đánh giá cuối, các lần đổi trạng thái.
3. `recovery.jsonl`: từng nhịp, blockers, chuỗi mẫu, checklist và trạng thái chưa biết.
4. `controller.jsonl`: kiểm tra controller vẫn HOLD, lệnh băng vẫn 0.
5. `effective_config.json`, `manifest.json`: cấu hình và mã đã dùng.

Muốn chạy riêng một profile tự chỉnh, sao chép profile review, sửa outage rồi:

```powershell
.\scripts\docker_dt.ps1 -Mode demo -Config my_hold_review.json
```

Nhánh demo vòng hở chỉ dành cho mô phỏng, không xác nhận rằng phần cứng thật đã
có đủ feedback. Dùng `strict` để giữ các rào chặn do feedback còn thiếu.

## Kết quả phát triển

Lượt `output/hold_review_dev_20261031_a` qua 10/10 ca:

| Tình huống | Controller cuối | Assessment cuối |
|---|---|---|
| Không lỗi | DONE | NOT_HOLD |
| Mất telemetry ngắn khi cấp phôi rồi phục hồi | HOLD | OPERATOR_REVIEW |
| Mất telemetry ngắn trong TRACK rồi phục hồi | HOLD | OPERATOR_REVIEW |
| Telemetry chưa phục hồi | HOLD | WAIT_OBSERVATIONS |
| Thiếu quang pickup/upstream/pusher hoặc quang báo cao ngay đầu | HOLD | MANUAL_INTERVENTION |
| Strict thiếu xác nhận chuyển động/chân không | HOLD | MANUAL_INTERVENTION |
| Dữ liệu trở lại nhưng đã quá cửa sổ review | HOLD | MANUAL_INTERVENTION |

Các ca HOLD đều giữ lệnh băng 0, giữ latch, không có chuyển tiếp ra khỏi HOLD;
assessment không phát restart. PASS còn kiểm tra kết quả đặt phôi hoặc hỗ trợ
phôi cuối lượt theo evaluator hình học sẵn có. Đây không chứng minh an toàn toàn
quỹ đạo, hiệu chuẩn máy, độ chính xác chẩn đoán hoặc tự phục hồi thành công.
Budget predictor của bộ thử là 1 s; chưa chứng minh deadline vận hành 20 ms.

## Kết quả kiểm tra trong Docker

Candidate cuối qua **82 kiểm tra logic**, **10 ca review**, **78 ca robustness**,
**9 adaptive smoke**, **15 ca hồi quy fixed**, demo và strict. Hai kiểm tra biên
đóng gói trên host cũng đạt. Trong cả 10 ca review, không có chuyển tiếp ra khỏi
HOLD hoặc lệnh restart. Các trạng thái cuối lặp lại bảng phát triển ở trên.

Toàn bộ nhật ký `controller.jsonl` của 78 ca robustness có hash trùng bản trước,
cho thấy thay đổi này không đổi quyết định trong các fixture đó. Không suy rộng
thành chứng minh tương đương cho mọi trạng thái có thể xảy ra.

Image: `sha256:9da55946676d7edf4bf22b6186b541128b6631e68f10713922e54e3a01efc542`.
Hồ sơ đầy đủ: `docker/evidence/candidate-20261031-hold-review.json`.
Log: `output/docker/qualification_20261031_hold_review/`.
Các image trước giữ nguyên; chưa có nghiệm thu cá nhân cho candidate này.

## Phần còn phải làm sau assessment

Khôi phục thực cần hợp đồng reset/request-ack với PLC, epoch dữ liệu mới, xác
nhận trạng thái vật lý và tái đồng bộ vị trí/phôi trước khi tạo lệnh chuyển động.
Phải thiết kế riêng đường xử lý tải đang giữ và mất xác nhận chân không; không
dùng một nút xóa lỗi chung cho mọi nguyên nhân. Các nội dung đó chưa triển khai.
CAD V5 và plant chức năng MuJoCo cũng chưa đồng bộ toàn bộ; số đo và feedback
thật còn thiếu không được tự lấp bằng trạng thái mô phỏng.
