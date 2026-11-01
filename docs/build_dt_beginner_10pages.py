"""Build a ten-page Vietnamese primer from the implemented baseline and its logs."""

from pathlib import Path
from html import escape
import hashlib
import json
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                               TableStyle, PageBreak, Image, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderSVG
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/pdf/hieu_loi_digital_twin_10_trang.pdf'
DATA = ROOT/'output/dt_acceptance_20261027_v2'
results = json.loads((DATA/'results.json').read_text(encoding='utf-8'))
assert len(results) == 12 and all(r['pass'] for r in results)
by_case = {r['case']: r for r in results}
nominal = by_case['bin_1']
sensor_rows = [json.loads(l) for l in (DATA/'bin_1/signals.jsonl').read_text().splitlines()]
truth_rows = [json.loads(l) for l in (DATA/'bin_1/ground_truth.jsonl').read_text().splitlines()]
anchors = {k: next(r['source_time_s'] for r in sensor_rows if r['values'][k]) for k in ('ps1','ps2')}
assert abs(anchors['ps2']-anchors['ps1']-1.48) < 1e-8

for name, file in [('Text','arial.ttf'), ('Bold','arialbd.ttf'),
                   ('Italic','ariali.ttf'), ('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Text',normal='Text',bold='Bold',italic='Italic',boldItalic='Bold')
NAVY, TEAL = colors.HexColor('#17384D'), colors.HexColor('#087E8B')
PALE, INK, GRAY = colors.HexColor('#EDF5F7'), colors.HexColor('#243947'), colors.HexColor('#596B76')
W = A4[0]-96
styles = {
    'body': ParagraphStyle('body',fontName='Text',fontSize=10.4,leading=15.1,textColor=INK,spaceAfter=8),
    'title': ParagraphStyle('title',fontName='Bold',fontSize=22,leading=28,textColor=NAVY,spaceAfter=9),
    'sub': ParagraphStyle('sub',fontName='Bold',fontSize=11.2,leading=15,textColor=TEAL,spaceBefore=7,spaceAfter=6,keepWithNext=True),
    'small': ParagraphStyle('small',fontName='Text',fontSize=9.1,leading=12.5,textColor=INK,spaceAfter=5),
    'code': ParagraphStyle('code',fontName='Mono',fontSize=8.4,leading=11.5,textColor=NAVY,backColor=PALE,borderPadding=7,spaceBefore=5,spaceAfter=11),
    'deck': ParagraphStyle('deck',fontName='Text',fontSize=10,leading=14,textColor=GRAY,spaceAfter=12),
}
story, md, sources = [], [], []


def p(text,style='body'):
    story.append(Paragraph(text,styles[style]))
    md.append(text.replace('<b>','**').replace('</b>','**').replace('<br/>','\n'))


def page(n,title,goal,source):
    if story:
        story.append(PageBreak())
    sources.append(source)
    p(f'{n:02d}  {title}','title')
    p(goal,'deck')


def sub(text): p(text,'sub')


def code(text):
    story.append(Paragraph(escape(text).replace(' ','&#160;').replace('\n','<br/>'),styles['code']))
    md.extend(['```text',text,'```'])


def table(head,rows,widths):
    data = [[Paragraph(('<b>'+escape(str(c))+'</b>') if i==0 else escape(str(c)),styles['small'])
             for c in row] for i,row in enumerate([head]+rows)]
    t=Table(data,colWidths=[W*x for x in widths],hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LINEBELOW',(0,0),(-1,0),.8,TEAL),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#DCE5EA')),
    ]))
    story.extend([t,Spacer(1,7)])
    md.extend([' | '.join(head),' | '.join(['---']*len(head))]+[' | '.join(map(str,r)) for r in rows])


def check(question,answer):
    content=Paragraph('<b>Tự kiểm tra:</b> '+question+'<br/><b>Đáp án:</b> '+answer,styles['small'])
    t=Table([[content]],colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.5,TEAL),
                          ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
                          ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.extend([Spacer(1,4),t])
    md.append('Tự kiểm tra: '+question+'\nĐáp án: '+answer)


def arrow(d,x1,y1,x2,y2,color=TEAL):
    d.add(Line(x1,y1,x2,y2,strokeColor=color,strokeWidth=1.3))
    if x1==x2:
        sign=1 if y2>y1 else -1
        pts=[x2,y2,x2-3,y2-6*sign,x2+3,y2-6*sign]
    else:
        sign=1 if x2>x1 else -1
        pts=[x2,y2,x2-6*sign,y2-3,x2-6*sign,y2+3]
    d.add(Polygon(pts,fillColor=color,strokeColor=color))


def box(d,x,y,w,h,label,fill=PALE):
    d.add(Rect(x,y,w,h,rx=5,ry=5,fillColor=fill,strokeColor=TEAL,strokeWidth=.7))
    lines=label.split('|')
    for i,text in enumerate(lines):
        d.add(String(x+w/2,y+h/2+(len(lines)-1)*6-i*12-3,text,fontName='Text',fontSize=9,textAnchor='middle',fillColor=NAVY))


page(1,'Bạn đang xây dựng cái gì?',
     'Mục tiêu: kể lại được hành trình của một phôi và phân biệt máy ảo, cảm biến, điều khiển và bản sao số.',
     'mujoco/README.md; production_cell.xml; run_cell.py')
