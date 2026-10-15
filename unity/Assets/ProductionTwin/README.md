# Production Twin V4 — bàn giao cho Unity

## Mở scene

1. Sao chép thư mục `Assets/ProductionTwin` vào `Assets` của một dự án Unity.
2. Đợi Unity biên dịch, chọn **Tools → Production Twin → Build Scene**.
3. Mở `Assets/ProductionTwin/ProductionTwin.unity`. Chọn `Production Twin V4` để chỉnh `ProductionTwinRuntime` trong Inspector.

Scene được dựng từ `parts.csv` bằng primitive có sẵn của Unity. Năm OBJ (`static.obj`, `x.obj`, `y.obj`, `z.obj`, `pusher.obj`) là các lưới tham chiếu của cùng bản bố trí. Mỗi tọa độ trong scene dùng mét: 1 Unity unit = 1 m. CSV và script CAD dùng mm. Trục CAD `(X,Y,Z)` đổi thành Unity `(X,Z,Y)`.

## Vật liệu hiển thị

Scene mới dùng camera gần hơn, nền tối, ánh sáng nền và bóng mềm. Trong `My project`, cấu hình PC URP đã đặt MSAA 4× và Render Scale 1,2 để giảm răng cưa; khi chuyển gói sang dự án khác, đặt hai thông số này trong URP Asset của dự án đó. Game view có thể phóng to bằng cách nhấp đúp tab **Game**.

Fusion 360, CAD Viewer GLB và Unity dùng chung quy ước màu: khung nhôm bạc, ty và con lăn xám thép, đai băng tải xanh, tấm đế than, sáu hộp tím nhạt, thân cảm biến vàng với mặt quang đen, vỏ PLC/động cơ xám đậm, nút nhấn đỏ/vàng/xanh và phụ kiện khí nén xanh/đen. Unity Builder tự tạo các material Lit khi dựng scene. Đây là **vật liệu trực quan** dựa trên ảnh; chưa xác định hợp kim, mác thép, polymer, khối lượng riêng, ma sát hoặc độ bền của linh kiện thực. Không dùng chúng để suy ra động lực học hay tải trọng.

## Cụm chuyển động

Trong Unity project, chạy `Tools > Production Twin > Build Scene`, sau đó nhấn Play. `ProductionTwinDemo` tự chạy một chu trình minh họa: băng tải ngang đưa vật tới A1, A1 đẩy sang băng tải dọc, đầu hút lấy vật tại vùng gắp, giàn XY chuyển và thả lần lượt vào sáu hộp. Các vạch tối trên mặt đai cho thấy chiều chuyển động. Tốc độ ba nhóm (`beltSpeedMmPerSecond`, `axisSpeedMmPerSecond`, `cylinderSpeedMmPerSecond`) chỉnh trong Inspector của `Production Twin V4`; bỏ chọn `playOnStart` để chỉ điều khiển bằng `SetPoseMm`. Đây là hoạt ảnh trực quan, chưa có PLC hay mô phỏng tiếp xúc vật lý.

| Transform | Chi tiết | Điều khiển |
|---|---|---|
| `X axis` | Dầm Y di động | `xMm` cộng theo X |
| `Y axis` | Xe gắp, thân xi lanh A2, S3/S4 | `yMm` cộng theo chiều băng tải dọc |
| `A2 down` | Hai ty, tấm đầu ty, đầu hút | `lowerMm` hướng xuống |
| `A1 pusher` | Ty và tấm đẩy | `pusherMm` hướng từ băng tải ngang vào băng tải dọc (+Y) |

Có thể gọi `SetPoseMm(x, y, lower, push)` từ lớp nhận dữ liệu PLC/digital twin. Giá trị là **độ lệch khỏi tư thế vẽ**; không phải tọa độ homing đã hiệu chuẩn. Hành trình minh họa của A1 là 0–110 mm, **chỉ là ước lượng**. Không nối giá trị trực tiếp vào phần cứng khi chưa xác minh giới hạn hành trình, hướng trục và dừng khẩn cấp.

Động cơ ở đầu dầm Y thuộc cụm X và trượt cùng dầm. Hai động cơ tại đầu phải của các ray X thuộc khung tĩnh. Fusion đã kiểm tra ba tư thế tâm đầu gắp: lấy vật `(-180,120)`, hộp gần `(80,75)`, hộp xa `(195,305)` mm. Chu trình Unity đặt mốc gắp tại Y≈170 mm theo PS2; vị trí này cũng nằm trong hành trình vẽ. Ở hộp xa, mép dầm Y còn cách đầu ray X 107,5 mm và mép xe gắp còn cách đầu ray Y 95,5 mm. Các số này là **khoảng hở trong mô hình ước lượng**, chưa phải hành trình cơ khí hoặc giới hạn phần mềm đã hiệu chuẩn.

Đường đi của vật theo ảnh: băng tải ngang đưa vật từ bên phải tới vị trí giao với băng tải dọc; A1 đặt phía trước băng tải ngang, đẩy vật theo +Y qua khe thanh dẫn lên đầu băng tải dọc; băng tải dọc chuyển vật vào vùng gắp. Tâm tấm đẩy trùng tâm băng tải dọc. Khi thu về, tấm đẩy ở ngoài mép băng tải ngang; khi tiến 110 mm, mép tấm đẩy đến đầu băng tải dọc. Hai thanh dẫn của băng tải ngang được ngắt tại khe chuyển vật. Chiều chuyển động và vị trí tương đối lấy từ ảnh/video; hành trình và kích thước vẫn cần đo thực tế.

