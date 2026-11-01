# Kiểm chứng theo ma trận — ngày 31/10/2026

Hạng mục này **mở rộng công cụ đo và kiểm chứng**, không thay thuật toán giảm tốc
đang có. Candidate mới: `candidate-20261031-robustness`; chưa được người dùng
kiểm nghiệm hoặc nghiệm thu trên máy vật lý.

## Đã làm gì, dùng để làm gì?

| Tệp/phần bổ sung | Chức năng | Tác dụng |
|---|---|---|
| `mujoco/check_robustness.py` | Tạo cặp bật/tắt chính sách theo cùng scenario và seed; chạy MuJoCo, đánh giá và tổng hợp. | Thấy được giới hạn ngoài các ca demo thuận lợi. |
| `mujoco/experiments/robustness_20261031.json` | 13 scenario × 3 seed × 2 chính sách = 78 lượt. | Thay ma trận thử bằng JSON, không sửa thuật toán. |
| `mujoco/experiments/robustness_smoke.json` | 3 scenario × 1 seed × 2 chính sách = 6 lượt. | Kiểm tra nhanh/CI; không thay thế ma trận đầy đủ. |
| `mujoco/test_robustness.py` | Kiểm tra ghép cặp, giới hạn patch/tên, phân biệt DONE/HOLD và tổng hợp sai số. | Tránh tổng hợp sai hoặc chấm HOLD thành đặt phôi thành công. |
| `report.md`, `report.json`, `groups.csv` | Báo cáo tự sinh sau từng lượt. | Thành viên đọc bảng tổng kết, phân tích số liệu và truy ngược từng ca. |
| `study_manifest.json`, `plan.json`, `base_config.json` | Hash kế hoạch/driver, kế hoạch và cấu hình nền thực dùng. | Biết kết quả thuộc phiên bản và bộ tham số nào. |
| Docker/launcher/PowerShell | Thêm `robustness-check`, tùy chọn `-Plan`, mount kế hoạch chỉ đọc. | Chạy lại cùng thí nghiệm trên máy khác; giữ candidate trước. |

Các lần chạy vẫn có cấu hình hiệu lực, hash nguồn, model XML, nhật ký cảm biến,
quyết định, chính sách và ground truth riêng. Chương trình giữ cả ca lỗi/exception,
ghi báo cáo trước khi trả exit code khác 0 nếu vi phạm tiêu chí.

## Ma trận hiện tại

Các seed: 0, 1, 2. Mỗi scenario chạy cả `disabled` và `enabled`; khác nhau ở bật
tắt chính sách tái cấu hình, các tham số khác của cùng cặp giữ nguyên.

| Scenario | Thay đổi so với cấu hình nền |
|---|---|
| `nominal` | Không thay đổi |
| `delay20` | Trễ 20 ms |
| `delay40` | Trễ 40 ms |
| `jitter` | Trễ danh định 10 ms, jitter đều ±15 ms, cắt tại 0 |
| `loss5` | Xác suất mất mẫu 5% |
| `combined` | Trễ 20 ms, jitter ±10 ms, mất mẫu 5% |
| `loss_all` | Mất toàn bộ dữ liệu |
| `old_data` | Trễ 120 ms |
| `belt_scale90` | Hệ số tốc độ plant băng dài 0,9 |
| `belt_scale110` | Hệ số tốc độ plant băng dài 1,1 |
| `mass150` | Khối lượng phôi 0,03 kg, bằng 150% giá trị nền |
| `pickup_missing` | Quang tại điểm gắp kẹt 0 từ t=0 |
| `upstream_missing` | Quang đầu băng dài kẹt 0 từ t=0 |

Đây là các biến thiên tổng hợp để thử thuật toán, không phải số đo mới. Khi đổi
hệ số plant, không sửa tham số estimator tương ứng để giúp bộ ước lượng biết
trước đáp án. Controller vẫn không đọc ground truth hoặc nhãn fault fixture.

Budget predictor là **1 giây** cho kiểm chứng chức năng. Không diễn giải kết quả
thành đã bảo đảm deadline vận hành 20 ms. Các profile vận hành giữ nguyên 20 ms.

## PASS thực sự có nghĩa gì?

Một lượt đạt tiêu chí khi:

1. DONE và evaluator chấm đặt phôi đúng; **hoặc** HOLD và evaluator chấm phôi còn
   trong vùng hỗ trợ theo tiêu chí hình học hiện có.
2. Trong DEGRADED/TRACK, tốc độ sau chính sách không vượt cap.
3. Chính sách bật có nhật ký; chính sách tắt không sinh các dòng quyết định giả.

Đây là tiêu chí kiểm tra mô phỏng hữu hạn. Không phải xác nhận an toàn toàn bộ
quỹ đạo, E-stop công nghiệp hoặc khả năng giữ tải treo. Bảng vẫn ghi riêng số
DONE, HOLD, exception và vi phạm; **78 lượt đạt tiêu chí không có nghĩa 78 lượt
đều sản xuất thành công**.

Sai số nguồn-thời-gian được so với biên bất định ở từng nhịp có ước lượng:
`error_bound_samples_within / error_bound_samples`. Coverage này chỉ mô tả các
mẫu đã quan sát, có tương quan thời gian; biên chưa được hiệu chuẩn và không phải
khoảng tin cậy thống kê. Coverage không được âm thầm dùng để đổi tiêu chí PASS.

