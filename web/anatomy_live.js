/* Anatomy renderer: the recorded sample drives both pose and readout. No PLC output. */
(()=>{
const data=JSON.parse(document.getElementById('anatomy-data').textContent);
const $=id=>document.getElementById(id), stage=$('stage');
const P=fitProjection(boxCorners({x:-380,y:-500,w:760,d:1000,r:0},-30,380),940,680,{pad:35,azimuth:-45,elevation:38});
const scene=[];
const selected={};
function add(name,p,s,tone='mid',pick='machine',inner=''){
 const plan={x:p[0]-s[0],y:p[1]-s[1],w:s[0]*2,d:s[1]*2,r:Math.min(1.2,s[0]/3,s[1]/3)};
 const g=document.createElementNS('http://www.w3.org/2000/svg','g');
 g.dataset.pick=pick;g.dataset.name=name;
 const title=document.createElementNS(g.namespaceURI,'title');title.textContent=name;g.appendChild(title);
 g.insertAdjacentHTML('beforeend',solidSvg(slabOf(plan,p[2]-s[2],2*s[2],P,3,.4),{tone,lit:tone==='hi'&&name==='product',inner}));
 const item={g,p:p.slice(),s:s.slice(),name};scene.push(item);return item;
}
const M=v=>v.map(x=>x*1000);
for(const a of data.geometry){
 if(a.name==='product_box')continue;
 const n=a.name;
 const pick=a.site?'sensors':n.includes('belt')||n.includes('rail')||n==='transfer_bridge'?'belts':n.includes('pusher')?'pusher':n.includes('bin_')?'bins':n.includes('carriage')||n.includes('beam')?'robot':'machine';
 const item=add(n,M(a.p),M(a.s),n.includes('belt')?'lo':a.site?'hi':'mid',pick);
 if(a.site)selected[n]=item;
}
// Teaching details on the existing base; these are illustrative hardware, not CAD measurements.
for(const [x,y] of [[-350,-470],[350,-470],[-350,470],[350,470]]){
 add('base_fastener',[x,y,.6],[4,4,.6],'lo');
 add('base_fastener_slot',[x,y,1.35],[2.7,.6,.15],'hi');
}
for(const [x,y] of [[-140,-335],[-140,0],[180,-335]]){
 add('conveyor_support',[x,y,43],[12,12,43],'lo','belts');
}
for(const a of data.geometry.filter(a=>a.site)){
 const [x,y,z]=M(a.p);
 if(a.name!=='transfer_present_beam'){
  add('optical_mount',[x-9,y,z/2],[3,9,z/2],'mid','sensors');
  add('optical_case',[x-4,y,z],[6,9,8],'hi','sensors');
 }
}
// A square symbolic cup, intentionally not presented as a detailed pneumatic CAD model.
add('cup_symbol',[-140,60,238],[11,11,8],'lo','robot');
add('a2_reference_body',[-140,60,296],[15,15,47],'mid','robot');
const product=add('product',[0,0,0],data.product_size_m.map(x=>x*500),'hi','product');
const ghost=add('counterfactual',[0,0,0],data.product_size_m.map(x=>x*500),'mid','product');ghost.g.classList.add('ghost');
stage.innerHTML=figureSvg({width:940,height:680,label:'Dây chuyền hai băng tải, bộ đẩy, robot XY, sáu hộp và ba vị trí cảm biến; phôi chuyển động theo nhật ký MuJoCo.',body:[]});
const svg=stage.querySelector('svg');const world=document.createElementNS(svg.namespaceURI,'g');svg.appendChild(world);
const topics={
 machine:['Dây chuyền và giới hạn hình học','Hai băng tải đưa một phôi đến điểm gắp; robot XY và xi lanh nâng hạ phục vụ đưa phôi vào hộp. Hình lấy từ effective_model.xml của chính ca thử. Chi tiết đỡ và vít là minh họa; đây chưa phải bản CAD V5 đã đồng bộ.'],
 belts:['Hai băng tải','Lệnh chạy không chứng minh băng tải thực sự chạy. Bảng bên phải hiển thị cả lệnh DT và tốc độ áp dụng ở mô phỏng để người xem đối chiếu. Lõi DT không được đọc tốc độ áp dụng vì hệ hiện tại chưa có phản hồi tốc độ đã xác nhận.'],
 pusher:['Xi lanh đẩy và PS1','PS1 nằm trên đầu đẩy, tia quét cùng phương đẩy. Tên logic là transfer_present. Tư thế đầu đẩy trong hình là tham chiếu vì bộ nhật ký này không ghi vị trí khớp; không lấy lệnh đặt làm số đo vị trí thực.'],
 robot:['Robot XY và đầu hút','Các ca nghiêm ngặt dừng trước bước gắp khi chưa xác nhận vị trí XY, hành trình giữa của A2 và chân không. Vì vậy hình không tự diễn hoạt một thao tác gắp chưa được kiểm chứng. Chuyển động robot ở đây là tư thế tham chiếu, không phải phản hồi đo.'],
 sensors:['Ba cảm biến quang','PS1 trên đầu đẩy → transfer_present; PS2 phía trước → ps1; PS3 điểm gắp → ps2. Đèn trong bảng là bit mà DT nhận. Nếu bị chèn lỗi, bit này có thể khác tia cảm biến lý tưởng. Phản hồi chưa có được ghi là chưa có dữ liệu, không phải tắt.'],
 product:['Hai loại vị trí phôi','Khối sáng lấy từ vị trí thật do MuJoCo ghi, chỉ dành cho người đánh giá. Vị trí DT ước lượng được tính từ tín hiệu thưa và lịch sử lệnh; có thể chưa biết hoặc sai khi truyền động không thực hiện đúng lệnh. Khối mờ là phôi của ca đối chiếu ở cùng thời điểm.'],
 bins:['Sáu hộp nhận phôi','Hộp có đáy và thành theo mô hình chức năng. Nghiên cứu đang xem chỉ kiểm tra tín hiệu và điều kiện dừng; không chứng minh toàn chu kỳ gắp–thả đã hoàn thành trong chế độ nghiêm ngặt.']};
const steps=[['Tín hiệu','sensors','1 · Thu nhận','Khung tín hiệu gồm giá trị, thời gian và chất lượng. Bộ đọc phân biệt true, false và null (chưa có phản hồi); dữ liệu không tự chứng minh cảm biến còn tốt.'],['Mạng','network','2 · Kiểm tra đầu vào','Kiểm tra thứ tự gói, dấu thời gian, đúng phiên và tuổi dữ liệu. Đây là mô đun có thật trong lõi, nhưng bảy ca đang xem truyền khung trực tiếp, không chèn trễ/mất gói. Không dùng các ca này để kết luận hiệu năng mạng.'],['Ước lượng','observer','3 · Suy ra vị trí','DT dùng mốc cảm biến và lịch sử lệnh chạy để ước lượng vị trí dọc băng. Cột vị trí ước lượng đọc từ nhật ký lõi, không sao chép vị trí thật của MuJoCo.'],['Dự báo','forecast','4 · Thử tương lai ngắn','Khi có đủ trạng thái, bộ dự báo 1D thử các tổ hợp sai số vị trí, tốc độ và trễ phản ứng để chọn tiếp tục hoặc giữ. 54 tổ hợp không có nghĩa là 54 loại lỗi. Bảng chỉ hiện kết quả thực sự ghi tại mẫu đang xem.'],['Bất thường','health','5 · Tìm dấu hiệu','Quy tắc kiểm tra thiếu cạnh cảm biến, thời gian di chuyển vô lý hoặc thứ tự bất hợp lý. Phát hiện dấu hiệu không đồng nghĩa đã biết chính xác cảm biến hay động cơ nào hỏng.'],['Quyết định','decision','6 · Giữ chu trình','Bộ điều phối kết hợp điều kiện chu trình, tuổi dữ liệu, dự báo và dấu hiệu bất thường. HOLD được giữ, không tự xóa. Trang này phát lại quyết định đã ghi; bấm nút không gửi lệnh đến PLC.']];
function detail(title,text){$('detail').replaceChildren();const h=document.createElement('h3');h.textContent=title;const p=document.createElement('p');p.textContent=text;$('detail').append(h,p);}
steps.forEach(([label,id,title,text],j)=>{const b=document.createElement('button');b.type='button';b.innerHTML='<small>0'+(j+1)+'</small>'+label;b.onclick=()=>{document.querySelectorAll('.steps button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));detail(title,text)};$('steps').appendChild(b)});
stage.addEventListener('click',ev=>{const node=ev.target.closest('[data-pick]');if(node&&topics[node.dataset.pick])detail(...topics[node.dataset.pick]);});
const phaseNames={FEED:'Cấp phôi',PUSH:'Đẩy phôi',RETRACT:'Thu đầu đẩy',TRACK:'Theo dõi trên băng',HOLD:'Giữ chu trình',DONE:'Hoàn tất'};
const reasons={
 'unconfirmed_xy_a2_midstroke_and_vacuum':['Thiếu phản hồi để gắp','Chế độ nghiêm ngặt yêu cầu xác nhận XY, vị trí A2 và chân không. Ca bình thường vẫn dừng tại đây; chưa có lỗi cảm biến được xác định.'],
 'timeout:FEED:transfer_present':['Không thấy phôi ở đầu đẩy','Hết thời gian chờ PS1. Có thể do cảm biến không báo hoặc phôi chưa tới; dữ liệu hiện tại không phân biệt được hai nguyên nhân.'],
 'reconfiguration:expected_edge_missing':['Thiếu cạnh cảm biến đúng hạn','Không thấy PS3 như dự kiến sau mốc PS2. Chưa thể kết luận PS3 hỏng hay băng dọc đã đứng.'],
 'implausible_transit_speed':['Tín hiệu đến quá sớm','Khoảng thời gian giữa các mốc không hợp lý với miền tốc độ cho phép; lõi giữ chu trình.'],
 'ps2_without_ps1':['Sai thứ tự mốc cảm biến','PS3 đã báo nhưng thiếu mốc PS2 trước đó; không tự bỏ qua cảm biến để tiếp tục.']};
data.trials.forEach((t,i)=>{const opt=document.createElement('option');opt.value=String(i);opt.textContent=t.label;$('case').appendChild(opt)});
const pairs={feed_sensor_missing:'feed_drive_stall',feed_drive_stall:'feed_sensor_missing',pickup_sensor_missing:'long_drive_stall',long_drive_stall:'pickup_sensor_missing'};
let trial=data.trials[0], index=0, playing=false, frameId=0,last=0,clock=0,visible=true;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
function frameAt(t,time){let lo=0,hi=t.frames.length-1;while(lo<hi){const m=Math.ceil((lo+hi)/2);if(t.frames[m].t<=time+1e-8)lo=m;else hi=m-1;}return t.frames[lo]}
function pose(item,p){item.p=M(p);item.g.setAttribute('transform',translateAlong(P,item.p));}
function render(){
 const f=trial.frames[index],pairId=pairs[trial.id],paired=data.trials.find(x=>x.id===pairId);
 pose(product,f.p);const show=$('compare').checked&&!!paired;ghost.g.style.display=show?'':'none';
 if(show){const other=frameAt(paired,f.t);pose(ghost,other.p);const distance=Math.hypot(...f.p.map((v,i)=>v-other.p[i]));$('comparison').textContent='Đối chiếu: '+paired.label+' · chênh vị trí '+(distance*100).toFixed(1)+' cm. Cùng thời điểm; so chuỗi tương đương tới HOLD đầu tiên.';}
 else $('comparison').textContent=paired?'Có ca đối chiếu với cùng chuỗi quan sát tới HOLD.':'Ca này không có cặp tương đương được chứng minh trong nghiên cứu.';
 // Axis-separating planes order disjoint boxes; not a contact/collision certificate.
 const view=[...towardViewer(P),Math.tan(38*Math.PI/180)];
 const edges=scene.map(()=>[]),counts=scene.map(()=>0);
 const bounds=scene.map(a=>{const pts=boxCorners({x:a.p[0]-a.s[0],y:a.p[1]-a.s[1],w:a.s[0]*2,d:a.s[1]*2,r:0},a.p[2]-a.s[2],a.p[2]+a.s[2]).map(p=>iso(p,P));return [Math.min(...pts.map(p=>p[0])),Math.min(...pts.map(p=>p[1])),Math.max(...pts.map(p=>p[0])),Math.max(...pts.map(p=>p[1]))]});
 for(let a=0;a<scene.length;a++)for(let b=a+1;b<scene.length;b++){
   const ba=bounds[a],bb=bounds[b];
   if(ba[2]<=bb[0]+.1||bb[2]<=ba[0]+.1||ba[3]<=bb[1]+.1||bb[3]<=ba[1]+.1)continue;
   const left=scene[a],right=scene[b],signs=[];
   for(let axis=0;axis<3;axis++){
     if(left.p[axis]+left.s[axis]<=right.p[axis]-right.s[axis]+1e-6)signs.push(view[axis]>=0?1:-1);
     else if(right.p[axis]+right.s[axis]<=left.p[axis]-left.s[axis]+1e-6)signs.push(view[axis]>=0?-1:1);
   }
   if(signs.length&&signs.every(s=>s===signs[0])){const from=signs[0]>0?a:b,to=signs[0]>0?b:a;edges[from].push(to);counts[to]++;}
 }
 const queue=scene.map((_,i)=>i).filter(i=>!counts[i]),sorted=[];
 while(queue.length){queue.sort((a,b)=>depthOf(scene[b].p,P)-depthOf(scene[a].p,P));const i=queue.pop();sorted.push(scene[i]);for(const next of edges[i])if(!--counts[next])queue.push(next);}
 stage.dataset.orderCycles=String(scene.length-sorted.length);
 // Remaining interpenetrating reference parts have no strict separating plane.
 scene.filter(x=>!sorted.includes(x)).sort((a,b)=>depthOf(a.p,P)-depthOf(b.p,P)).forEach(x=>sorted.push(x));
 sorted.forEach(a=>world.appendChild(a.g));
 $('timeline').max=String(trial.frames.length-1);$('timeline').value=String(index);
 $('clock').textContent=f.t.toFixed(2)+' / '+trial.frames.at(-1).t.toFixed(2)+' s';
 $('readout').textContent='Phôi '+(f.p[0]*1000).toFixed(0)+', '+(f.p[1]*1000).toFixed(0)+', '+(f.p[2]*1000).toFixed(0)+' mm';
 const isHold=f.phase==='HOLD';$('phase').textContent=phaseNames[f.phase]||f.phase;$('status').dataset.hold=String(isHold);$('mode').textContent=isHold?'HOLD · GIỮ CHU TRÌNH':'ĐANG PHÁT LẠI DỮ LIỆU';
 const meaning=reasons[f.reason]||[phaseNames[f.phase]||f.phase,'Lõi đang xử lý chu trình theo khung tín hiệu và các điều kiện hiện có.'];$('reason').textContent=meaning[0];$('meaning').textContent=meaning[1];
 $('sensors').replaceChildren();
 [['PS1 · đầu đẩy','transfer_present'],['PS2 · phía trước','ps1'],['PS3 · điểm gắp','ps2'],['Chân không','vacuum_ok']].forEach(([label,key])=>{const row=document.createElement('div');row.className='signal';row.dataset.on=String(f.o[key]);const a=document.createElement('span');a.textContent=label;const b=document.createElement('b');b.textContent=f.o[key]===null?'CHƯA CÓ':f.o[key]?'CÓ':'KHÔNG';row.append(a,b);$('sensors').appendChild(row)});
 for(const key of ['front','long'])$(key).textContent=f.command[key].toFixed(2)+' / '+f.applied[key].toFixed(2)+' m/s';
 $('estimate').textContent=f.estimate.y_m===null?'Chưa biết':(f.estimate.y_m*1000).toFixed(0)+' mm ± '+(f.estimate.uncertainty_m*1000).toFixed(0);
 $('prediction').textContent=(f.policy.observation_age_s*1000).toFixed(0)+' ms / '+(f.prediction?f.prediction.action:'chưa chạy');
 $('compare').disabled=!paired;$('play').textContent=playing?'Tạm dừng':'Phát lại';stage.dataset.sample=String(index);stage.dataset.parts=String(scene.length);
}
function stop(){playing=false;if(frameId)cancelAnimationFrame(frameId);frameId=0;render()}
function tick(now){frameId=0;if(!playing||!visible||document.hidden)return;const dt=last?Math.min((now-last)/1000,.05):0;last=now;clock+=dt;const f=frameAt(trial,clock);index=trial.frames.indexOf(f);if(clock>=trial.frames.at(-1).t)playing=false;render();if(playing)frameId=requestAnimationFrame(tick)}
function play(){if(reduced.matches){detail('Chế độ giảm chuyển động','Tự phát đã tắt theo cài đặt thiết bị. Dùng thanh tua hoặc phím mũi tên để xem từng mẫu.');return}if(index===trial.frames.length-1)index=0;clock=trial.frames[index].t;last=0;playing=true;render();if(visible&&!frameId)frameId=requestAnimationFrame(tick)}
$('play').onclick=()=>playing?stop():play();$('start').onclick=()=>{stop();index=0;render()};$('timeline').oninput=()=>{const next=Number($('timeline').value);stop();index=next;render()};
$('hold').onclick=()=>{stop();index=trial.frames.findIndex(f=>f.phase==='HOLD');if(index<0)index=trial.frames.length-1;render()};
$('case').onchange=()=>{stop();trial=data.trials[Number($('case').value)];index=0;$('compare').checked=false;render()};$('compare').onchange=render;
$('theme').onclick=()=>{document.body.dataset.theme=document.body.dataset.theme==='light'?'dark':'light'};
stage.onkeydown=e=>{if([' ','ArrowRight','ArrowLeft','Home','End','Escape'].includes(e.key))e.preventDefault();if(e.key===' ')playing?stop():play();else if(e.key==='Escape')stop();else if(['Home','End','ArrowRight','ArrowLeft'].includes(e.key)){stop();index=e.key==='Home'?0:e.key==='End'?trial.frames.length-1:Math.max(0,Math.min(trial.frames.length-1,index+(e.key==='ArrowRight'?1:-1)*(e.shiftKey?25:1)));render()}};
new IntersectionObserver(entries=>{visible=entries.at(-1).isIntersecting;if(visible&&playing&&!frameId){last=0;frameId=requestAnimationFrame(tick)}}).observe(stage);
document.addEventListener('visibilitychange',()=>{if(document.hidden){if(frameId)cancelAnimationFrame(frameId);frameId=0}else if(playing&&visible){last=0;frameId=requestAnimationFrame(tick)}});
reduced.addEventListener('change',()=>{if(reduced.matches)stop()});
detail(...topics.machine);render();
})();