p('<b>Lõi Digital Twin từ số 0</b> - tài liệu học 10 trang, gắn với mã và kết quả của dự án ngày 27/10/2026. Đọc theo thứ tự; không cần biết trước Python hay điều khiển tự động.')
p('<b>Baseline</b> là phiên bản cơ sở để kiểm tra từng giả định trước khi thêm chức năng. Trong các bài này, Python/MuJoCo làm phần tính và điều khiển; Unity không tham gia các lượt nghiệm thu. Chương trình Python này chưa nối với PLC thật.','small')
p('Hãy tưởng tượng một kiện hàng chạy trên băng. A1 đẩy nó sang băng thứ hai; PS1/PS2 báo khi nó đi qua. Robot XY đưa đầu hút tới vị trí gắp; A2 hạ/nâng đầu hút; robot mang hàng tới một trong sáu hộp.')
preview=ROOT/'mujoco/preview.png'
if preview.exists():
    from reportlab.lib.utils import ImageReader
    iw,ih=ImageReader(str(preview)).getSize()
    scale=min(300/iw,150/ih)
    story.append(Image(str(preview),width=iw*scale,height=ih*scale,hAlign='CENTER'))
    p('Ảnh mô hình mô phỏng hiện có. Kích thước và thông số vật lý còn là giả định/ước lượng.','small')
table(['Khái niệm','Hiểu bằng ngôn ngữ thường'],[
    ['Plant / đối tượng','Chiếc máy cần điều khiển; ở giai đoạn này là máy ảo MuJoCo.'],
    ['Cơ cấu chấp hành','Bộ phận nhận lệnh và tạo chuyển động: động cơ, xi lanh, hút.'],
    ['Cảm biến','Nguồn thông tin máy có thể đọc, chẳng hạn có/không có phôi.'],
    ['Bộ điều khiển','Chọn lệnh tiếp theo dựa trên điều kiện và thông tin đang có.'],
    ['Bản sao số','Biểu diễn số có cập nhật thông tin để hỗ trợ theo dõi/ước lượng/dự báo. Lõi hiện chưa đủ mọi chức năng này.'],
],[.29,.71])
sub('Vì sao hình 3D chưa đủ?')
p('Hình 3D mô tả hình dạng. Mô phỏng vật lý còn cần khối lượng, lực, ma sát và tiếp xúc. MuJoCo tính chuyển động từng bước; trong mô hình này, băng dùng vận tốc bề mặt và giác hút dùng lực bám tiếp xúc giả định. Chưa có mô hình áp suất/rò khí đã hiệu chuẩn.')
check('Đầu hút chuyển động đẹp có chứng minh đã gắp được phôi không?',
      'Không. Phải có bằng chứng phôi đi theo đầu hút hoặc kiểm tra độc lập; lệnh bật hút chỉ là một lệnh.')


page(2,'Dữ liệu đi qua chương trình ra sao?',
     'Mục tiêu: chỉ ra ai được đọc tín hiệu, ai được đọc đáp án và một vòng lặp Python làm gì.',
     'run_twin.py; sensor_model.py; estimator.py; sequence.py')
d=Drawing(W,136)
for x,w,label in [(0,100,'Máy ảo|MuJoCo'),(127,105,'Cảm biến|SignalFrame'),(259,100,'Ước lượng|vị trí phôi'),(386,112,'Điều khiển|máy trạng thái')]:
    box(d,x,83,w,42,label)
for a,b in [(100,127),(232,259),(359,386)]: arrow(d,a,104,b,104)
d.add(Line(180,125,180,133,strokeColor=TEAL,strokeWidth=1))
d.add(Line(180,133,442,133,strokeColor=TEAL,strokeWidth=1))
arrow(d,442,133,442,125)
box(d,260,12,238,40,'Bộ đánh giá: so ước lượng với đáp án')
arrow(d,50,83,50,32,GRAY); arrow(d,50,32,260,32,GRAY)
arrow(d,308,83,308,52,GRAY)
d.add(String(56,43,'Trạng thái chuẩn chỉ để chấm',fontName='Text',fontSize=8.5,fillColor=GRAY))
story.append(d)
p('Controller nhận cả tín hiệu trực tiếp lẫn ước lượng. MuJoCo biết vị trí thật của mọi vật vì nó đang tính mô phỏng; máy thật không tự cung cấp “tọa độ chính xác của phôi”. Nếu controller đọc thẳng đáp án đó, bài thử dễ thành công nhưng chưa chứng minh cách điều khiển có thể chuyển sang máy thật.')
table(['Tệp trong mujoco/','Bạn đọc nó để hiểu'],[
    ['run_cell.py','Máy ảo và commissioning cũ; commissioning dùng đáp án phôi.'],
    ['signals.py + sensor_model.py','Cấu trúc gói dữ liệu và cách tạo tín hiệu cảm biến.'],
    ['estimator.py','Từ các mốc quang suy ra vị trí và vận tốc.'],
    ['sequence.py','Điều kiện chuyển bước, timeout và HOLD.'],
    ['run_twin.py','Ghép các phần, phát lệnh trở lại máy ảo và ghi log.'],
],[.40,.60])
sub('Đọc Python bằng một ví dụ nhỏ')
code('frame, edges = sensor.sample(state)\ncommand = controller.tick(frame, frame.received_time_s)\n# Sau đó bộ nối áp dụng command vào máy ảo.\n# Chỉ evaluator dùng state để tính sai số.')
p('Dấu <b>=</b> gán kết quả cho biến; dấu chấm gọi một chức năng của đối tượng. <b>sample</b> tạo một mẫu; <b>tick</b> xử lý một lượt điều khiển. Dictionary là bảng tên-giá trị, ví dụ <b>{"ps1": True}</b>. <b>if</b> nghĩa là “nếu điều kiện đúng thì làm việc này”.','small')
p('Vòng lặp hiện đọc cảm biến, ước lượng/chọn lệnh, áp dụng lệnh, ghi log rồi tiến mô phỏng. Luồng lệnh từ controller quay lại plant. Các số sai số trong log không được đưa ngược vào quyết định canh gắp.','small')
check('sensor_model được đọc vị trí khớp để tạo công tắc; controller có được đọc cùng dữ liệu đó không?',
      'Không. Mô hình cảm biến nằm bên trong plant; đầu ra công khai cho controller là tín hiệu nhị phân.')


