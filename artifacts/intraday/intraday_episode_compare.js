(function(){
 function pc(x){return x==null||x===''?'—':(100*(+x)).toFixed(2)+'%'}
 function usd(x){return x==null||x===''?'—':'$'+Number(x).toFixed(2)}
 function tm(x){return new Date(x).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}
 function episodes(r){let o=[],c=null;r.forEach((x,i)=>{if(x.h03){if(!c||i>c.last+1){c={last:i,rows:[x]};o.push(c)}else{c.last=i;c.rows.push(x)}}else c=null});return o}
 function trade(x){let a=+x.call_entry_ask,r=+x.call_60m_tp10_sl10_exit_return;if(!a||!Number.isFinite(r))return null;let ep=a*(1+r),gross=(ep-a)*100;let fee=.015*2+.025*2+.000003*100*2+.00329+.0000206*ep*100;return{entry:a,exit:ep,capital:a*100,gross,fee,net:gross-fee}}
 function ceilCent(x){return Math.ceil((x-1e-12)*100)/100}
 function dailyFees(ts){let n=ts.length,sell=ts.reduce((a,t)=>a+t.exit*100,0);let c={ORF:ceilCent(.015*n*2),OCC:ceilCent(.025*n*2),CAT:ceilCent(.000003*100*n*2),TAF:ceilCent(.00329*n),SEC:ceilCent(.0000206*sell)};return{c,total:Object.values(c).reduce((a,b)=>a+b,0)}}
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
  h+=row('Capital · 1 contrato',(z,x)=>usd(trade(x)?.capital));h+=row('Entrada · ask',(z,x)=>usd(+x.call_entry_ask));
  h+=row('Salida primer TP/SL · bid',(z,x)=>usd(trade(x)?.exit));h+=row('P&L bruto · 1 contrato',(z,x)=>usd(trade(x)?.gross));
  h+=row('Retorno al primer TP/SL',(z,x)=>pc(x.call_60m_tp10_sl10_exit_return));
  h+=row('Retorno 60m',(z,x)=>pc(x.call_ret_60m));h+=row('MFE · mejor a favor',(z,x)=>'<span class="good">'+pc(x.call_mfe_60m)+'</span>');
  h+=row('MAE · peor en contra',(z,x)=>'<span class="bad">'+pc(x.call_mae_60m)+'</span>');h+=row('TP10 / SL10',(z,x)=>x.call_60m_tp10_sl10||'—');
  h+=row('SPY al inicio',(z,x)=>pc(x.spy_from_open));h+=row('IWM al inicio',(z,x)=>pc(x.iwm_from_open));h+=row('Contrato CALL',(z,x)=>x.call_contract||'—');
  const ts=e.map(q=>trade(q.z.rows[0])).filter(Boolean),gross=ts.reduce((a,t)=>a+t.gross,0),fees=dailyFees(ts);
  h+='</tbody></table><div class="explain" style="margin-top:14px"><b>Dinero · selección actual:</b> P&L bruto '+usd(gross)+' · fees regulatorios Alpaca estimados '+usd(fees.total)+' · <b>neto observable '+usd(gross-fees.total)+'</b>.<br><span class="hint">El spread ya está incluido: compra al ask y salida al bid. Stress adicional: 1¢ peor por lado = '+usd(gross-fees.total-2*ts.length)+'; 2¢ peor por lado = '+usd(gross-fees.total-4*ts.length)+'. Fees: ORF '+usd(fees.c.ORF)+', OCC '+usd(fees.c.OCC)+', CAT '+usd(fees.c.CAT)+', TAF '+usd(fees.c.TAF)+', SEC '+usd(fees.c.SEC)+'.</span></div>';
  root.innerHTML=h;
 }
 window.toggleEpisodeCompare=function(i,on){if(on)window.EP_COMPARE_SELECTED.add(i);else window.EP_COMPARE_SELECTED.delete(i);window.refreshEpisodeComparison();document.querySelectorAll('.ep').forEach((x,j)=>x.classList.toggle('active',window.EP_COMPARE_SELECTED.has(j)))}
 window.selectAllEpisodes=function(on){document.querySelectorAll('.epcheck').forEach((x,i)=>{x.checked=on;if(on)window.EP_COMPARE_SELECTED.add(i);else window.EP_COMPARE_SELECTED.delete(i)});window.refreshEpisodeComparison();document.querySelectorAll('.ep').forEach(x=>x.classList.toggle('active',on))}
 window.resetEpisodeCompare=function(){window.EP_COMPARE_SELECTED.clear();setTimeout(()=>window.refreshEpisodeComparison(),0)}
 setTimeout(()=>{window.refreshEpisodeComparison();const s=document.getElementById('date');if(s)s.addEventListener('change',window.resetEpisodeCompare)},0);
})();