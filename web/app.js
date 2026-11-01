'use strict';
const $ = id => document.getElementById(id);
const fmt = (v, n=2) => Number.isFinite(v) ? v.toLocaleString('vi-VN',{minimumFractionDigits:n,maximumFractionDigits:n}) : '—';
const phaseText = {
 FEED:['Đưa phôi vào vùng chuyển tiếp','Băng ngang đưa phôi đến trước xi lanh A1. Hiện thời điểm vào được xác định theo mô hình và thời gian, chưa có đo thực.'],
 PUSH:['A1 chuyển phôi sang băng dọc','Xi lanh A1 đẩy phôi qua vùng nối. Bộ điều khiển chờ công tắc hành trình mở hết.'],
 RETRACT:['Thu xi lanh A1','A1 trở về để nhường đường cho băng tải dọc.'],
 TRACK:['Theo dõi phôi qua PS1 → PS2','DT tích phân vị trí từ vận tốc và neo lại khi có cạnh cảm biến quang. Chỉ khi đã quan sát phôi, supervisor mới xét dự báo dừng.'],
 ALIGN:['Canh robot trên phôi','Băng tải đã nhận lệnh dừng. Robot dịch XY tới vị trí ước lượng; chuyển động này dùng giả định hở vòng nếu đã bật cho phép.'],
 LOWER:['Hạ đầu gắp A2','A2 xuống vị trí gắp trung gian theo mô hình thời gian; chưa có tín hiệu đo vị trí trung gian thật.'],
 GRIP:['Bật lệnh hút','Mô phỏng áp dụng lực bám. Lệnh hút ON không có nghĩa đã đo được Vacuum_OK; lượt này dùng giả định hở vòng.'],
 LIFT:['Nâng phôi','A2 nâng đầu gắp trước khi robot chuyển sang hộp.'],
 MOVE:['Chuyển tới hộp đích','Robot XY đưa đầu gắp đến tọa độ hộp trong cấu hình.'],
 LOWER_BIN:['Hạ phôi vào hộp','Robot hạ đầu gắp đến cao độ thả.'],
 RELEASE:['Thả phôi','Tắt lệnh hút. Bộ đánh giá sẽ dùng vị trí phôi mô phỏng để kiểm tra kết quả.'],
 RAISE:['Nâng đầu gắp khỏi hộp','A2 thu về sau khi thả phôi.'],
 RETURN:['Trở về vị trí chờ','Robot quay về vị trí ban đầu để kết thúc chu kỳ một phôi.'],
 DONE:['Chu kỳ hoàn tất','Trình tự đã kết thúc. Xem kết quả đánh giá đặt phôi phía dưới; đây là kết quả mô phỏng, chưa phải xác nhận trên máy thật.'],
 HOLD:['Dừng có lý do','Máy giữ trạng thái dừng theo điều kiện giám sát. HOLD được giữ chốt; chưa có phục hồi tự động.']
};
const reasonText = {
 predictive_continue:'Mọi tổ hợp CONTINUE được xét đều còn biên dừng không âm trong mô hình 1D.',
 predictive_stop_margin:'Nếu đi thêm một chu kỳ 20 ms, ít nhất một tổ hợp vượt giới hạn. Supervisor chọn HOLD ngay.',
 predictive_no_admissible_continue:'Ngay cả yêu cầu HOLD cũng có tổ hợp vượt giới hạn mô hình. Dừng đã muộn trong các giả thiết này; không phải bảo đảm dừng an toàn.',
 prediction_deadline_exceeded:'Bộ dự báo không hoàn tất trong ngân sách. Không dùng phần kịch bản đã tính dở; chuyển HOLD.',
 telemetry_timeout:'Không nhận được mẫu trong thời gian cho phép. Watchdog chuyển HOLD; chưa có dữ liệu để dự báo.',
 unconfirmed_xy_a2_midstroke_and_vacuum:'Chưa có phản hồi xác nhận XY, vị trí A2 trung gian và hút. Chế độ nghiêm ngặt dừng trước thao tác gắp.'
};
const explanation = reason => reasonText[reason] || (reason?.startsWith('timeout:TRACK') ? 'Chờ PS2 quá thời gian cho phép. Trình tự điều khiển nền chuyển HOLD.' : reason || 'Chưa có lý do bổ sung.');
let run=null, index=0, playing=false, lastWall=0, playTime=0, lastIndex=-1, loadingToken=0;
const cache=new Map();
let latestLab=null;
function stop(){playing=false;$('play').textContent='Phát chu kỳ';}
function nearestBefore(rows,time,key='time_s'){
 let lo=0, hi=rows.length-1, found=null;
 while(lo<=hi){const mid=(lo+hi)>>1;if(rows[mid][key]<=time+1e-8){found=rows[mid];lo=mid+1;}else hi=mid-1;}
 return found;
}
function current(){return run?.frames[index];}
function badge(id,text){$(id).textContent=text;$(id).className='badge '+(text==='HOLD'?'hold':text==='DONE'||text==='CONTINUE'?'done':'');}
function metric(label,value){const div=document.createElement('div');const span=document.createElement('span');span.textContent=label;const strong=document.createElement('strong');strong.textContent=value;div.append(span,strong);return div;}
async function loadCase(id){
 const token=++loadingToken;stop();$('error').hidden=true;$('scenario').disabled=true;$('play').disabled=true;$('step').disabled=true;$('timeline').disabled=true;
 try {
  if(!cache.has(id)){const response=await fetch(`data/${encodeURIComponent(id)}.json`);if(!response.ok)throw Error('Không đọc được dữ liệu kịch bản.');cache.set(id,await response.json());}
  if(token!==loadingToken)return;
  run=cache.get(id);index=0;playTime=0;lastIndex=-1;$('scenario').value=id;
  $('timeline').max=run.frames.length-1;$('timeline').value=0;
  ['play','step','timeline','download'].forEach(k=>$(k).disabled=false);
  const c=run.config,s=run.summary;
  $('case-description').textContent=`${run.label}. Tốc độ lệnh ${fmt(s.commanded_long_belt_speed_m_s)} m/s; trễ mạng ${fmt(c.network.delay_s*1000,0)} ms; mất gói cấu hình ${fmt(c.network.drop_probability*100,0)}%. ${s.assume_open_loop?'Cho phép giả định XY/A2/hút hở vòng.':'Giữ chế độ xác nhận nghiêm ngặt.'}`;
  $('phase-markers').replaceChildren();
  run.summary.transitions.forEach(t=>{const b=document.createElement('button');b.textContent=t.phase||t.to||t.state; b.dataset.phase=b.textContent;b.title=`Đến ${fmt(t.time_s)} s`;b.onclick=()=>seekTime(t.time_s);$('phase-markers').append(b);});
  $('run-summary').replaceChildren(metric('Kết quả cuối lượt',s.controller_state),metric('Thời gian mô phỏng',fmt(s.simulation_time_s)+' s'),metric('Lần gọi dự báo',String(s.prediction.calls)),metric('p95 tính dự báo · log',fmt(s.prediction.compute_p95_ms)+' ms'));
  $('evaluation').textContent=s.controller_state==='DONE'?`Đánh giá cuối lượt: ${s.placement_pass_evaluator_only?'đặt phôi trong hộp đạt':'đặt phôi trong hộp chưa đạt'}. RMSE Y trong TRACK/ALIGN: ${fmt(s.y_error_rmse_m*1000,2)} mm; không phải độ chính xác toàn bộ robot.`:`Đánh giá cuối lượt: HOLD tại ${fmt(s.hold_time_s)} s; ${s.hold_product_supported_evaluator_only?'phôi còn được đỡ theo tiêu chí mô phỏng':'chưa xác nhận phôi được đỡ'}. ${explanation(s.hold_reason)}`;
  render();
 } catch(error){if(token===loadingToken){$('error').hidden=false;$('error').textContent=error.message;}}
 finally {if(token===loadingToken)$('scenario').disabled=false;}
}
function seekTime(t){stop();index=Math.max(0,run.frames.findIndex(f=>f.time_s>=t-1e-8));playTime=run.frames[index].time_s;render();}
function render(){
 if(!run)return;const f=current(),t=f.time_s,truth=run.truth[index];const rx=nearestBefore(run.received,t,'received_time_s');const prediction=nearestBefore(run.predictions,t);
 $('timeline').value=index;$('clock').textContent=`t = ${fmt(t)} s`;$('time-label').textContent=`${fmt(t)} / ${fmt(run.frames.at(-1).time_s)} s`;
 $('timeline').setAttribute('aria-valuetext',`${fmt(t)} giây, ${f.phase}`);
 badge('phase',f.phase);const info=phaseText[f.phase]||['Khởi tạo','Đang chuẩn bị chu kỳ.'];$('explain-title').textContent=info[0];$('explain').textContent=f.phase==='HOLD'?explanation(f.reason):info[1];
 $('estimate-y').textContent=fmt(f.estimate.y_m,3)+' m';$('uncertainty').textContent=fmt(f.estimate.uncertainty_m*1000,1)+' mm';if(f.estimate.uncertainty_m==null)$('uncertainty').textContent='—';
 $('age').textContent=rx?fmt((t-rx.source_time_s)*1000,0)+' ms':'Chưa có mẫu';$('belt-speed').textContent=fmt(f.command.long)+' m/s';
 const sensorNames={ps1:'PS1',ps2:'PS2',a1_retracted:'A1 thu',a1_extended:'A1 đẩy',a2_retracted:'A2 trên',a2_extended:'A2 dưới',vacuum_ok:'Hút OK',home_x:'Home X'};
 $('sensors').replaceChildren(...Object.entries(sensorNames).map(([key,label])=>{const v=rx?.values[key];const div=document.createElement('div');div.className='sensor '+(v===true?'on':v==null?'na':'');div.textContent=label;const strong=document.createElement('strong');strong.textContent=v==null?'CHƯA CÓ':v?'ON':'OFF';div.append(strong);return div;}));
 let message='Dự báo chưa hoạt động: chỉ chạy trong TRACK, băng dọc đang chạy và đã có ít nhất một neo quang.';
 if(!run.summary.prediction.enabled)message='Lượt điều khiển nền: không bật supervisor dự báo. Các giới hạn trình tự và watchdog vẫn hoạt động.';
 else if(prediction)message=`Lần dự báo gần nhất tại ${fmt(prediction.time_s)} s: ${prediction.action}. ${explanation(prediction.reason)} Đã tính ${prediction.completed_scenarios}/${prediction.expected_scenarios} tổ hợp trong ${fmt(prediction.compute_ms)} ms.`;
 if(f.phase==='HOLD')message=`HOLD · ${explanation(f.reason)}${prediction?' Quyết định dự báo gần nhất: '+prediction.action+'.':''}`;
 $('prediction-note').className='decision-box '+(f.phase==='HOLD'?'hold':'');$('prediction-note').textContent=message;
 $('raw').textContent=JSON.stringify({controller:f,last_received:rx,prediction_latest:prediction,truth_for_evaluation_only:truth},null,2);
 document.querySelectorAll('#phase-markers button').forEach(b=>b.classList.toggle('current',b.dataset.phase===f.phase));
 drawPlant(f,truth);drawHistory(t);
}
function surface(id){const canvas=$(id),r=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);const w=Math.max(1,r.width),h=Math.max(1,r.height);canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);return {ctx,w,h};}
function drawPlant(f,s){
 const {ctx:c,w,h}=surface('plant'),g=run.config.geometry;
 const scale=Math.min((w-64)/.79,(h-60)/.96), ox=w/2,oy=h/2+.01*scale;
 const X=x=>ox+x*scale,Y=y=>oy-y*scale;
 function line(x1,y1,x2,y2,color,width=1,dash=[]){c.beginPath();c.strokeStyle=color;c.lineWidth=width;c.setLineDash(dash);c.moveTo(X(x1),Y(y1));c.lineTo(X(x2),Y(y2));c.stroke();c.setLineDash([]);}
 function rect(x,y,dx,dy,color,stroke){c.fillStyle=color;c.fillRect(X(x-dx/2),Y(y+dy/2),dx*scale,dy*scale);if(stroke){c.strokeStyle=stroke;c.lineWidth=1;c.strokeRect(X(x-dx/2),Y(y+dy/2),dx*scale,dy*scale);}}
 function label(text,x,y,color='#aab9cd',align='left'){c.font='10px Segoe UI';c.fillStyle=color;c.textAlign=align;c.fillText(text,X(x),Y(y));}
 rect(0,0,.75,.92,'#111f30','#283c52');
 for(let x=-.35;x<=.35;x+=.05)for(let y=-.4;y<=.4;y+=.05){c.fillStyle='#2b3b50';c.fillRect(X(x),Y(y),1,1);}
 const front=g.front_belt_xy_m;rect((front[0][0]+front[0][1])/2,(front[1][0]+front[1][1])/2,front[0][1]-front[0][0]+.012,front[1][1]-front[1][0]+.016,'#456074');
 rect((front[0][0]+front[0][1])/2,(front[1][0]+front[1][1])/2,front[0][1]-front[0][0],front[1][1]-front[1][0],'#175342');
 const lane=g.lane_x_m,lo=g.long_belt_y_m[0],hi=g.long_belt_y_m[1];rect(lane,(lo+hi)/2,.10,hi-lo+.02,'#496276');rect(lane,(lo+hi)/2,.078,hi-lo,'#175342');
 for(let y=lo+.025;y<hi;y+=.036){line(lane-.018,y-.007,lane,y+.003,'#418976');line(lane,y+.003,lane+.018,y-.007,'#418976');}
 for(let x=front[0][0]+.025;x<front[0][1];x+=.04){line(x+.005,-.337,x-.005,-.325,'#418976');line(x-.005,-.325,x+.005,-.313,'#418976');}
 rect(lane,-.282,.082,.028,'#738897');
 const a1Y=-.377+s.a1_m;rect(lane,-.423+s.a1_m/2,.014,.06+s.a1_m,'#8a9bae');rect(lane,a1Y,.07,.006,'#c4d4e6');label('A1',lane+.049,-.405);
 // Base geometry and moving gantry are drawn in the model coordinate frame.
 line(-.305,.01,.305,.01,'#637b8d',5);line(-.305,.425,.305,.425,'#637b8d',5);
 const rx=g.robot_origin_xy_m[0]+s.x_m,ry=g.robot_origin_xy_m[1]+s.y_m;
 line(rx,0,rx,.435,'#a2b8c7',5);rect(rx,ry,.05,.053,'#314d64','#accbdf');
 g.bin_centers_xy_m.forEach(([x,y],i)=>{const size=g.bin_inner_size_xy_m;rect(x,y,size[0],size[1],'#1c2c43','#697d9b');rect(x,y,size[0]-.012,size[1]-.012,'#142238');label(String(i+1),x,y-.009,'#aebcd2','center');});
 for(const [name,y] of Object.entries(g.ps_y_m)){const active=s[name];rect(g.optical_xz_m[0],y,.024,.016,active?'#ffc876':'#ad7f38');line(g.optical_xz_m[0]+.012,y,lane+.04,y,active?'#ffd58e':'#8a7144',active?2:1,[4,4]);label(name.toUpperCase(),g.optical_xz_m[0]-.02,y+.012,active?'#ffd58e':'#aab9cd','right');}
 const p=s.product_xyz_m;rect(p[0],p[1],g.product_size_m[0],g.product_size_m[1],'#76e4bb','#d7fff0');
 if(f.estimate.y_m!=null && ['TRACK','ALIGN'].includes(f.phase)){
  const e=f.estimate,uu=e.uncertainty_m;c.strokeStyle='#7eb6ff';c.lineWidth=2;c.setLineDash([4,3]);c.strokeRect(X(lane-.016),Y(e.y_m+.016),.032*scale,.032*scale);c.setLineDash([]);line(lane+.065,e.y_m-uu,lane+.065,e.y_m+uu,'#7eb6ff',2);line(lane+.05,e.y_m-uu,lane+.08,e.y_m-uu,'#7eb6ff');line(lane+.05,e.y_m+uu,lane+.08,e.y_m+uu,'#7eb6ff');
 }
 c.beginPath();c.arc(X(rx),Y(ry),8,0,Math.PI*2);c.strokeStyle=s.vacuum_command?'#ffc876':'#d1dfed';c.lineWidth=2;c.stroke();
 label('XY / A2',rx+.035,ry+.028,'#d1dfed');label('BĂNG NGANG',.02,-.405);label('BĂNG DỌC',-.32,.3);label(`A2: ${fmt(s.a2_m*1000,0)} mm`,.015,.397);label(`Z phôi: ${fmt(p[2]*1000,0)} mm`,.015,.365);
 line(-.32,-.44,-.22,-.44,'#aab9cd',2);label('100 mm',-.27,-.475,'#aab9cd','center');
}
function drawHistory(t){
 const {ctx:c,w,h}=surface('history'),pad={l:48,r:16,t:16,b:28},maxT=run.frames.at(-1).time_s;
 const X=x=>pad.l+x/maxT*(w-pad.l-pad.r),Y=y=>h-pad.b-(y+.29)/.56*(h-pad.b-pad.t);
 c.font='10px Consolas';c.textAlign='right';
 for(const y of [-.25,0,.2]){c.strokeStyle='#30415a';c.beginPath();c.moveTo(pad.l,Y(y));c.lineTo(w-pad.r,Y(y));c.stroke();c.fillStyle='#aab9cd';c.fillText(fmt(y,2),pad.l-8,Y(y)+4);}
 c.textAlign='center';for(let x=0;x<=maxT;x+=2){c.fillStyle='#aab9cd';c.fillText(fmt(x,0)+' s',X(x),h-6);}
 for(const [isEst,color,dash] of [[false,'#76e4bb',[]],[true,'#7eb6ff',[4,3]]]){c.beginPath();c.strokeStyle=color;c.lineWidth=2;c.setLineDash(dash);let open=false;for(let i=0;i<run.frames.length;i++){const f=run.frames[i];if(!['TRACK','ALIGN'].includes(f.phase)){open=false;continue;}const y=isEst?f.estimate.y_m:run.truth[i].product_xyz_m[1];let time=f.time_s;if(isEst){const seq=f.estimate_source_sequence;time=seq==null?time:run.truth[seq]?.time_s??time;}if(y==null){open=false;continue;}if(open)c.lineTo(X(time),Y(y));else{c.moveTo(X(time),Y(y));open=true;}}c.stroke();c.setLineDash([]);}
 c.strokeStyle='#ffc876';c.beginPath();c.moveTo(X(t),pad.t);c.lineTo(X(t),h-pad.b);c.stroke();
}
const flow=[
 ['01','Máy mô phỏng','run_cell.py / MuJoCo','Mô phỏng vật lý','MuJoCo tiến bước vật lý 2 ms cho băng tải, A1, robot XY, A2 và phôi. Vị trí thật được đưa vào mô hình cảm biến và bộ đánh giá; bộ điều khiển không được đọc trực tiếp vị trí phôi này.'],
 ['02','Cảm biến & mạng','sensor_model.py / network.py','Tín hiệu không phải sự thật tức thời','Mỗi 20 ms, mô hình cảm biến tạo trạng thái PS1, PS2 và công tắc hành trình, cùng số thứ tự và thời điểm nguồn. Mạng có thể trễ hoặc làm mất mẫu. Gói cũ bị loại; tuổi dữ liệu được kiểm tra. Chưa mô phỏng đồng bộ đồng hồ PLC thật.'],
 ['03','Ước lượng','estimator.py','DT biết phôi đang ở đâu bằng cách nào?','Sau PS1, DT dựa vào tốc độ lệnh để tích phân vị trí một phôi. Khi nhận PS2, khoảng cách hai cảm biến chia cho thời gian di chuyển cho một ước lượng vận tốc. Sai số cho phép tăng dần giữa các neo; đây chưa phải khoảng tin cậy thống kê đã hiệu chuẩn.'],
 ['04','Trình tự','sequence.py','Ai quyết định đẩy, gắp và thả?','Máy trạng thái xử lý thứ tự FEED → PUSH → TRACK → gắp → thả. Công tắc, giới hạn thời gian, watchdog và điều kiện đủ phản hồi quyết định chuyển trạng thái. Chế độ nghiêm ngặt HOLD khi thiếu xác nhận XY/A2/hút.'],
 ['05','Dự báo & giám sát','predictor.py / supervisor.py','Tính trước rồi chọn một bước','Trong TRACK sau neo quang, predictor chạy 54 tổ hợp động học 1D. Supervisor cho đi thêm một tick hoặc giữ HOLD theo biên dừng xấu nhất. Không tính kịp cũng HOLD. Đây chưa phải lập lịch tối ưu toàn nhà máy hoặc tự phục hồi sau lỗi.'],
 ['06','Đánh giá riêng','evaluation.py / experiment.py','Làm sao biết kết quả có đúng?','Bộ đánh giá nhận vị trí thật của MuJoCo để tính sai số theo cùng thời điểm nguồn và kiểm tra đặt phôi. Nó không cung cấp đáp án cho estimator hoặc supervisor. Nhật ký có cấu hình hiệu lực, hash mã nguồn và hash dữ liệu để truy xuất.']
];
flow.forEach(([n,title,file,heading,copy],i)=>{const b=document.createElement('button');b.innerHTML=`<span>${n} /</span>${title}`;b.setAttribute('aria-pressed',String(i===0));b.onclick=()=>{document.querySelectorAll('#flow button').forEach(x=>x.setAttribute('aria-pressed','false'));b.setAttribute('aria-pressed','true');$('flow-file').textContent=file;$('flow-title').textContent=heading;$('flow-copy').textContent=copy;};$('flow').append(b);if(i===0)b.click();});
function labValues(){return {y:Number($('y').value),speed:Number($('speed').value),uncertainty:Number($('uncertainty-input').value),age:Number($('age-input').value)};}
function updateLabLabels(){const v=labValues();$('y-value').textContent=fmt(v.y,3)+' m';$('speed-value').textContent=fmt(v.speed)+' m/s';$('uncertainty-input-value').textContent=fmt(v.uncertainty*1000,0)+' mm';$('age-input-value').textContent=fmt(v.age*1000,0)+' ms';}
let labVersion=0;
function invalidateLab(){labVersion++;updateLabLabels();latestLab=null;badge('lab-action','CHƯA CHẠY');$('lab-metrics').replaceChildren();$('lab-explain').textContent='Đầu vào đã thay đổi. Chạy lại để xem quyết định tương ứng.';drawForecast();}
function drawForecast(){
 const {ctx:c,w,h}=surface('forecast');c.font='11px Consolas';
 if(!latestLab){c.fillStyle='#aab9cd';c.textAlign='center';c.fillText('Chọn thông số → Chạy bộ dự báo',w/2,h/2);return;}
 const {curves,limit}=latestLab;const all=curves.flatMap(row=>row.points.map(p=>p[1]));let low=Math.min(...all,limit)-.004,high=Math.max(...all,limit)+.004;
 const left=58,right=w-16,top=20,bottom=h-30;const X=t=>left+t/.5*(right-left),Y=y=>bottom-(y-low)/(high-low)*(bottom-top);
 for(let i=0;i<5;i++){const y=low+(high-low)*i/4;c.strokeStyle='#2b3c53';c.beginPath();c.moveTo(left,Y(y));c.lineTo(right,Y(y));c.stroke();c.fillStyle='#aab9cd';c.textAlign='right';c.fillText(fmt(y,3),left-8,Y(y)+4);}
 c.textAlign='center';for(let i=0;i<=5;i++)c.fillText(fmt(i/10,1)+' s',X(i/10),h-7);
 c.save();c.beginPath();c.rect(left,top,right-left,bottom-top);c.clip();c.fillStyle='#ff969e0d';c.fillRect(left,top,right-left,Y(limit)-top);
 for(const row of curves){c.beginPath();c.strokeStyle=row.policy==='CONTINUE'?'#76e4bb60':'#7eb6ff70';c.lineWidth=1.2;c.setLineDash(row.policy==='HOLD'?[3,3]:[]);row.points.forEach(([t,y],i)=>i?c.lineTo(X(t),Y(y)):c.moveTo(X(t),Y(y)));c.stroke();}
 c.setLineDash([6,4]);c.strokeStyle='#ff969e';c.lineWidth=2;c.beginPath();c.moveTo(left,Y(limit));c.lineTo(right,Y(limit));c.stroke();c.restore();c.fillStyle='#ffb6bd';c.textAlign='right';c.fillText('Giới hạn '+fmt(limit,3)+' m',right,Y(limit)-7);
}
async function compute(){
 const version=labVersion,button=$('compute');button.disabled=true;button.textContent='Đang tính…';$('lab-explain').className='';
 try{const response=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(labValues())});const data=await response.json();if(!response.ok)throw Error(data.error||'Không tính được');if(version!==labVersion)return;latestLab=data;const r=data.result;badge('lab-action',r.action);$('lab-explain').textContent=explanation(r.reason);$('lab-metrics').replaceChildren(metric('Tổ hợp hoàn tất',`${r.completed_scenarios} / ${r.expected_scenarios}`),metric('Biên CONTINUE',fmt(r.margins_m.CONTINUE*1000,1)+' mm'),metric('Biên HOLD',fmt(r.margins_m.HOLD*1000,1)+' mm'),metric('Tính lõi · lần này',fmt(r.compute_ms)+' ms'),metric('Chân trời',fmt(.5,1)+' s'),metric('Bước thực thi',fmt(data.period*1000,0)+' ms'));drawForecast();}
 catch(error){if(version===labVersion){badge('lab-action','LỖI');$('lab-explain').className='error';$('lab-explain').textContent='Không gọi được lõi Python. Hãy mở bằng START_EXPLORER.cmd thay vì mở HTML trực tiếp. '+error.message;}}
 finally{button.disabled=false;button.textContent='Chạy bộ dự báo';}
}
$('lab-form').onsubmit=e=>{e.preventDefault();compute();};
['y','speed','uncertainty-input','age-input'].forEach(id=>$(id).oninput=invalidateLab);
document.querySelectorAll('[data-lab]').forEach(b=>b.onclick=()=>{const values={clear:[.12,.16,.006,.02],edge:[.2,.16,.006,0],stale:[.18,.16,.006,.18]}[b.dataset.lab];['y','speed','uncertainty-input','age-input'].forEach((id,i)=>$(id).value=values[i]);invalidateLab();});
$('use-frame').onclick=()=>{const f=current(),rx=run&&nearestBefore(run.received,f.time_s,'received_time_s');if(!f||f.estimate.y_m==null||!['TRACK','ALIGN'].includes(f.phase)){ $('lab-explain').textContent='Hãy chọn một mẫu TRACK/ALIGN đã có ước lượng vị trí trước khi nhập vào phòng dự báo.';return;}const e=f.estimate;$('y').value=e.y_m;$('speed').value=e.velocity_m_s;$('uncertainty-input').value=e.uncertainty_m;$('age-input').value=rx?Math.max(0,f.time_s-rx.source_time_s):0;invalidateLab();};
$('scenario').onchange=()=>loadCase($('scenario').value);
document.querySelectorAll('[data-case]').forEach(b=>b.onclick=()=>loadCase(b.dataset.case));
$('play').onclick=()=>{if(!run)return;if(playing){stop();return;}if(index===run.frames.length-1){index=0;render();}playing=true;playTime=current().time_s;lastWall=performance.now();$('play').textContent='Tạm dừng';};
$('step').onclick=()=>{stop();if(run){index=Math.min(index+1,run.frames.length-1);render();}};
$('reset').onclick=()=>{stop();if(run){index=0;render();}};
$('timeline').oninput=()=>{stop();index=Number($('timeline').value);render();};
$('download').onclick=()=>{if(!run)return;const blob=new Blob([JSON.stringify(run,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=run.id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('tour').onclick=()=>{stop();$('guide').showModal();};$('close-guide').onclick=()=>$('guide').close();
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
window.addEventListener('resize',()=>{render();drawForecast();});
function animate(now){if(playing&&run){playTime+=(now-lastWall)/1000*Number($('rate').value);lastWall=now;while(index<run.frames.length-1&&run.frames[index+1].time_s<=playTime)index++;if(index!==lastIndex){render();lastIndex=index;}if(index===run.frames.length-1)stop();}requestAnimationFrame(animate);}requestAnimationFrame(animate);
async function init(){try{const response=await fetch('data/index.json');if(!response.ok)throw Error('Thiếu dữ liệu phát lại. Chạy build_replays.py trước.');const list=await response.json();$('scenario').replaceChildren(...list.map(row=>{const o=document.createElement('option');o.value=row.id;o.textContent=row.label;return o;}));await loadCase(list[0].id);}catch(error){$('error').hidden=false;$('error').textContent=error.message;}updateLabLabels();drawForecast();}
let activeJob=null, jobTimer=null, experimentsReady=false;
async function api(path,body){
 const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const value=await response.json();if(!response.ok)throw Error(value.error||`HTTP ${response.status}`);return value;
}
function jobPayload(){return {profile:$('experiment-profile').value,speed:Number($('experiment-speed').value),fault:$('experiment-fault').value,
 delay_ms:Number($('experiment-delay').value),jitter_ms:Number($('experiment-jitter').value),loss_pct:Number($('experiment-loss').value),seed:Number($('experiment-seed').value),
 bin:Number($('experiment-bin').value),predictive:$('experiment-predictive').checked,assume_open_loop:$('experiment-assume').checked,compare:$('experiment-compare').checked};}
function updateCompare(){const paired=$('experiment-compare').checked;$('experiment-predictive').disabled=paired;$('experiment-predictive').parentElement.title=paired?'Chạy cặp luôn xét cả hai chế độ.':'Chọn chế độ cho một lượt.';}
$('experiment-compare').onchange=updateCompare;updateCompare();
async function openTrial(job,trial){
 try{const data=await api(`/api/experiments/${job}/replay/${trial}`);cache.set(data.id,data);
  if(!Array.from($('scenario').options).some(o=>o.value===data.id)){const option=document.createElement('option');option.value=data.id;option.textContent=`Mới ${job.slice(0,8)} · ${trial}`;$('scenario').append(option);}
  await loadCase(data.id);$('replay').scrollIntoView({behavior:'auto'});
 }catch(error){$('job-state').textContent=error.message;}
}
function showJob(job){
 const labels={queued:'Đang chuẩn bị',running:'Đang mô phỏng',completed:'Hoàn tất tính toán',failed:'Chạy không thành công',interrupted:'Lượt bị gián đoạn'};
 const p=job.progress;const detail=p?.stage==='simulating'?` · lượt ${p.number}/${p.total}: ${p.trial}`:'';
 $('job-state').textContent=`${labels[job.state]||job.state}${detail} · ID ${job.id.slice(0,8)}${job.error?' · '+job.error:''}`;
 $('job-result').hidden=true;
 if(job.state!=='completed')return;
 const box=$('job-result');box.hidden=false;box.replaceChildren();
 const heading=document.createElement('h3');heading.textContent='Kết quả mới từ MuJoCo';box.append(heading);
 const date=new Date(job.created_at).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'});
 const request=document.createElement('p');request.className='fine';request.textContent=`${date} (giờ Việt Nam) · ${job.request.profile} · ${job.request.speed} m/s · ${job.request.fault} · mạng ${job.request.delay_ms} ± ${job.request.jitter_ms} ms / mất ${job.request.loss_pct}% / seed ${job.request.seed} · hộp ${job.request.bin} · ${job.request.assume_open_loop?'cho phép hở vòng':'phản hồi nghiêm ngặt'}`;box.append(request);
 for(const row of job.result.trials){const s=row.summary;const section=document.createElement('div');section.className='trial-row';
  const title=document.createElement('strong');title.textContent=`${row.trial==='baseline'?'Điều khiển nền':'Có dự báo'} · ${s.controller_state}`;
  const outcome=document.createElement('p');outcome.textContent=s.controller_state==='DONE'?`Đặt phôi: ${s.placement_pass_evaluator_only===true?'ĐẠT':'KHÔNG ĐẠT'}.`:`Lý do: ${explanation(s.hold_reason)} Phôi được đỡ: ${s.hold_product_supported_evaluator_only===true?'đạt tiêu chí':'chưa đạt tiêu chí'}.`;
  const info=document.createElement('p');info.className='fine';info.textContent=`Thời gian mô phỏng ${fmt(s.simulation_time_s)} s · HOLD lúc ${fmt(s.hold_time_s)} s · p95 tính dự báo ${fmt(s.prediction.compute_p95_ms)} ms · config ${s.config_sha256.slice(0,12)}…`;
  const button=document.createElement('button');button.type='button';button.textContent=`Xem lượt ${row.trial}`;button.onclick=()=>openTrial(job.id,row.trial);
  section.append(title,outcome,info,button);box.append(section);
 }
 if(job.result.comparison){const compare=job.result.comparison;const text=document.createElement('p');text.className='decision-box';
  text.textContent=compare.earlier_hold_s!=null?`Trong cặp thử này, dự báo HOLD sớm hơn nền ${fmt(compare.earlier_hold_s*1000,0)} ms mô phỏng.`:compare.cycle_time_delta_s!=null?`Cả hai lượt đặt phôi đạt. Thời gian nền trừ thời gian có dự báo: ${fmt(compare.cycle_time_delta_s,3)} s mô phỏng.`:'Hai lượt đã chạy cùng điều kiện yêu cầu; lý do dừng hoặc kết quả khác nhau nên không quy đổi thành mức tăng tốc hay “phát hiện sớm”.';
  text.textContent+=' Một cặp mô phỏng không xác nhận hiệu quả trên máy thật hoặc độ chính xác chẩn đoán lỗi.';box.append(text);
 }
}
async function refreshJobs(){
 const list=await api('/api/experiments');$('job-history').replaceChildren();
 for(const job of list){const button=document.createElement('button');button.type='button';button.textContent=`${job.id.slice(0,8)} · ${job.state} · ${job.request.fault}`;
 button.onclick=()=>{if(['running','queued'].includes(job.state))watchJob(job.id);else showJob(job);};$('job-history').append(button);}
 if(!list.length)$('job-history').textContent='Chưa có lịch sử. Kết quả mới sẽ được lưu trên máy này.';
}
async function watchJob(id){
 clearTimeout(jobTimer);activeJob=id;$('start-experiment').disabled=true;
 try{const job=await api(`/api/experiments/${id}`);showJob(job);
  if(['queued','running'].includes(job.state)){jobTimer=setTimeout(()=>watchJob(id),1200);return;}
  activeJob=null;$('start-experiment').disabled=!experimentsReady;await refreshJobs();
 }catch(error){activeJob=null;$('start-experiment').disabled=!experimentsReady;$('job-state').textContent='Không đọc được trạng thái: '+error.message;}
}
$('experiment-form').onsubmit=async event=>{
 event.preventDefault();$('start-experiment').disabled=true;$('job-state').textContent='Đang gửi yêu cầu chạy mô phỏng…';
 try{const job=await api('/api/experiments',jobPayload());await watchJob(job.id);}
 catch(error){$('job-state').textContent=error.message;$('start-experiment').disabled=!experimentsReady;}
};
async function initExperiments(){
 try{const capabilities=await api('/api/capabilities');experimentsReady=capabilities.enabled;
 $('backend-state').textContent=experimentsReady?`Bộ chạy ${capabilities.backend} · giới hạn worker ${capabilities.wall_timeout_s} s / yêu cầu`:'Chế độ xem. Muốn chạy mới: mở START_SIMULATION_EXPLORER.cmd với môi trường MuJoCo WSL đã cài.';
 $('start-experiment').disabled=!experimentsReady;await refreshJobs();if(capabilities.active_job)watchJob(capabilities.active_job);
 }catch(error){$('backend-state').textContent='Không tìm thấy API thí nghiệm. Hãy khởi động lại máy chủ bằng START_SIMULATION_EXPLORER.cmd.';}
}
init();initExperiments();