page(3,'Cảm biến thực sự nói được điều gì?',
     'Mục tiêu: đọc đúng True, False, None và hiểu vì sao hạ 60 mm không phải hết hành trình 75 mm.',
     'sensor_model.py; signals.py; production_cell.xml')
p('Cảm biến quang trong mô hình được tạo từ tia đo khoảng cách, sau đó đổi thành có/không phát hiện. <b>ps1=True</b> không phải tọa độ liên tục; nó chỉ cho biết vùng tia đang có vật gây phát hiện. Mô hình hiện là cảm biến lý tưởng, chưa mô phỏng mọi nguyên nhân báo sai.')
table(['Tín hiệu','Ý nghĩa / trạng thái hiện tại'],[
    ['ps1, ps2','Hai vị trí phát hiện phôi trên băng tải dài.'],
    ['a1_retracted / extended','A1 gần đầu thu 0 mm / đầu ra 110 mm.'],
    ['a2_retracted / extended','A2 gần đầu trên 0 mm / đầu dưới 75 mm.'],
    ['home_x, home_y1, home_y2','Chưa xác nhận nguồn phản hồi: None / unavailable.'],
    ['vacuum_ok','Chưa có nguồn xác nhận chân không: None / unavailable.'],
    ['belt_speed_*','Chưa có encoder tốc độ được xác nhận; không dùng lệnh tốc độ như phép đo.'],
],[.42,.58])
sub('Mô phỏng công tắc cuối hành trình')
p('Gọi q là hành trình. Công tắc tác động nếu khoảng cách tới đầu hành trình không quá 2 mm. Dấu |...| nghĩa là lấy độ lớn, bỏ dấu âm; dung sai 2 mm là tham số thử chưa hiệu chuẩn.')
code('A1 ra hết:  |q_A1 - 110 mm| <= 2 mm\nA2 xuống hết: |q_A2 - 75 mm| <= 2 mm\nNếu q_A2 = 60 mm: |60 - 75| = 15 mm > 2 mm')
p('Vì thế tại 60 mm, tín hiệu dưới A2 vẫn False. Ta giữ nguyên điều này. Dời ngưỡng xuống 60 chỉ để chương trình chạy tiếp sẽ che mất giới hạn thật của phép đo. A1 trong baseline mới chờ công tắc ra hết, thay vì dùng tọa độ khớp để chuyển bước sớm.')
p('A2 trong MuJoCo nhận lệnh vị trí. Điều đó không chứng minh van khí nén 5/2 ngoài thực tế có thể giữ xi lanh tại 60 mm; đây là một giới hạn khi chuyển từ mô phỏng sang máy thật.','small')
table(['Giá trị / chất lượng','Cách hiểu'],[
    ['False / good','Có mẫu hợp lệ, mẫu đang báo chưa tác động.'],
    ['None / unavailable','Chưa có nguồn đo; không thể kết luận là chưa tác động.'],
    ['True hoặc False / stale','Giữ giá trị cũ nhưng đã quá tuổi cho phép.'],
],[.40,.60])
p('<b>good không có nghĩa cảm biến chắc chắn khỏe.</b> Cảm biến kẹt mức vẫn có thể gửi mẫu đúng cấu trúc và mới, nhưng giá trị không phản ánh vật thể. Chất lượng truyền dữ liệu khác với chẩn đoán phần cứng.','small')
check('Bật hút True có được gán vacuum_ok=True không?',
      'Không. Một bên là ý định điều khiển, bên kia phải là thông tin xác nhận độc lập.')


page(4,'Thời gian, lấy mẫu và cạnh tín hiệu',
     'Mục tiêu: hiểu 2 ms, 20 ms, timestamp, tuổi dữ liệu và vì sao một True có thể chỉ là thông tin cũ.',
     'signals.py; run_cell.py; sensor_model.py; sequence.py')
