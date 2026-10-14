(function(){
window.DASHBOARD_READY.then(()=>{
 const M=window.RESEARCH_META||{},C=M.collector_coverage||{},day=window.DASHBOARD_VIEW?.day;
 const d=(C.days||{})[day]||{};
 const cards=document.getElementById('healthcards');
 if(!cards)return;
 const pct=d.coverage_rate==null?'--':(100*Number(d.coverage_rate)).toFixed(2)+'%';
 const extra=[
  ['Cobertura collector',pct,(d.successes??0)+'/'+(d.attempts??0)+' capturas'],
  ['Huecos con PUT armado',d.armed_failures??0,'fallos de captura durante estado ARMED']
 ];
 extra.forEach(([label,value,hint])=>{
  const el=document.createElement('div');el.className='card';
  el.innerHTML='<span>'+label+'</span><b>'+value+'</b><div class="hint">'+hint+'</div>';
  cards.appendChild(el);
 });
 const status=document.getElementById('view-status');
 if(status&&d.failures>0)status.textContent+=' · Cobertura collector '+pct+' ('+d.failures+' huecos).';
});
})();
