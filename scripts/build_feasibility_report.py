from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf' / 'bao_cao_kha_thi_network_aware_predictive_digital_twin.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
FONT = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Arial', str(FONT / 'arial.ttf')))
pdfmetrics.registerFont(TTFont('Arial-Bold', str(FONT / 'arialbd.ttf')))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold')

navy = colors.HexColor('#103054')
blue = colors.HexColor('#16649a')
light = colors.HexColor('#eaf2f8')
muted = colors.HexColor('#526578')
green = colors.HexColor('#1a735d')
amber = colors.HexColor('#b35a0a')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleVN', fontName='Arial-Bold', fontSize=19, leading=25, textColor=navy, spaceAfter=11))
styles.add(ParagraphStyle(name='SubVN', fontName='Arial', fontSize=10, leading=15, textColor=muted, spaceAfter=8))
styles.add(ParagraphStyle(name='H1VN', fontName='Arial-Bold', fontSize=13, leading=18, textColor=navy, spaceBefore=11, spaceAfter=6))
styles.add(ParagraphStyle(name='H2VN', fontName='Arial-Bold', fontSize=10.3, leading=15, textColor=blue, spaceBefore=8, spaceAfter=4))
styles.add(ParagraphStyle(name='BodyVN', fontName='Arial', fontSize=8.6, leading=13.5, spaceAfter=5))
styles.add(ParagraphStyle(name='SmallVN', fontName='Arial', fontSize=7.5, leading=11, spaceAfter=3))
styles.add(ParagraphStyle(name='CellVN', fontName='Arial', fontSize=7.3, leading=10.8))
styles.add(ParagraphStyle(name='CellHeadVN', fontName='Arial-Bold', fontSize=7.4, leading=10.8, textColor=colors.white))
styles.add(ParagraphStyle(name='CaptionVN', fontName='Arial', fontSize=7.4, leading=10.5, textColor=muted, alignment=TA_CENTER, spaceAfter=5))

P=lambda s,sty='BodyVN': Paragraph(s, styles[sty])
story=[]
def h(s): story.append(P(s,'H1VN'))
def h2(s): story.append(P(s,'H2VN'))
def para(s): story.append(P(s))
def bullets(items):
    for x in items: story.append(P('• '+x))