table(['Đại lượng','Giá trị trong baseline','Nghĩa của nó'],[
    ['Bước vật lý','2 ms = 0,002 s','Khoảng thời gian mô phỏng mỗi bước giải.'],
    ['Lấy mẫu / tick','20 ms = 10 bước vật lý','50 lượt mỗi giây mô phỏng.'],
    ['Nguồn và nhận','source_time_s / received_time_s','Lúc lấy mẫu / lúc nhận, hiện dùng chung đồng hồ mô phỏng.'],
    ['sequence','Số thứ tự tăng dần','Ghép log và nhận biết trùng hoặc đảo thứ tự.'],
],[.27,.29,.44])
p('<b>20 ms không phải độ trễ đồng bộ với máy thật.</b> Không có kết nối máy thật để đo đại lượng đó. Thời gian mô phỏng là thời gian của thế giới ảo; thời gian chạy trên laptop có thể nhanh hoặc chậm hơn. Hiện thời gian nhận bằng thời gian lấy mẫu, chưa có mô hình truyền mạng.')
sub('Cạnh lên là một sự kiện, không phải một mức kéo dài')
code('Mẫu:      0    1    2    3    4\nPS1:   False False True True False\nCạnh:     -    -   lên   -   xuống')
p('Nếu đếm mọi mẫu True, một phôi có thể bị đếm nhiều lần. Chỉ chuyển False → True tạo cạnh lên để đánh dấu mốc đi qua. Mẫu đầu thiết lập trạng thái; True ngay từ đầu không chứng minh vừa có một phôi mới vượt tia.')
sub('Gói dữ liệu giống một phong bì có ngày gửi')
code('{"sequence": 259,\n "source_time_s": 5.18, "received_time_s": 5.18,\n "values": {"ps1": true}, "quality": {"ps1": "good"}}')
p('Đây là bản rút gọn để đọc: gói thật có đủ các tín hiệu và trường nguồn/miền đồng hồ. Trong JSON dùng <b>true/null</b>; trong Python dùng <b>True/None</b>. Dữ liệu có thể gửi được không có nghĩa dữ liệu còn mới.','small')
code('Tuổi dữ liệu = thời gian hiện tại - thời gian lấy mẫu\nVí dụ minh họa: 5,40 - 5,18 = 0,22 s = 220 ms')
p('Ngưỡng hiện tại là 100 ms: ví dụ trên thành stale dù gói vừa đến. Khoảng lấy mẫu lớn hơn 61 ms hoặc thứ tự thời gian/số thứ tự không tăng cũng đưa controller vào HOLD. Các ngưỡng này là cấu hình thử, không phải tiêu chuẩn công nghiệp chung.')
check('Gói cũ vừa nhận lúc 5,40 s có tự trở nên mới không?',
      'Không. Tuổi tính từ lúc lấy mẫu. Khi sang nhiều đồng hồ thật phải xử lý thêm sai lệch đồng hồ.')


page(5,'Từ hai lần thấy phôi đến vị trí ước lượng',
     'Mục tiêu: tự tính được vận tốc, vị trí tâm phôi và hiểu dấu “ước lượng” trong y_hat.',
     'estimator.py; dt_acceptance_20261027_v2/bin_1/signals.jsonl')
p('Không thấy liên tục vẫn có thể ước lượng: nếu biết vừa đi qua một mốc và chuyển động khoảng bao nhanh, ta suy ra vị trí giữa hai lần quan sát. Giống dự đoán vị trí xe từ mốc cây số và tốc độ; đó là <b>ước lượng</b>, chưa phải quan sát trực tiếp.')
d=Drawing(W,93)
d.add(Rect(10,28,W-20,24,fillColor=PALE,strokeColor=TEAL))
for x,label in [(105,'PS1: -65 mm'),(374,'PS2: 170 mm')]:
    d.add(Line(x,18,x,67,strokeColor=TEAL,strokeWidth=1.4))
    d.add(String(x,74,label,fontName='Text',fontSize=10,textAnchor='middle',fillColor=NAVY))
arrow(d,115,40,360,40)
d.add(String(W/2,8,'Khoảng cách 235 mm; phôi đi theo +Y (minh họa, không theo tỷ lệ)',fontName='Text',fontSize=8.5,textAnchor='middle',fillColor=GRAY))
story.append(d)
sub('Bước 1. Tính vận tốc từ hai cạnh cùng một phôi')
p('Lượt hộp 1 ghi PS1 lên ở 5,18 s và PS2 lên ở 6,66 s. Cùng một mặt trước vượt hai tia, nên khoảng cách giữa các mốc bằng 0,235 m.')
code('Delta_t = 6,66 - 5,18 = 1,48 s\nv_hat = 0,235 / 1,48 = 0,15878 m/s = 158,78 mm/s')
p('Hậu tố _hat trong tên v_hat/y_hat chỉ giá trị ước lượng. Vận tốc đặt là 0,16 m/s; vận tốc trung bình suy ra khoảng 0,1588 m/s. Chênh lệch có thể do lấy mẫu và động lực học mô hình, không tự chứng minh động cơ thật bị lỗi.','small')
sub('Bước 2. Đổi mốc mặt trước thành vị trí tâm')
p('Phôi dài 22 mm nên tâm nằm sau mặt trước 11 mm. Lần đọc cảm biến có thể trễ trong một khoảng lấy mẫu 20 ms; mã bù xấp xỉ bằng nửa khoảng đó. Đây là phép gần đúng, không biết chính xác thời điểm vượt tia.')
code('y_hat = 0,170 - 0,011 + 0,15878 * 0,020 / 2\n      = 0,160588 m, khoảng 160,59 mm tại mẫu PS2')
sub('Bước 3. Dự đoán giữa các mốc')
code('y_hat_moi = y_hat_cu + v_hat * Delta_t\nĐi thêm 0,5 s: Delta_y = 0,15878 * 0,5 = 79,39 mm')
p('Trước khi có PS2, mã dùng vận tốc đặt làm tiên nghiệm. Nếu PS2 đến mà chưa có PS1 hợp lệ, không tự bịa một tọa độ. Hai cạnh phải ghép đúng một phôi và lệnh tốc độ không đổi giữa chúng; thay tốc độ giữa hai mốc hiện dẫn tới từ chối mô hình vận tốc này.','small')
check('Bỏ qua nửa chiều dài phôi gây sai theo hướng nào?',
      'Nhắm quá xa về phía trước khoảng 11 mm, trước khi xét các sai số khác.')