PS1 và PS2 đều được đặt bên trái băng tải dọc, thân hướng vào tâm đai theo ảnh tổng thể. Vật đi theo +Y sau khi A1 đẩy: PS1 tại Y≈−65 mm xác nhận vật đã qua vùng chuyển băng; PS2 tại Y≈170 mm là mốc dừng để gắp. Tâm quang cao hơn mặt đai khoảng 16 mm, đối diện thân vật mô phỏng cao 22 mm. Hai gá có chân tới mặt dưới khung băng tải. Các tọa độ và khoảng cách phát hiện là **ước lượng từ ảnh**; cần đo và hiệu chuẩn trên máy. Trong Play mode, `ps1Detected`/`ps2Detected` là trạng thái quang **mô phỏng** theo vị trí vật; `ps1PulseCount`/`ps2PulseCount` đếm cạnh phát hiện để đối chiếu chu trình.

## Bản đối chiếu ảnh và độ tin cậy

Ảnh tổng thể ngày 15/10/2026 xác nhận: hai băng tải chữ L, giàn XY ba động cơ bước, sáu hộp 2 cột × 3 hàng, hai cảm biến quang, PLC ở bên phải, hai van và bảng nút ở mép trước. Bảng nút được đặt theo thứ tự nhìn từ trên: E-Stop, Reset (màu vàng trong ảnh), Stop, Start. Ảnh cận cho thấy **E3F-DS30C4** trên cảm biến quang, **EAGLE-A 4V210-08** trên van, **TN10X75-S** trên A2. Trên cuộn van đọc được DC24V, 4.8W, 200mA. Tên S1–S4, van hút Y3 và công tắc áp suất giữ theo sơ đồ chức năng; mã sản phẩm thực chưa được chốt.

| Kích thước trong mô hình | Giá trị dùng | Mức chắc chắn |
|---|---:|---|
| Tấm đế | 760 × 1000 × 12 mm | Ước lượng từ ảnh; cần đo, sai khác có thể trên 20% |
| Băng tải dọc | 510 × 100 mm; mặt đai 490 × 78 mm | Ước lượng; cần đo |
| Băng tải ngang | 610 × 95 mm; mặt đai 590 × 73 mm | Ước lượng; cần đo |
| Hộp | 104 × 104 × 78 mm, tường 4 mm | Ước lượng; cần đo |
| Khung nhôm | Tiết diện 20 mm, đỉnh cao 300 mm | Ước lượng; cần đo |
| Cảm biến quang | Thân M18, dài vẽ 58 mm | M18 và mã đọc từ ảnh; chiều dài vẽ ước lượng |
| A2 | Nhãn TN10X75-S; hành trình danh nghĩa 75 mm | Nhãn đọc từ ảnh; vị trí lắp và vỏ ước lượng |
| Van Y1/Y2 | Nhãn 4V210-08 | Mã đọc từ ảnh; kích thước khối ước lượng |

Sai số của các kích thước ước lượng **không phải dung sai chế tạo**; hiện chưa có thước chuẩn trong ảnh để xác định sai số bằng đo lường. Không dùng mesh này để thiết kế gá lắp hay kiểm tra va chạm cơ khí chính xác. Đo tối thiểu dài/rộng đế, băng tải, hộp, cao khung, vị trí gốc và hành trình thực rồi cập nhật script CAD, sau đó chạy lại `python scripts/export_unity_twin.py`.

## Tín hiệu dự kiến để nối digital twin

Theo sơ đồ điện đã gửi: I0.4/I0.5 = S1/S2 A1, I0.6/I0.7 = S3/S4 A2, I1.0/I1.1 = PS1/PS2, I1.2 = Vacuum_OK, I1.3–I1.5 = home X/Y1/Y2; Q0.0/Q0.1 = Y1/Y2, Q0.2 = Y3, Q0.3/Q0.4 = motor băng tải, Q0.5–Q1.2 = STEP/DIR. Đây là **mapping của sơ đồ**, chưa xác nhận đấu nối PLC thực. `ProductionTwinRuntime` mới nhận tư thế để vẽ; đường truyền PLC, xử lý lỗi và logic điều khiển an toàn cần triển khai và thử riêng.

## Kiểm tra đã làm

`python scripts/export_unity_twin.py` tạo CSV, 5 OBJ và ảnh chiếu bằng từ cùng script Fusion. Kiểm tra hình học xác nhận tấm đẩy A1 đồng tâm với băng tải dọc, ở cao độ mặt đai, bắt đầu ngoài mép băng tải ngang, tới đầu băng tải dọc khi tiến 110 mm, ty vẫn nối với thân xi lanh, và hai thanh dẫn chừa khe cho tấm đẩy. Kiểm tra thêm hai mặt quang cùng ở cạnh trái băng tải dọc, PS1 trước PS2 theo chiều chạy, tia nhìn ngang đi qua cao độ vật, chân gá chạm khung băng tải, khớp nối thân A2 với xe gắp, bảng nút không chồng động cơ và đúng thứ tự. Script Fusion `fusion/ProductionTwin_V0/ProductionTwin_V0.py` là nguồn bố trí cho Fusion, CSV, GLB và Unity.

CAD Viewer có hai trạng thái ở `output/cad`: `production_twin_v4_viewer.glb` (A1 thu về) và `production_twin_v4_a1_extended.glb` (A1 tiến 110 mm). Đây là lưới xem trước từ CSV, không phải STEP cơ khí đo lường.