def table(rows,widths=None,header=True):
    data=[[P(str(c),'CellHeadVN' if header and i==0 else 'CellVN') for c in row] for i,row in enumerate(rows)]
    t=Table(data,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    cmds=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#cfdae3'))]
    if header: cmds += [('BACKGROUND',(0,0),(-1,0),navy),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8fb')])]
    t.setStyle(TableStyle(cmds));story.append(t);story.append(Spacer(1,5*mm))
def page(): story.append(PageBreak())

story += [P('BÁO CÁO ĐÁNH GIÁ KHẢ THI','TitleVN'),P('Network-Aware Predictive Digital Twin for Resilient and Self-Reconfigurable Cyber-Physical Production Systems','SubVN'),P('Áp dụng cho mô hình phân loại và gắp sản phẩm tự động | cập nhật theo thông tin người dùng ngày 11/10/2026','SmallVN')]
table([['Kết luận đề xuất','Mức đánh giá'],['Twin giám sát, dự báo tiến độ/lỗi và tự chọn chế độ vận hành trên thiết bị hiện có','Khả thi cao (≈ 8/10), sau khi đối chiếu I/O và thu thập dữ liệu'],['Tự đổi tham số, thời điểm kích hoạt và trình tự khi tốc độ thay đổi hoặc mất cảm biến không trọng yếu','Khả thi có điều kiện (≈ 7/10), tùy khả năng điều tốc và mức quan sát còn lại'],['Tiếp tục chu kỳ tự động khi mất cảm biến xác nhận giữ vật, home hoặc E-stop','Không được mặc định khả thi; thiếu bằng chứng trạng thái an toàn']], [127*mm,55*mm])
para('<b>Luận điểm chính.</b> “Tự tái cấu hình” trong báo cáo này là thay đổi <b>phần mềm</b>: tự chọn mode, tham số tốc độ/timeout, lịch kích hoạt, nguồn tín hiệu thay thế và trình tự xử lý trên cùng cơ cấu. Twin dùng đồng thời trạng thái thiết bị, tiến độ sản phẩm và chất lượng mạng để dự báo và chọn chính sách; PLC vẫn giữ điều khiển thời gian thực và liên động tại chỗ. Không yêu cầu thêm băng tải hoặc đầu hút dự phòng.')
para('<b>Ranh giới bằng chứng.</b> Người dùng xác nhận CPU 1214C DC/DC/DC, hai cảm biến quang và tất cả xi lanh có cảm biến báo hai đầu hành trình. Chương trình TIA Portal chưa viết; hiện đang mô phỏng khí nén và băng tải trên Automation Studio. Camera Hikvision DS-U02 là khả năng bổ sung, chưa thuộc cấu hình bắt buộc. Chưa có bản vẽ đấu dây hoàn công, firmware, module DO, profile driver, tốc độ băng tải, chu kỳ gắp hoặc log mạng. Mọi số liệu hiệu năng và ngân sách phía sau là <b>mục tiêu thiết kế / phép tính minh họa</b>, chưa phải kết quả đo trên máy.')
h('1. Hiện trạng suy ra từ hình')
table([['Hạng mục','Hiện trạng và điểm cần xác minh'],['Điều khiển','Đã xác nhận CPU S7-1200 1214C DC/DC/DC. TIA Portal chưa viết; cần kiểm kê firmware, module DO, đấu dây thực và backup trước khi nạp chương trình.'],['Cơ cấu','Theo sơ đồ: 2 băng tải DC, 2 xi lanh khí nén, 1 giác hút Venturi, 3 trục bước X/Y1/Y2. Mô phỏng khí nén và băng tải đang được thực hiện trên Automation Studio.'],['Tín hiệu','Người dùng xác nhận mọi xi lanh đều có cảm biến hai đầu hành trình và có 2 cảm biến quang. Sơ đồ chỉ rõ 14 DI (I0.0-I1.5) và 13 DO (Q0.0-Q1.4); phải đối chiếu với đấu dây thực.'],['Bổ sung tùy chọn','Camera Hikvision DS-U02 có thể lắp để quan sát sản phẩm/cơ cấu; encoder băng tải, áp suất analog và phản hồi driver chưa được xác nhận có sẵn.']], [35*mm,147*mm])
para('<b>Điểm nghẽn I/O trước khi viết TIA.</b> CPU 1214C DC/DC/DC có 14 DI, 10 DO và 2 AI tích hợp [1]. Sơ đồ yêu cầu 13 DO, vì vậy phải xác nhận có module mở rộng hay khác biệt giữa sơ đồ và máy thật. STEP trong sơ đồ đang gán Q0.5/Q0.7/Q1.1, trong khi ví dụ 1214C của Siemens gán xung PTO Q0.0-Q0.3 và DIR Q0.4-Q0.7 [2]. Nếu driver nhận xung trực tiếp từ PLC, cần remap STEP sang ngõ PTO hợp lệ và bố trí lại các tải còn lại. Đây là điều kiện chặn trước khi nạp chương trình thực.')
page()

h('2. Định nghĩa bài toán và mức tự tái cấu hình')
para('<b>Đối tượng số</b> gồm từng sản phẩm, hai băng tải, giàn 3 trục, xy lanh, chân không, PLC, máy biên và liên kết mạng. Twin đồng bộ sự kiện PLC với trạng thái mạng, ước lượng thời gian hoàn thành và xác suất hoàn tất thao tác. Network-aware có nghĩa chất lượng mạng là biến đầu vào của dự báo/quyết định, không chỉ là biểu đồ ping.')
table([['Mức','Hành vi phần mềm trên cell','Giới hạn'],['0 - quan sát','Twin ước lượng trạng thái, thời gian chu kỳ, cảnh báo lệch dự báo.','Không ghi PLC.'],['1 - điều chỉnh tham số','Tự chọn tốc độ nếu drive hỗ trợ, thời gian chờ, nhịp cấp phôi, thời điểm gắp theo recipe.','PLC kiểm min/max và interlock.'],['2 - đổi logic theo lỗi','Thay tín hiệu PS hỏng bằng ước lượng từ tín hiệu còn lại + thời gian chạy khi đủ độ tin cậy; retry hoặc bỏ qua sản phẩm không chắc chắn.','Không thay thế E-stop, home hoặc xác nhận hút bằng suy đoán.'],['3 - tự chọn chính sách','Bộ giám sát chọn Normal/Degraded/Local/Stop từ xác suất lỗi, độ tươi dữ liệu và ràng buộc sản xuất.','PLC phê chuẩn chuyển mode; chứng minh bằng fault injection.']], [30*mm,83*mm,69*mm])
para('<b>Giới hạn quan trọng về tốc độ:</b> sơ đồ chỉ thể hiện K1/K2 đóng/cắt động cơ DC, chưa thể hiện driver nhận lệnh tốc độ. Nếu máy thật chỉ có contactor, phần mềm không thể tạo điều tốc liên tục; có thể đổi nhịp cấp phôi và tốc độ trục bước, nhưng cần xác minh drive băng tải trước khi đặt mục tiêu thay đổi tốc độ băng tải. Không dùng đóng/cắt contactor liên tục như một bộ PWM giả. Camera tùy chọn có thể xác nhận vị trí/loại sản phẩm, song phải đo độ trễ hình ảnh và khả năng hoạt động khi ánh sáng thay đổi.')
h('3. Kiến trúc đề xuất')
para('<b>Tầng OT:</b> PLC giữ E-stop, interlock hành trình, chống va chạm, PTO, van và trình tự chu kỳ. <b>Tầng edge:</b> một IPC/mini PC lấy dữ liệu 10-20 Hz (50-100 ms/mẫu) cho sự kiện quan trọng; lưu time-series và event log; chạy mô hình trạng thái + dự báo; giám sát RTT, jitter, mất gói, tuổi dữ liệu và tình trạng phiên. <b>Tầng ứng dụng:</b> dashboard, thử kịch bản, nhật ký quyết định. Đường mạng khuyến nghị PLC - switch công nghiệp - edge trong VLAN/zone OT, không đưa điều khiển ra cloud.')
para('Giao tiếp ưu tiên <b>OPC UA read-only</b> nếu CPU/firmware/license xác nhận hỗ trợ và tải chấp nhận được; Siemens công bố OPC UA server từ firmware S7-1200 V4.4 [3]. Phương án tương thích là S7/Modbus TCP qua gateway đọc DB, chỉ mở các biến lệnh whitelist khi kiểm thử mức 2. OPC UA có mô hình bảo mật phiên, xác thực và mã hóa [4]; không mặc định rằng PLC trong ảnh đã bật tính năng này.')
h2('Luồng dữ liệu và quyết định')
table([['Nhóm tag','Tốc độ khởi đầu','Dùng cho'],['S1-S4, PS1-PS2, Vacuum_OK, Home X/Y1/Y2, mode, fault, product ID','Theo thay đổi + snapshot 50-100 ms','State estimation, phát hiện thiếu sự kiện, timeout.'],['STEP/DIR command, target position, motion busy/done, cycle counter, recipe','20-100 ms / theo sự kiện','Đồng bộ twin, dự báo hoàn thành.'],['RTT, jitter, loss, disconnect, age of last good sample','1 s; sự kiện khi vượt ngưỡng','Điều chỉnh độ tin cậy và chính sách ghi.'],['Dòng/áp động cơ, áp chân không analog, encoder (nếu bổ sung)','10-100 ms tùy thiết bị','Dự báo suy giảm cơ cấu; không thể suy ra từ tín hiệu on/off đơn lẻ.']], [73*mm,37*mm,72*mm])
para('<b>Đồng bộ thời gian:</b> PLC/edge cùng nguồn NTP trong OT; ghi timestamp tại nguồn nếu có, và timestamp nhận tại edge. Phân biệt “sensor event xảy ra muộn” với “gói tin đến muộn”. Với 30-50 biến, mỗi biến 10 Hz và bản ghi khoảng 64 byte, lưu lượng thô xấp xỉ 19-32 kB/s, 1,7-2,8 GB/ngày trước nén; đây là ước lượng để chọn lưu trữ, không phải băng thông mạng đo được.')
page()

h('4. Mô hình dự báo và chính sách resilience')
h2('4.1 Twin lai, có thể triển khai trong một học kỳ')
bullets(['Mô hình rời rạc: <b>Idle → Feed → Detect → Pick → Verify Vacuum → Move → Release → Return → Done</b>; mỗi trạng thái có guard, timeout và nguyên nhân lỗi. Gắn product ID theo sự kiện PS1/PS2; nếu không có nhận dạng loại sản phẩm thì loại hàng phải đến từ recipe hoặc bổ sung cảm biến/camera.','Mô hình thời gian: học phân bố thời gian theo recipe, vị trí, tải và trạng thái mạng. Bắt đầu bằng quantile/gradient boosting hoặc survival model đơn giản; chỉ dùng ML phức tạp khi baseline kém.','Mô hình mạng: mất kết nối, tuổi bản tin, RTT p50/p95/p99, jitter và loss. Dự báo có khoảng tin cậy tăng khi telemetry cũ. PLC vẫn điều khiển cục bộ khi edge mất kết nối.'])
para('<b>Do mọi xi lanh đã có hai cảm biến đầu hành trình:</b> ưu tiên giám sát chuỗi lệnh van → rời đầu cũ → tới đầu mới; báo lỗi khi quá thời gian hoặc hai đầu cùng báo bất khả thi. Ước lượng chỉ cần cho trạng thái giữa hành trình và thời điểm hoàn thành dự kiến. Bước triển khai đầu là hoàn thiện mô phỏng Automation Studio, xuất bảng tín hiệu/trình tự/timeout, rồi mới lập state machine trong TIA Portal và thu log thực để hiệu chuẩn twin.')
para('<b>Quy tắc quyết định minh họa:</b> nếu tuổi dữ liệu &gt; 300 ms hoặc thiếu ACK trong 500 ms thì edge khóa mọi lệnh mới; PLC hoàn tất chuyển động an toàn hoặc dừng theo trạng thái. Nếu Vacuum_OK còn đáng tin nhưng không lên trong T_vac được hiệu chuẩn (khởi đầu 0,8 s), PLC có thể retry tối đa 1 lần theo liên động. Nếu chính cảm biến Vacuum_OK hỏng hoặc không xác định được, không tiếp tục gắp/thả tự động. Các ngưỡng phải lấy từ log và thử nghiệm, không dùng trực tiếp như giá trị an toàn.')
table([['Sự cố','Twin dự báo/nhận biết','Tái cấu hình phần mềm hợp lệ'],['Đổi tốc độ băng tải','Thời gian đi giữa PS1-PS2 thay đổi, ETA cũ sai.','Ước lượng lại thời gian vận chuyển và cửa sổ gắp; đổi tốc độ nếu drive có giao diện tốc độ.'],['PS1 hoặc PS2 stuck','Sensor không chuyển trạng thái dù chu kỳ/sensor khác vẫn đổi.','Chuyển sang mode Degraded: suy ra vị trí từ sự kiện còn lại + mô hình thời gian, tăng khoảng bất định; chỉ thao tác khi còn đủ xác nhận.'],['Trễ mạng 100-300 ms / mất gói','Tuổi dữ liệu tăng; quyết định của edge dễ dựa trên trạng thái cũ.','Giảm quyền edge xuống chỉ quan sát; PLC dùng chính sách local đã lưu.'],['Vacuum_OK mất hoặc không xác nhận','Không biết chắc sản phẩm đã được giữ.','Dừng chu kỳ gắp tự động, báo kiểm tra; không coi bộ đếm thời gian là bằng chứng giữ vật.'],['Home / hành trình hoặc E-stop bất thường','Không xác minh được vị trí trục hoặc điều kiện an toàn.','Không tự bỏ qua tín hiệu; dừng theo logic an toàn và yêu cầu kiểm tra.']], [42*mm,63*mm,77*mm])
para('<b>Ước lượng khi hỏng cảm biến:</b> nếu sản phẩm còn được phát hiện tại một điểm và khoảng cách đến điểm gắp là 0,30 m, ở tốc độ 0,15 m/s thời gian đến dự kiến là 2,0 s. Sai số tốc độ ±10% có thể tạo sai số vị trí cỡ ±30 mm trên quãng này, chưa tính trượt băng tải và độ trễ phát hiện. Vì vậy “virtual sensor” chỉ hợp lệ nếu sai số đã đo nhỏ hơn cửa sổ gắp và vẫn có tín hiệu khác xác nhận; nếu không phải bỏ qua sản phẩm hoặc dừng, không gắp mù.')
h2('4.2 Ranh giới an toàn và an ninh')
para('E-stop phải cắt năng lượng nguy hiểm theo mạch an toàn đã được đánh giá; tín hiệu I0.0 chỉ được xem là giám sát trạng thái, không thay chức năng an toàn. Lệnh từ twin đi qua whitelist, số thứ tự và TTL; PLC kiểm mode, E-stop, home, timeout và cho phép trước khi thực thi. Tách mạng OT/IT thành zone và conduit, áp quyền tối thiểu và log mọi lệnh theo nguyên tắc ISA/IEC 62443 [5]. Không thử gây lỗi trực tiếp trên mạng sản xuất chưa được cách ly.')
page()

h('5. Thiết kế thí nghiệm có thể công bố')
para('<b>Baseline:</b> đo ít nhất 1.000 chu kỳ bình thường ở 2-3 recipe và 3 mức tốc độ; lưu kết quả thành công, chu kỳ, thời điểm sensor, chuyển trạng thái, thời gian hút/di chuyển, lỗi và dữ liệu mạng. Chia tập train/test theo phiên chạy hoặc ngày, tránh chia ngẫu nhiên các chu kỳ liên tiếp vì sẽ rò rỉ điều kiện vận hành.')
table([['Kịch bản','Tác động mạng/thiết bị','So sánh A/B'],['N0','Không bơm lỗi; RTT nội bộ thực đo.','PLC chuẩn vs twin chỉ quan sát (kiểm tra overhead).'],['N1/N2','Trễ 50/100/200 ms, loss 1/3/5%, ngắt 5/15/30 s.','Chính sách cố định vs tự chuyển Local theo tuổi dữ liệu.'],['V1','Đổi tốc độ 0,7/1,0/1,3 lần tốc độ chuẩn nếu drive cho phép.','ETA/cửa sổ gắp cố định vs cập nhật online.'],['S1','Mô phỏng PS1 hoặc PS2 stuck-at-0/stuck-at-1.','Dừng toàn bộ vs mode Degraded có giới hạn tin cậy.'],['S2','Mô phỏng mất Vacuum_OK, Home hoặc E-stop.','Xác nhận hệ thống không tiếp tục thao tác không quan sát được.']], [22*mm,79*mm,81*mm])
para('Mỗi kịch bản tối thiểu 30 lần lặp độc lập, thứ tự chạy xáo trộn; ghi điều kiện cơ khí và operator. Báo cáo median, p95, khoảng tin cậy bootstrap 95% cho chênh lệch; không tuyên bố “tăng năng suất” từ một lượt demo. Với tỉ lệ lỗi hiếm, cần tăng số lần lặp hoặc đưa kết quả thành bằng chứng thăm dò.')
table([['KPI','Cách tính','Ngưỡng nghiệm thu đề xuất'],['Sai số dự báo chu kỳ','MAE và p90(|t_dự báo - t_thực|)','MAE ≤ 0,5 s; p90 ≤ 1,0 s sau hiệu chuẩn.'],['Độ trễ phát hiện sensor','t_cảnh báo - t_bắt đầu lỗi','Median ≤ 1 s cho lỗi có quan sát chéo.'],['Sai số virtual sensor','|x_ước lượng - x_thực| ở điểm gắp','p95 nhỏ hơn cửa sổ gắp đo được; nếu không, không dùng để gắp.'],['Thời gian chuyển mode','t_mode mới ổn định - t_phát hiện','Giảm ≥ 25% so với xử lý thủ công trên lỗi PS có thể chịu được.'],['Tỉ lệ hoàn tất','sản phẩm hoàn tất / sản phẩm đưa vào','Không giảm &gt; 1 điểm % ở N0; báo cáo riêng từng mode.'],['Lệnh không an toàn','Số lệnh vượt interlock/1000 chu kỳ','0; mọi yêu cầu bị PLC từ chối và ghi log.'],['Độ tươi dữ liệu','p95(age of state used for decisions)','≤ 200 ms ở N0; khi &gt; 300 ms ngừng ghi.']], [44*mm,68*mm,70*mm])
para('<b>Ví dụ định lượng, chưa phải dự báo kết quả:</b> nếu chu kỳ 8 s, công suất lý thuyết 450 sản phẩm/giờ. Giả sử 85% thời gian hữu ích, nền đạt 382,5 sản phẩm/giờ. Một mất mạng 60 s mỗi 30 phút gây 2 phút ngừng/giờ, tương đương 12,75 sản phẩm/giờ theo nhịp nền. Nếu chính sách local giảm mỗi lần ngừng còn 15 s, mất 0,5 phút/giờ ≈ 3,19 sản phẩm/giờ; mức thu hồi tối đa trong giả định này ≈ 9,56 sản phẩm/giờ (2,5%). Nếu PLC đã tự chạy local khi mất mạng, lợi ích này bằng 0. Cần đo baseline trước khi dùng trong luận văn.')
page()

h('6. Lộ trình triển khai và nguồn lực')
table([['Giai đoạn','Thời lượng','Đầu ra / điều kiện qua cổng'],['G0 - kiểm kê','1-2 tuần','Đọc mã CPU, firmware, module DO, sơ đồ đấu dây thực, loại driver, topology mạng, E-stop, khả năng backup project. Chốt bảng I/O đúng.'],['G1 - quan sát','2-3 tuần','Gateway read-only, timestamp, event log, dashboard, baseline ≥1.000 chu kỳ, đo tải PLC và mạng.'],['G2 - twin dự báo','3-4 tuần','State machine, replay, dự báo chu kỳ và lỗi, kiểm định trên phiên chạy mới.'],['G3 - resilience','2-3 tuần','Fault injection trên mô phỏng/bench; PLC state machine nhận lệnh có guard; recovery chỉ sau FAT.'],['G4 - đánh giá','2-3 tuần','30 lặp/kịch bản, thống kê, ablation không dùng đặc trưng mạng, báo cáo hạn chế.']], [28*mm,25*mm,129*mm])
para('<b>Tổng lịch:</b> 10-15 tuần với 1 người PLC/OT (khoảng 60-100 giờ), 1 người edge/data (80-140 giờ), giám sát an toàn và thử nghiệm (20-40 giờ). Có thể chồng lấn G1/G2 khi I/O đã chốt. Lịch là ước lượng dự án học thuật, không phải cam kết tiến độ.')
h2('Ngân sách tham khảo để lập đề cương, chưa phải báo giá')
table([['Hạng mục bổ sung','Dự toán (triệu VND)','Lưu ý'],['Mini PC/IPC + SSD + UPS nhỏ','4-9','Có thể dùng máy sẵn có để giảm chi phí.'],['Switch quản lý/thiết bị gây lỗi mạng trong testbed','1,5-4','Có thể dùng phần mềm netem trên gateway Linux.'],['Module DO, đấu nối, dây, cầu chì','2-6','Chỉ mua sau G0; có thể đã lắp sẵn.'],['Cảm biến analog chân không / encoder / tín hiệu driver (tùy chọn)','2-7','Để nâng chất lượng dự báo thiết bị.'],['Tổng phần cứng dự kiến','9,5-26','Không gồm PLC, máy cơ khí, license TIA/OPC và nhân công.']], [90*mm,34*mm,58*mm])
para('<b>Phạm vi tự tái cấu hình phần mềm:</b> nếu dùng PC và mạng sẵn có, chi phí bổ sung có thể khoảng 0-3 triệu VND cho kết nối/testbed. Edge PC riêng là tùy chọn. Các hạng mục cảm biến/encoder trong bảng chỉ phục vụ tăng độ tin cậy quan sát, không phải điều kiện để đổi tuyến vật lý. Tuy nhiên, điều tốc băng tải chỉ khả thi nếu driver hiện hữu nhận tham số tốc độ; nếu chỉ có K1/K2 đóng/cắt, phạm vi thử nghiệm phải đổi nhịp cấp phôi hoặc tốc độ trục bước. Các khoảng tiền là giả định lập kế hoạch, phải xin báo giá khi mua.')
h('7. Triển vọng và quyết định go/no-go')
para('<b>Tiềm năng khoa học:</b> so sánh dự báo dùng và không dùng đặc trưng mạng; twin nhận biết bất định do telemetry trễ; quyết định local/edge dưới mất kết nối; bộ dữ liệu sự kiện PLC + mạng + lỗi cơ cấu có thể công bố nếu chuẩn hóa và ẩn thông tin. <b>Tiềm năng ứng dụng:</b> chuyển từ demo phân loại sang giám sát tình trạng, bảo trì dự báo, recipe động và virtual commissioning. Lợi ích kinh tế chỉ ước lượng sau khi đo downtime và tỷ lệ sản phẩm lỗi thực tế.')
table([['Điều kiện bắt buộc trước G3','Tiêu chí go'],['PTO/I/O','Xác nhận model CPU, DO mở rộng; STEP trên ngõ PTO hợp lệ hoặc driver có bộ phát xung riêng; backup TIA.'],['An toàn','E-stop độc lập, interlock kiểm thử, timeout và mode manual/auto; người có chuyên môn ký biên bản FAT.'],['Quan sát','Tag đủ để biết vị trí/trạng thái hàng và xác nhận hút/thả; nếu không, giới hạn ở khuyến nghị.'],['Mạng','Có mạng OT cô lập cho thử lỗi, log RTT/loss/age và rollback.'],['Mẫu số liệu','Baseline ≥1.000 chu kỳ, định nghĩa KPI trước khi so sánh.']], [55*mm,127*mm])
page()
h('8. Khuyến nghị và nguồn tham khảo')
para('Triển khai G0-G2 ngay trên mô hình này; chỉ mở quyền ghi sau khi giải quyết ánh xạ PTO/DO và chứng minh interlock. Đóng góp chính nên là bộ chọn chính sách Normal/Degraded/Local/Stop, cập nhật tham số online khi tốc độ đổi, và virtual sensor có định lượng bất định khi một PS hỏng. Tên phù hợp: “Network-Aware Predictive Digital Twin with Software Self-Reconfiguration for a PLC-Based Sorting-and-Pick Cell”. Kết luận thực nghiệm phải phân biệt rõ lỗi cảm biến có thể chịu được với lỗi làm mất khả năng xác nhận an toàn.')
h2('Nguồn tham khảo')
sources=[
('[1] Siemens SiePortal, CPU 1214C DC/DC/DC 6ES7214-1AG40-0XB0 (14 DI/10 DO/2 AI; xác nhận theo mã thiết bị).','https://sieportal.siemens.com/en-dz/products-services/detail/6ES7214-1AG40-0XB0'),
('[2] Siemens, Moving PTO positioning axes of an S7-1200 as IO device, Table 2-1: Q0.0-Q0.3 PTO, Q0.4-Q0.7 DIR.','https://cache.industry.siemens.com/dl/files/880/109768880/att_1000798/v1/109768880_S7-1200_LPTO_DOC_V1.0_en.pdf'),
('[3] Siemens, firmware S7-1200 V4.4 bổ sung OPC UA Data Access server.','https://press.siemens.com/global/en/pressrelease/new-firmware-simatic-s7-1500-and-simatic-s7-1200-controllers'),
('[4] OPC Foundation, OPC UA Security Model.','https://reference.opcfoundation.org/specs/OPC-10000-2/full'),
('[5] ISA, ANSI/ISA-62443-3-2:2020, phân vùng zone/conduit và đánh giá rủi ro.','https://www.isa.org/getmedia/661c718f-8e64-446d-acf9-2c6286db1b33/isa-62443-3-2-preview.pdf'),
('[6] NIST, Digital Twins for Advanced Manufacturing: xác thực mô hình và định lượng bất định.','https://www.nist.gov/programs-projects/digital-twins-advanced-manufacturing')]
for label,url in sources:
    story.append(P(label,'SmallVN'));story.append(P(f'<link href="{url}" color="#16649a">{url}</link>','SmallVN'))
h2('Phân loại số liệu trong báo cáo')
para('<b>Người dùng đã xác nhận:</b> CPU 1214C DC/DC/DC, tất cả xi lanh có phản hồi hai đầu, 2 cảm biến quang, TIA chưa viết, Automation Studio đang dùng; camera DS-U02 chỉ là lựa chọn bổ sung. <b>Từ sơ đồ:</b> 14 DI, 13 DO và các tên tín hiệu. <b>Từ tài liệu hãng:</b> I/O tích hợp, ánh xạ PTO ví dụ, OPC UA tùy firmware. <b>Giả định thiết kế:</b> 10-20 Hz, timeout, 1.000 chu kỳ, KPI và ví dụ 8 s/chu kỳ.')
para('<b>Chưa xác minh:</b> firmware, DO mở rộng, STEP/DIR có trùng đấu dây thật, sơ đồ an toàn, áp khí, tốc độ trục/băng tải, loại mạng, license và khả năng điều tốc. Báo cáo là tiền khả thi kỹ thuật; các chỉ tiêu phải đo sau khi có baseline PLC và chạy thử.')

def footer(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setStrokeColor(colors.HexColor('#ccd9e4'));canvas.line(15*mm,15*mm,w-15*mm,15*mm)
    canvas.setFont('Arial',7);canvas.setFillColor(muted)
    canvas.drawString(15*mm,10*mm,'Báo cáo tiền khả thi | Network-Aware Predictive Digital Twin')
    canvas.drawRightString(w-15*mm,10*mm,f'{doc.page}')
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=14*mm,leftMargin=14*mm,topMargin=15*mm,bottomMargin=20*mm,title='Báo cáo tiền khả thi Network-Aware Predictive Digital Twin',author='Codex')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