page(6,'Biết mình có thể sai; đổi tọa độ thành lệnh',
     'Mục tiêu: hiểu khoảng sai số, quãng trôi sau dừng và sự khác nhau giữa tọa độ thế giới với hành trình khớp.',
     'estimator.py; sequence.py; production_cell.xml')
p('Một con số 160,59 mm dễ tạo cảm giác chính xác giả. Bộ ước lượng còn giữ <b>uncertainty_m</b>: khoảng sai số kỹ thuật để quyết định có nên dùng dự báo. Đây chưa phải khoảng tin cậy 95% và chưa được hiệu chuẩn bằng máy thật.')
table(['Thao tác trong mã','Ví dụ tính tay tại PS2'],[
    ['Khởi tạo khoảng sai số','2 mm + 158,78 mm/s × 0,020 s / 2 = 3,59 mm.'],
    ['Ngoại suy thêm 0,5 s khi băng chạy','Tăng 20 mm/s × 0,5 s = 10 mm; tổng khoảng 13,59 mm nếu chưa được hiệu chỉnh.'],
    ['Dừng băng','Thêm một lần quãng trôi thử 2 mm vào vị trí và khoảng sai số.'],
    ['Điều kiện canh gắp tại PS2','Khoảng sai số + phần trôi phải không vượt 10 mm.'],
],[.42,.58])
p('Khi có PS2, một mốc mới hiệu chỉnh lại vị trí và khoảng sai số. Nếu chỉ giữ ngoại suy lâu, độ không chắc phải tăng. Quãng trôi 2 mm và mức tăng 20 mm/s là tham số thử; số liệu nhỏ trong một lượt không biến chúng thành một bảo đảm an toàn.')
sub('Tại sao trong mã có +0,180 và -0,120?')
p('Trong mô hình, đầu robot ở X = -0,180 m và Y = 0,120 m khi khớp XY bằng 0. Vị trí thế giới và hành trình khớp khác nhau như vị trí một căn nhà và quãng đường đi từ nhà đó. q là hành trình khớp, đơn vị mét.')
code('x_world = -0,180 + q_X    => q_X = x_dich + 0,180\ny_world =  0,120 + q_Y    => q_Y = y_dich - 0,120\ny_dich = 0,160588 + 0,002 = 0,162588 m\nq_Y = 0,162588 - 0,120 = 0,042588 m')
p('Mã hiện giả định phôi nằm trên làn X = -0,180 m, nên q_X gắp bằng 0; không ước lượng X từ PS1/PS2. Trục Z hướng lên nhưng hành trình A2 dương đi xuống theo khớp đã định nghĩa.','small')
sub('Vì sao thời gian XY dùng max, không cộng?')
code('T_du_kien = max(|Delta_X|, |Delta_Y|) / 0,12 + 0,30\nVí dụ Delta_X=0,24 m, Delta_Y=0,12 m: T=2,30 s')
p('Hai trục được ra lệnh đồng thời, nên trục lâu hơn quyết định thời gian dự kiến. Đây là thời gian từ lệnh, chưa xác nhận robot thật đã tới. Mất bước hoặc bị kẹt có thể phá vỡ giả định; vì vậy chế độ mặc định chặn trước thao tác này.','small')
p('<b>Điểm đặt</b> là vị trí mong muốn. <b>Ramp</b> nghĩa là tăng dần điểm đặt theo tốc độ giới hạn, thay vì nhảy ngay tới đích. Khi HOLD, bộ nối giữ điểm đặt ramp đã phát; đó chưa phải phép đo vị trí đứng yên thực tế.','small')
check('Một khoảng sai số 3,59 mm có nghĩa 95% lần gắp sẽ đúng không?',
      'Không. Muốn kết luận xác suất cần mô hình sai số, dữ liệu và kiểm chứng tương ứng.')


page(7,'Máy trạng thái: làm đúng việc, đúng lúc',
     'Mục tiêu: đọc một trình tự như danh sách công việc có điều kiện, thay vì chuỗi lệnh chờ mù.',
     'sequence.py; dt_acceptance_20261027_v2/bin_1/summary.json')
