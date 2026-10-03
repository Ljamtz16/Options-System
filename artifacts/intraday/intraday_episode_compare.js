(function(){
 function pc(x){return x==null||x===''?'—':(100*(+x)).toFixed(2)+'%'}
 function tm(x){return new Date(x).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}
 function episodes(r){let o=[],c=null;r.forEach((x,i)=>{if(x.h03){if(!c||i>c.last+1){c={last:i,rows:[x]};o.push(c)}else{c.last=i;c.rows.push(x)}}else c=null});return o}
 window.EP_COMPARE_SELECTED=new Set();
 window.refreshEpisodeComparison=function(){
  const root=document.getElementById('compare'),sel=document.getElementById('date');if(!root||!sel)return;
  const all=episodes((window.DASHBOARD_DATA||[]).filter(x=>x.decision_date===sel.value));
  let ids=[...window.EP_COMPARE_SELECTED].filter(i=>i<all.length);
  if(!ids.length){root.innerHTML='<div class="sub">Selecciona al menos un episodio con la casilla “Comparar”.</div>';return}
  const e=ids.map(i=>({z:all[i],id:i}));
  const row=(name,fn)=>'<tr><th>'+name+'</th>'+e.map(q=>'<td>'+fn(q.z,q.z.rows[0],q.id)+'</td>').join('')+'</tr>';
  let h='<table class="cmp"><thead><tr><th>Métrica</th>'+e.map(q=>'<th>E'+(q.id+1)+'<br><span class="hint">'+tm(q.z.rows[0].captured_at_utc)+'</span></th>').join('')+'</tr></thead><tbody>';
  h+=row('Duración',z=>Math.max(5,z.rows.length*5)+' min');h+=row('Snapshots',z=>z.rows.length);
  h+=row('Retorno 60m',(z,x)=>pc(x.call_ret_60m));h+=row('MFE · mejor a favor',(z,x)=>'<span class="good">'+pc(x.call_mfe_60m)+'</span>');
  h+=row('MAE · peor en contra',(z,x)=>'<span class="bad">'+pc(x.call_mae_60m)+'</span>');h+=row('TP10 / SL10',(z,x)=>x.call_60m_tp10_sl10||'—');
  h+=row('SPY al inicio',(z,x)=>pc(x.spy_from_open));h+=row('IWM al inicio',(z,x)=>pc(x.iwm_from_open));h+=row('Contrato CALL',(z,x)=>x.call_contract||'—');
  root.innerHTML=h+'</tbody></table>';
 }
 window.toggleEpisodeCompare=function(i,on){if(on)window.EP_COMPARE_SELECTED.add(i);else window.EP_COMPARE_SELECTED.delete(i);window.refreshEpisodeComparison();document.querySelectorAll('.ep').forEach((x,j)=>x.classList.toggle('active',window.EP_COMPARE_SELECTED.has(j)))}
 window.selectAllEpisodes=function(on){document.querySelectorAll('.epcheck').forEach((x,i)=>{x.checked=on;if(on)window.EP_COMPARE_SELECTED.add(i);else window.EP_COMPARE_SELECTED.delete(i)});window.refreshEpisodeComparison();document.querySelectorAll('.ep').forEach(x=>x.classList.toggle('active',on))}
 window.resetEpisodeCompare=function(){window.EP_COMPARE_SELECTED.clear();setTimeout(()=>window.refreshEpisodeComparison(),0)}
 setTimeout(()=>{window.refreshEpisodeComparison();const s=document.getElementById('date');if(s)s.addEventListener('change',window.resetEpisodeCompare)},0);
})();