(function(){
const ny=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const parts=Object.fromEntries(ny.formatToParts(new Date()).map(p=>[p.type,p.value]));
const today=`${parts.year}-${parts.month}-${parts.day}`;
const params=new URLSearchParams(location.search),historical=params.get('mode')==='history';
const day=historical&&/^\d{4}-\d{2}-\d{2}$/.test(params.get('day')||'')?params.get('day'):today;
window.DASHBOARD_VIEW={mode:historical?'history':'today',day,today};
const header=document.querySelector('header'),controls=document.createElement('div');
controls.style.cssText='display:flex;gap:8px;flex-wrap:wrap;align-items:center';
controls.innerHTML='<label>Modo <select id="view-mode"><option value="today">Hoy</option><option value="history">Histórico</option></select></label><label id="history-picker">Sesión <select id="history-date"></select></label>';
header.appendChild(controls);document.getElementById('date').style.display='none';
const status=document.createElement('p');status.id='view-status';status.className='sub';status.setAttribute('role','status');header.after(status);
status.textContent='Cargando sesión '+day+'…';
document.getElementById('view-mode').value=window.DASHBOARD_VIEW.mode;
document.getElementById('history-picker').hidden=!historical;
const navigate=(mode,date)=>{const url=new URL(location.href);url.search='';if(mode==='history'){url.searchParams.set('mode','history');url.searchParams.set('day',date)}location.assign(url.href)};
document.getElementById('view-mode').onchange=e=>navigate(e.target.value,day);
document.getElementById('history-date').onchange=e=>navigate('history',e.target.value);
async function get(path){const r=await fetch(path,{cache:'no-store',signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
window.DASHBOARD_READY=(async()=>{
 try{
  const index=await get('sessions/index.json');window.DASHBOARD_INDEX=index;
  const select=document.getElementById('history-date');
  [...index.sessions].reverse().forEach(s=>{const o=document.createElement('option');o.value=s.day;o.textContent=s.day+' · '+s.rows+' registros';select.appendChild(o)});select.value=day;
  if(!index.sessions.some(s=>s.day===day)){
   window.DASHBOARD_DATA=[];window.RESEARCH_META={};status.textContent='Todavía no hay una sesión preparada para '+day+'.';return;
  }
  const [data,meta]=await Promise.all([get('sessions/'+day+'.json'),get('sessions/'+day+'.meta.json')]);
  if(historical)Object.assign(meta,await get('sessions/analysis.json'));
  window.DASHBOARD_DATA=data;window.RESEARCH_META=meta;
  const latest=data.reduce((v,r)=>r.captured_at_utc>v?r.captured_at_utc:v,'');
  status.textContent=(historical?'Histórico':'Hoy')+' · sesión '+day+' (Nueva York) · '+data.length+' registros · última captura '+(latest||'sin capturas')+'. Los saldos de cuenta muestran el estado al publicar; los análisis acumulados son los del último postcierre.';
  if(historical){
   const panel=document.createElement('details');panel.className='panel';const summary=document.createElement('summary');summary.textContent='Todas las sesiones preparadas';panel.appendChild(summary);
   const list=document.createElement('div');list.className='compare';const table=document.createElement('table');
   table.innerHTML='<thead><tr><th>Sesión</th><th>Registros</th><th>Símbolos</th><th>Última captura</th></tr></thead>';
   const body=document.createElement('tbody');[...index.sessions].reverse().forEach(s=>{const tr=document.createElement('tr');tr.tabIndex=0;[s.day,s.rows,s.symbols.join(', '),s.latest_capture||'Sin capturas'].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.appendChild(td)});tr.onclick=()=>navigate('history',s.day);tr.onkeydown=e=>{if(e.key==='Enter')navigate('history',s.day)};body.appendChild(tr)});table.appendChild(body);list.appendChild(table);panel.appendChild(list);status.after(panel);
  }
 }catch(error){window.DASHBOARD_DATA=[];window.RESEARCH_META={};status.textContent='No se pudo cargar la sesión: '+error.message;status.style.color='#ff8794'}
})();
window.loadDashboardScript=src=>new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(Error('No se pudo cargar '+src));document.body.appendChild(s)});
if(!historical)setInterval(async()=>{try{const next=await get('sessions/index.json');if(next.today!==today||next.generated_at_utc!==window.DASHBOARD_INDEX?.generated_at_utc)location.reload()}catch(e){status.textContent='No se pudo comprobar la actualización: '+e.message}},60000);
})();