p('<b>Trạng thái</b> trả lời “đang ở công đoạn nào?”. Mỗi tick kiểm tra dữ liệu, thực hiện lệnh phù hợp rồi xét điều kiện đi tiếp. <b>Timeout</b> là hạn chờ phản hồi. Một bước chưa xong không được ngầm coi là đã xong chỉ vì bước sau cần chạy.')
table(['Trạng thái','Lệnh/chức năng','Điều kiện chuyển'],[
    ['INIT','Kiểm tra đầu vào','A1 thu, A2 trên, hai tia quang không che.'],
    ['FEED','Băng đầu chạy','Khoảng 2,36 s, giả định một phôi tại reset.'],
    ['PUSH','A1 ra 110 mm','a1_extended=True; chờ tối đa 2 s.'],
    ['RETRACT','A1 thu','a1_retracted=True; chờ tối đa 2 s.'],
    ['TRACK','Băng dài chạy','PS2 + đủ hai mốc + sai số cho phép.'],
    ['ALIGN','XY tới vị trí ước lượng','Thời gian XY, chỉ nếu đã chọn giả định vòng hở.'],
    ['LOWER','A2 hạ 60 mm','Chờ dự kiến 0,75 s, không giả tín hiệu dưới.'],
    ['GRIP / LIFT','Bật hút rồi nâng','Chờ hút 0,25 s; nâng chờ công tắc A2 trên.'],
    ['MOVE / LOWER_BIN','Tới hộp, hạ A2','XY theo thời gian, hạ theo thời gian.'],
    ['RELEASE / RAISE','Nhả rồi nâng','Nhả 0,40 s; nâng chờ công tắc trên.'],
    ['RETURN / DONE','Trở về, kết thúc','Thời gian về; evaluator chấm đặt phôi riêng.'],
    ['HOLD','Dừng băng, giữ lệnh cần giữ','Không tự chạy lại khi xuất hiện tín hiệu mới.'],
],[.23,.29,.48])
sub('Ví dụ chuyển PUSH sang RETRACT')
code('if a1_extended:\n    chuyen_sang_RETRACT()\nelif thoi_gian_cho >= 2.0:\n    HOLD("timeout:PUSH:a1_extended")')
p('Đây là mã minh họa, không dán để chạy. Tại mỗi lượt, controller vẫn có cơ hội kiểm tra mẫu cũ hoặc lỗi phản hồi. Trong baseline hộp 1, PUSH bắt đầu 2,36 s; RETRACT bắt đầu 3,18 s; TRACK bắt đầu 4,00 s; ALIGN bắt đầu 6,66 s.','small')
p('<b>Vòng kín và vòng hở cùng tồn tại.</b> PUSH/RETRACT dùng phản hồi công tắc; XY và A2 trung gian trong chế độ thử vẫn dựa trên thời gian. Một chu trình có vài cảm biến chưa đồng nghĩa mọi chuyển động đều được xác nhận.','small')
check('Công tắc A1 không báo sau 2 s thì có được chạy TRACK để “thử xem” không?',
      'Không. Giữ HOLD và lý do. Phải điều tra trạng thái trước khi phục hồi.')


page(8,'Khi thiếu thông tin: HOLD như thế nào?',
     'Mục tiêu: phân biệt phát hiện dấu hiệu bất thường, xác định nguyên nhân và hành động giữ.',
     'sequence.py; run_twin.py; check_twin.py; results.json (bộ v2)')
p('Lỗi thử <b>stuck_low</b> giữ một tín hiệu luôn False, nhưng gói vẫn mới và quality vẫn good. Controller chỉ thấy dữ liệu đã bị thay; không được đọc nhãn lỗi hoặc đáp án trước khi quyết định. Đây là thử nghiệm có kiểm soát, không phải bằng chứng phát hiện được mọi kiểu hỏng.')
table(['Lượt thử','Phản ứng quan sát được'],[
    ['Chế độ mặc định','HOLD ở 6,66 s: chưa xác nhận XY/A2 trung gian/chân không. Đây là giới hạn quan sát, không phải cảm biến được chứng minh hỏng.'],
    ['PS1 luôn False','HOLD ở 6,66 s: PS2 xuất hiện nhưng không có PS1, không ghép được hai mốc.'],
    ['PS2 luôn False','HOLD ở 6,76 s: quá hạn chờ PS2.'],
    ['A1 ra hết luôn False','HOLD ở 4,38 s: quá hạn PUSH 2 s.'],
],[.33,.67])
sub('Một timeout 6 giây có thể quá chậm')
p('Nếu phôi vẫn chạy, chờ thêm có thể làm phôi rơi khỏi băng. Mã mới giới hạn thời gian theo quãng đường cho phép từ vùng chuyển phôi. Hệ số 0,44 m là tham số của cấu hình hiện tại, không phải hằng số phổ quát.')
code('T_TRACK = min(6 s, 0,44 m / v_dat)\nVới v_dat=0,16 m/s: T_TRACK=2,75 s\nTRACK từ 4,00 s: hạn 6,75 s, tick ghi HOLD ở 6,76 s')
sub('HOLD không chỉ là đổi một chữ trong log')
p('Bộ nối dừng băng, giữ các điểm đặt ramp đã phát và giữ lệnh hút đang có; không tự tắt hút nếu có thể đang mang phôi. HOLD được chốt: dữ liệu về sau không tự cho chạy tiếp. Muốn phục hồi phải xác định lại điều kiện và reset đúng cách.')
p('Evaluator chạy thêm ít nhất 0,30 s sau HOLD để kiểm tra phôi còn được đỡ trên băng. Cả bốn trường hợp HOLD trong bộ v2 đạt kiểm tra đó. Đây chưa phải kiểm chứng mọi va chạm, mọi tình huống giữ tải hoặc chức năng an toàn của máy thật.')
sub('Phát hiện dấu hiệu khác với chẩn đoán nguyên nhân')
p('Thiếu PS2 có thể do cảm biến hỏng, phôi bị kẹt hoặc vận chuyển chậm. Timeout cho biết giả định vận hành không được xác nhận, chưa đủ kết luận nguyên nhân. Tự tái cấu hình còn cần đánh giá phương án thay thế; baseline này mới dừng có lý do.','small')
check('12 lượt đạt có chứng minh phát hiện lỗi chính xác 100% không?',
      'Không. Chỉ các trường hợp đã dựng đạt tiêu chí. Chưa đo tỷ lệ bỏ sót/báo sai trên nhiều lịch lỗi.')


page(9,'Đọc kết quả mà không hiểu nhầm con số',
     'Mục tiêu: đọc log, hiểu RMSE/p95 và phân biệt thành công trong mô phỏng với chất lượng hệ thật.',
     'run_twin.py; dt_acceptance_20261027_v2/results.json và bin_1/ground_truth.jsonl')