HOLD khi không có lỗi cảm biến chủ động gây ra chưa thể gọi là HOLD nhầm: độ
trễ, khoảng khuyết và bất định vẫn có thể yêu cầu dừng. Chênh lệch thời gian chu
trình chỉ tính khi cả hai ca DONE. Với hai ca HOLD, chênh lệch thời điểm HOLD là
phản ứng sớm hơn, không phải dự đoán trước lỗi.

Cùng seed là cùng kế hoạch ngẫu nhiên ban đầu; khi chu trình có độ dài khác,
số mẫu và chuỗi thời điểm nhận cũng khác. Các ca không có ngẫu nhiên không trở
thành thử nghiệm độc lập chỉ vì đổi seed. Không suy ra kết quả tổng quát hoặc
độ chính xác phát hiện lỗi từ ba seed này.

## Chạy từng bước

```powershell
Set-Location 'C:\Users\Admin\Documents\ChatGPT\plc'

# 6 lượt kiểm tra nhanh
.\scripts\docker_dt.ps1 -Mode robustness-check -Plan robustness_smoke.json

# Ma trận đầy đủ 78 lượt
.\scripts\docker_dt.ps1 -Mode robustness-check
```

Kết quả nằm ở thư mục mới `output/docker/robustness-check_...`; launcher in đường
dẫn khi bắt đầu. Mở **report.md** trước, sau đó **groups.csv**, **report.json**
và thư mục ca muốn xem. Trong từng ca:

- `summary.json`: lý do DONE/HOLD, sai số và kết quả evaluator.
- `controller.jsonl`, `reconfiguration.jsonl`: thuật toán đã thấy gì và chọn gì.
- `ground_truth.jsonl`: đáp án chỉ dùng để đánh giá, không đưa vào controller.
- `effective_config.json`: toàn bộ tham số thật sự dùng cho ca đó.

Muốn đổi ma trận, sao chép plan trong `mujoco/experiments`, chỉnh seed hoặc
scenario rồi dùng `-Plan ten_moi.json`. File plan không phải machine profile;
`-Config` dùng cho profile máy. Compose gắn plan ở `/plans` chỉ đọc.

Chỉ cho phép patch một số trường plant/mạng; tên scenario không nhận đường dẫn.
Toàn bộ job được kiểm tra trước khi tạo đầu ra, tối đa 200 lượt. Không ghi đè
lượt trước. Muốn thay tham số chính sách, tạo machine profile riêng rồi truyền
cùng `-Config` và `-Plan`.

## Diễn giải và hướng phát triển

Docker candidate mới qua **68 kiểm tra logic**, **6 lượt smoke**, **15 kịch bản
tái cấu hình hồi quy**, demo đặt phôi và strict HOLD. Hai kiểm tra biên đóng gói
trên host cũng đạt. Hash lõi điều khiển không đổi so với candidate tái cấu hình;
đợt này không sửa ngưỡng để cải thiện kết quả.

Image: `sha256:31f56fd0c6aa724efaed3148f7df89fa8f7e21c23994062fe7e804cdfbf0169e`.
Hồ sơ nguồn/kết quả: `docker/evidence/candidate-20261031-robustness.json`.
Các image trước được giữ nguyên; chưa có xác nhận cá nhân của người dùng cho
candidate này và chưa chạy CI trên GitHub.

Lượt phát triển ban đầu có 78/78 lượt đạt tiêu chí hỗ trợ/đặt phôi và cap. Trong
39 lượt mỗi chính sách, tắt chính sách có 16 DONE/23 HOLD; bật có 19 DONE/20 HOLD.
Đây là tổng của ma trận được chọn, không phải xác suất hoàn tất máy thật.

Kết quả đáng chú ý là jitter không luôn được cải thiện: có seed mà bật chính
sách hoàn tất còn đối chứng HOLD, và có seed với kết quả ngược lại. Chưa đủ dữ
liệu để quy riêng nguyên nhân cho thuật toán, ma sát hay thời điểm lấy mẫu; cần
phân tích log, không loại seed bất lợi khỏi báo cáo.

Trong Docker candidate mới, ma trận đầy đủ cũng ghi nhận **78/78 đạt tiêu chí**,
với cùng tổng 16 DONE/23 HOLD khi tắt và 19 DONE/20 HOLD khi bật chính sách.
Không có exception, vi phạm cap hoặc ca không đạt tiêu chí đặt/giữ phôi cuối lượt.
Sai số của 2.905/2.905 mẫu đối chứng và 3.224/3.224 mẫu bật chính sách nằm trong
biên bất định tại nguồn, trong TRACK/ALIGN của ma trận này. Kết quả coverage hữu
hạn này không hiệu chuẩn hay chứng minh biên đúng trong các tình huống khác.

Báo cáo đầy đủ nằm tại
`output/docker/robustness-check_20261030T171309Z_f1975325/report.md`.
Tên thư mục lượt chạy dùng UTC, còn ngày tài liệu dùng Asia/Saigon nên có thể lệch
ngày. Các log và kết quả của lượt phát triển ban đầu vẫn được giữ riêng.

Giới hạn tiếp theo cần xử lý là chọn tốc độ có xét biên bất định và tuổi dữ liệu,
thay vì chỉ một cap cố định. Trước khi thay thuật toán, giữ ma trận này làm đối
chứng, kiểm tra sai số/coverage và vùng hoạt động theo từng kịch bản. Không nới
ngưỡng gắp chỉ để làm số DONE đẹp hơn. Tự reset HOLD, mạng PLC thật, đa phôi,
ML/RL và đồng bộ toàn bộ CAD V5 vẫn chưa triển khai trong hạng mục này.
