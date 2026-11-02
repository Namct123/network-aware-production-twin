'use strict';
const el=id=>document.getElementById(id);
const statusText={planned:'Chưa triển khai',implemented:'Đã viết và ghép; xem kết quả kiểm tra riêng',implemented_unvalidated:'Đã viết, chưa chạy kiểm tra',checked:'Đã kiểm tra theo phạm vi ghi nhận',external_pending:'Cần dữ liệu hoặc thao tác ngoài máy tính'};
const stateText={HOLD:'Dừng chờ',DONE:'Hoàn tất',COMPLETE:'Hoàn tất',RUNNING:'Đang chạy mô phỏng',BLOCKED:'Bị chặn',OPERATOR_REVIEW:'Chờ người kiểm tra xem xét'};
function reasonVi(r){if(!r)return 'Không có lý do dừng';if(r.startsWith('timeout:'))return 'Chờ tín hiệu hoặc thao tác quá lâu: '+r;if(r.startsWith('invalid_or_stale'))return 'Tín hiệu thiếu hoặc quá cũ: '+r;if(r==='prediction_deadline_exceeded')return 'Tính dự báo không xong trong thời gian cho phép';if(r==='unconfirmed_xy_a2_midstroke_and_vacuum')return 'Chưa xác nhận đủ vị trí trục và chân không';return 'Mã lý do trong nhật ký: '+r;}
function cell(row,text){const td=document.createElement('td');td.textContent=String(text??'—');row.append(td);}
function show(data){
 el('modules').replaceChildren();
 for(const item of data.implementation?.items||[]){const box=document.createElement('article');box.className='card';const h=document.createElement('h3');h.textContent=`${item.id} · ${item.title_vi}`;const p=document.createElement('p');p.textContent=statusText[item.status]||item.status;const d=document.createElement('p');d.className='small muted';d.textContent=item.purpose_vi||'';box.append(h,p,d);el('modules').append(box);}
 el('runs').replaceChildren();
 for(const r of data.runs||[]){const tr=document.createElement('tr');cell(tr,r.name);cell(tr,r.state_vi||stateText[r.state]||r.state);cell(tr,Number.isFinite(r.simulation_time_s)?r.simulation_time_s.toFixed(3)+' giây':null);cell(tr,r.placement_pass===true?'Đạt':r.placement_pass===false?'Chưa đạt':'Không chấm đặt phôi');cell(tr,r.message_guard?.rejected);cell(tr,r.session?`${r.session.session_id.slice(0,8)} / ${r.session.generation}`:null);cell(tr,reasonVi(r.reason));el('runs').append(tr);}
 if(data.journal)el('journal').textContent=data.journal;
 el('timing').replaceChildren();
 const q=data.qualifications?.[0];
 el('qualification-note').textContent=q?`${q.completed_runs}/${q.planned_runs} lượt đối chứng; vi phạm tiêu chí: ${q.verification_failures}. Chưa kiểm chứng máy thật.`:'Chưa có bản đánh giá mới.';
 for(const g of q?.benchmark_groups||[]){const tr=document.createElement('tr');cell(tr,g.backend==='numeric_1d'?'Tính 1 chiều':'MuJoCo băng/phôi');cell(tr,g.budget_kind==='configured'?'Đang cấu hình':'Chức năng');cell(tr,g.samples);for(const k of ['median_ms','p95_ms','max_ms'])cell(tr,Number.isFinite(g[k])?g[k].toFixed(3):null);cell(tr,g.deadline_misses);cell(tr,g.complete);el('timing').append(tr);}
}
async function refresh(){try{const r=await fetch('/api/project-state',{cache:'no-store'});if(!r.ok)throw Error('Chưa có bộ đọc nhật ký');const data=await r.json();show(data);el('connection').textContent='Đã đọc nhật ký trên máy này. Trang không gửi lệnh tới máy.';}catch(e){el('connection').textContent='Chưa kết nối bộ đọc. Bạn có thể chọn tệp đã lưu để xem; đây không phải lỗi máy.';}}
el('refresh').addEventListener('click',refresh);
el('files').addEventListener('change',async event=>{
 const data={implementation:{items:[]},runs:[],journal:''};const details=[];
 for(const file of event.target.files){if(file.size>4*1024*1024){details.push(file.name+': tệp quá lớn, giới hạn 4 MB.');continue;}
 try{const text=await file.text();if(file.name.endsWith('.md')){data.journal+=text+'\n';continue;}
 const obj=JSON.parse(text);details.push(file.name+'\n'+JSON.stringify(obj,null,2));
 if(Array.isArray(obj.items))data.implementation=obj;
 if(obj.kind==='qualification_v1')data.qualifications=[obj];
 if(obj.controller_state)data.runs.push({name:file.name,state:obj.controller_state,simulation_time_s:obj.simulation_time_s,placement_pass:obj.placement_pass_evaluator_only,message_guard:obj.message_guard,reason:obj.hold_reason});
 }catch(e){details.push(file.name+': không đọc được định dạng dữ liệu.');}}
 show(data);el('detail').textContent=details.join('\n\n');
});
refresh();