p('Mỗi lượt ghi <b>signals.jsonl</b> (cảm biến), <b>controller.jsonl</b> (quyết định/ước lượng), <b>ground_truth.jsonl</b> (đáp án chỉ để chấm) và <b>summary.json</b> (tổng kết). JSONL là mỗi dòng một gói JSON. Ghép ba log theo sequence, tránh so nhầm hai thời điểm.')
table(['Băng dài (m/s)','Chu trình hộp 1 (s)','RMSE Y (mm)','Max |sai số| (mm)'],[
    [f'{by_case[k]["commanded_long_belt_speed_m_s"]:.2f}',
     f'{by_case[k]["simulation_time_s"]:.2f}',f'{1000*by_case[k]["y_error_rmse_m"]:.3f}',
     f'{1000*by_case[k]["y_error_max_abs_m"]:.3f}'] for k in ('speed_010','bin_1','speed_024')
],[.24,.28,.22,.26])
errors=[(r['time_s'],1000*r['y_estimation_error_m']) for r in truth_rows if r['y_estimation_error_m'] is not None]
chart=Drawing(W,145)
plot=LinePlot(); plot.x=43; plot.y=32; plot.width=W-61; plot.height=88
plot.data=[errors]; plot.lines[0].strokeColor=TEAL; plot.lines[0].strokeWidth=1.25
plot.xValueAxis.valueMin=5.1; plot.xValueAxis.valueMax=7.4
plot.xValueAxis.valueSteps=[5.2,5.6,6.0,6.4,6.8,7.2]
plot.yValueAxis.valueMin=-2; plot.yValueAxis.valueMax=2; plot.yValueAxis.valueSteps=[-2,-1,0,1,2]
for axis in (plot.xValueAxis,plot.yValueAxis):
    axis.labels.fontName='Text'; axis.labels.fontSize=8; axis.strokeColor=GRAY
chart.add(plot)
chart.add(String(43,133,'Sai số Y (mm) - hộp 1, tốc độ đặt 0,16 m/s',fontName='Text',fontSize=9,fillColor=NAVY))
chart.add(String(W/2,8,'Thời gian mô phỏng (s)',fontName='Text',fontSize=8.5,textAnchor='middle',fillColor=GRAY))
story.append(chart)
p('Đồ thị là sai số, không phải đường đi của phôi. Quanh 6,66 s, chương trình hiệu chỉnh tại PS2 rồi bù quãng trôi khi dừng, nên sai số có thể đổi đột ngột.','small')
plot_dir=ROOT/'output/figures'; plot_dir.mkdir(parents=True,exist_ok=True)
renderSVG.drawToFile(chart,str(plot_dir/'dt_baseline_y_error.svg'))
sub('Tính sai số bằng một ví dụ nhỏ')
code('e = vi_tri_uoc_luong - vi_tri_chuan\nRMSE = can_bac_hai(trung_binh(e * e))\nVi du e=[1, -1, 2] mm: RMSE=sqrt(6/3)=1,414 mm')
p('<b>RMSE</b> nhỏ khi sai số thường nhỏ; bình phương khiến sai số lớn được tính nặng hơn. <b>Max</b> là độ lớn sai số lớn nhất đã ghi. <b>p95</b> là ngưỡng mà ít nhất khoảng 95% mẫu sai số tuyệt đối trong tập đo không vượt qua; không phải xác suất đúng của mọi lần chạy tương lai.','small')
p(f'Lượt hộp 1 có {nominal["y_error_samples"]} mẫu sai số trong đoạn sau PS1, khi TRACK/ALIGN; RMSE {1000*nominal["y_error_rmse_m"]:.3f} mm, p95 {1000*nominal["y_error_p95_abs_m"]:.3f} mm. Không đo toàn bộ XYZ hay giai đoạn chưa thấy phôi. Đây là so với đáp án của mô phỏng, chưa so với máy thật.','small')
p('<b>14 kiểm tra logic</b> kiểm tra quy tắc; <b>12 lượt nghiệm thu</b> chạy vật lý và chấm đầu ra. Tám lượt đặt phôi và bốn lượt HOLD đều đạt. Các lượt xác định này không đủ để tuyên bố độ tin cậy thống kê. DONE và đặt phôi đúng cũng phải được đọc riêng.','small')
check('Chu trình mới dài hơn commissioning cũ có phải thuật toán thất bại không?',
      'Chưa thể kết luận: tiêu chí chờ và giả định đã khác. Giai đoạn này chứng minh baseline, chưa chứng minh tăng năng suất.')


page(10,'Tự chạy, tự giải thích, rồi đi tiếp',
     'Mục tiêu: chạy ba thí nghiệm, đọc đúng kết quả và biết chính xác phần nào còn chưa làm.',
     'run_twin.py --help; check_twin.py; test_signals.py; test_sequence.py')
