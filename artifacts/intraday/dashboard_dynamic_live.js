(function(){
const KEY_TAB='optionsDashboardTab',KEY_DATE='optionsDashboardDate',KEY_SYMBOL='optionsDashboardSymbol';
const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];
function etNow(){
 const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23',weekday:'short'}).formatToParts(new Date()).filter(x=>x.type!=='literal').map(x=>[x.type,x.value]));
 return {date:p.year+'-'+p.month+'-'+p.day,hour:+p.hour,minute:+p.minute,weekday:p.weekday};
}
function phase(date){
 const x=etNow(); if(date!==x.date)return 'HISTORICAL'; if(['Sat','Sun'].includes(x.weekday))return 'CLOSED';
 const m=x.hour*60+x.minute; if(m<570)return 'PREMARKET'; if(m<960)return 'LIVE'; return 'POST-CLOSE';
}
function selectedDate(){return q('#date')?.value||etNow().date}
function selectedSymbol(){return q('#symbol')?.value||'SPY'}
function kind(date){const r=(window.DASHBOARD_DATA||[]).find(x=>x.decision_date===date);return r?.session_kind||(date===(window.RESEARCH_META||{}).discovery_session?'DISCOVERY':'PROSPECTIVE')}
function updateBanner(){
 const b=q('#dynamic-session-banner')||q('.research-banner'); if(!b)return;
 b.id='dynamic-session-banner'; const d=selectedDate(),s=selectedSymbol(),k=kind(d),p=phase(d);
 if(k==='DISCOVERY') b.innerHTML='<b>DISCOVERY · '+d+' · '+s+'</b> — Sesión diagnóstica; no cuenta como evidencia prospectiva. Las reglas congeladas no se modifican.';
 else if(p==='HISTORICAL') b.innerHTML='<b>PROSPECTIVE · '+d+' · '+s+'</b> — Sesión prospectiva histórica. Resultados preservados sin reajustar reglas.';
 else b.innerHTML='<b>'+p+' · '+d+' · '+s+'</b> — Sesión prospectiva actual. Paper Trading es simulación y permanece separado de la evidencia científica.';
}
function renameReadiness(){qa('[data-tab="health"]').forEach(x=>x.textContent='System Readiness'); const p=q('[data-tabgroup="health"] h2'); if(p)p.textContent='System Readiness'}
function restoreTab(){
 const wanted=sessionStorage.getItem(KEY_TAB); if(!wanted)return;
 const b=q('.tabs button[data-tab="'+wanted+'"]'); if(b&&!b.classList.contains('active'))b.click();
}
function persistTab(){qa('.tabs button[data-tab]').forEach(b=>b.addEventListener('click',()=>sessionStorage.setItem(KEY_TAB,b.dataset.tab)))}
function restoreSelectors(){
 const d=q('#date'),s=q('#symbol'),sd=sessionStorage.getItem(KEY_DATE),ss=sessionStorage.getItem(KEY_SYMBOL);
 if(d&&sd&&[...d.options].some(o=>o.value===sd)){d.value=sd;d.dispatchEvent(new Event('change'))}
 if(s&&ss&&[...s.options].some(o=>o.value===ss)){s.value=ss;s.dispatchEvent(new Event('change'))}
 d?.addEventListener('change',()=>{sessionStorage.setItem(KEY_DATE,d.value);setTimeout(updateBanner,0)});
 s?.addEventListener('change',()=>{sessionStorage.setItem(KEY_SYMBOL,s.value);setTimeout(updateBanner,0)});
}
function fixCadenceText(){
 const d=selectedDate(),s=selectedSymbol(),k=kind(d); const cards=qa('#cards .card');
 const c=cards.find(x=>x.querySelector('.lab')?.textContent.trim()==='Snapshots observados'); if(!c)return;
 const h=c.querySelector('.hint'); if(!h)return;
 h.textContent=k==='DISCOVERY'?'cadencia histórica ~5 min':(['SPY','QQQ','IWM'].includes(s)?'collector v2 · ~1 min':'collector v2 · ~2 min');
}
function tick(){updateBanner();fixCadenceText()}
function init(){renameReadiness();persistTab();restoreTab();restoreSelectors();tick();
 setInterval(()=>{const active=q('.tabs button.active')?.dataset.tab;if(active==='paper')location.reload();else tick()},15000);
 document.addEventListener('change',e=>{if(e.target?.id==='date'||e.target?.id==='symbol')setTimeout(tick,0)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,50));else setTimeout(init,50);
})();