p('<b>1. Mở PowerShell</b> từ Start trên Windows. WSL là môi trường Linux chạy trong Windows; MuJoCo đã cài ở đó trên máy này. Dán từng dòng sau; các biến chỉ là tên ngắn cho đường dẫn, không phải lệnh điều khiển máy thật.')
code('cd C:\\Users\\Admin\\Documents\\ChatGPT\\plc\n$py = "/home/admin/dt-cpps-venv/bin/python"\n$root = "/mnt/c/Users/Admin/Documents/ChatGPT/plc"\n$app = "$root/mujoco/run_twin.py"')
p('<b>2. Chạy chế độ mặc định.</b> Mong đợi HOLD với lý do thiếu xác nhận XY/A2/chân không, sau khi đã theo dõi phôi. Đây là kết quả có chủ đích.','small')
code('$out = "$root/output/hoc_strict_01"\nwsl -d Ubuntu-24.04 -- $py $app --output $out')
p('<b>3. Chạy trọn mô phỏng có giả định vòng hở.</b> Cửa sổ tự chuyển động; không cần bấm Run. Đóng cửa sổ sau khi xong để nhận tổng kết. Mong đợi DONE và placement_pass_evaluator_only=true.','small')
code('$out = "$root/output/hoc_nominal_01"\nwsl -d Ubuntu-24.04 -- $py $app --output $out --assume-open-loop --view')
p('<b>4. Giả lập PS2 kẹt thấp.</b> Mong đợi HOLD với timeout:TRACK:ps2; xem hold_time_s và kiểm tra phôi còn được đỡ sau dừng.','small')
code('$out = "$root/output/hoc_loi_01"\nwsl -d Ubuntu-24.04 -- $py $app --output $out --assume-open-loop --fault ps2_stuck_low')
p('Mỗi lần chạy chọn thư mục mới, đổi 01 thành 02 nếu đã tồn tại. Lỗi đồ họa thì thử bỏ --view; lỗi đường dẫn thì kiểm tra tên file. HOLD không phải lỗi cài đặt. Không sửa ngưỡng để ép một bài thử báo thành công.','small')
sub('Bài tập trước khi chuyển sang chức năng tiếp theo')
p('Mở summary.json, tìm trạng thái/lý do và số mẫu. Tìm PS1/PS2 đổi mức trong signals.jsonl; tự tính 0,235 chia chênh thời gian. Đối chiếu với estimated_transit_speed_m_s. Chỉ mở ground_truth.jsonl khi cần chấm sai số, không dùng nó làm đầu vào điều khiển.','small')
sub('Bản đồ học tiếp')
p('Đọc theo thứ tự: signals.py → sensor_model.py → estimator.py → sequence.py → run_twin.py. Kiểm tra bằng test_signals.py và test_sequence.py; chạy check_twin.py để thử đủ 12 trường hợp. Hướng dẫn chi tiết: docs/dt_estimator_sequence.md.','small')
p('Phần đã có: mô hình vật lý, tín hiệu, log/phát lại, ước lượng một phôi và máy trạng thái baseline. Phần tiếp theo: hiệu chuẩn và phản hồi còn thiếu; trễ/mất gói; chẩn đoán bất thường; mô phỏng dự báo độc lập và chọn chính sách tái cấu hình. <b>Chưa huấn luyện ML/RL; chưa nối mạng với PLC; chưa chứng minh tăng năng suất.</b>','small')
check('Bạn đã nắm lõi khi trả lời được điều gì?',
      'Máy biết gì từ cảm biến, đang giả định gì, có thể sai bao nhiêu, chuyển bước vì điều kiện nào và vì sao phải HOLD khi thiếu bằng chứng.')


def decorate(c,doc):
    c.saveState()
    c.setStrokeColor(TEAL); c.setLineWidth(1)
    c.line(48,A4[1]-34,A4[0]-48,A4[1]-34)
    c.setFillColor(GRAY); c.setFont('Text',8)
    c.drawString(48,A4[1]-26,'LÕI DIGITAL TWIN | HỌC TỪ MÔ HÌNH ĐANG CHẠY')
    c.drawRightString(A4[0]-48,A4[1]-26,'27/10/2026')
    c.setFont('Text',7.1)
    if doc.page <= len(sources):
        c.drawString(48,35,'Đối chiếu: '+sources[doc.page-1])
    c.setFont('Bold',8.2)
    c.drawRightString(A4[0]-48,21,f'{doc.page:02d} / 10')
    c.setFont('Text',7.6); c.drawString(48,21,'Số đo trong tài liệu là mô phỏng, trừ khi được ghi rõ khác.')
    c.restoreState()


OUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=48,rightMargin=48,
                      topMargin=52,bottomMargin=52,title='Lõi Digital Twin từ số 0 - 10 bài cho người mới',
                      author='',subject='Hướng dẫn baseline MuJoCo PS1/PS2, estimator và state machine')
doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
with pdfplumber.open(OUT) as pdf:
    counts=[len((pg.extract_text() or '').split()) for pg in pdf.pages]
    print('Pages:',len(pdf.pages),'word counts:',counts)
    assert len(pdf.pages)==10, 'Adjust content/layout before delivery'
    for index,pg in enumerate(pdf.pages,1):
        text=pg.extract_text() or ''
        assert f'{index:02d} / 10' in text
        assert '\ufffd' not in text
(ROOT/'docs/hieu_loi_digital_twin_10_trang.md').write_text('\n\n'.join(md),encoding='utf-8')
paths=['mujoco/signals.py','mujoco/sensor_model.py','mujoco/estimator.py','mujoco/sequence.py',
       'mujoco/run_twin.py','mujoco/check_twin.py','output/dt_acceptance_20261027_v2/results.json']
manifest={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
(ROOT/'output/pdf/hieu_loi_digital_twin_sources.json').write_text(
    json.dumps({'date':'2026-10-27','source_sha256':manifest,'pages':10,'page_word_counts':counts,
                'results_scope':'deterministic simulation, not hardware validation'},indent=2),encoding='utf-8')
print(OUT)
