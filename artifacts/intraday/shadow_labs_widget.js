(()=>{
const M=window.RESEARCH_META||{},H=M.h09_live||{},D=M.h09_put_flow||{},L=M.multisymbol_live||{},MD=M.multisymbol_discovery||{};
const root=document.querySelector('.w');if(!root)return;
const hsig=H.signals||[],msig=L.signals||[];
const esc=x=>String(x??'--').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const panel=document.createElement('details');panel.className='panel';panel.open=false;
panel.innerHTML=`<summary><b>Shadow Labs · H09 + Multi-Symbol</b> · sin órdenes broker</summary>
<div class="explain"><b>Separación científica:</b> discovery hasta 2026-10-14; desde 2026-10-15 las señales nuevas cuentan como observaciones prospectivas. Estos motores no envían órdenes a Alpaca.</div>
<div class="cards"><div class="card"><div class="lab">H09 señales live</div><div class="val">${esc(hsig.length)}</div><div class="hint">H09A / H09B PUT</div></div><div class="card"><div class="lab">Multi señales live</div><div class="val">${esc(msig.length)}</div><div class="hint">9 símbolos</div></div><div class="card"><div class="lab">H09 discovery</div><div class="val">${esc(D.discovery?.episodes)}</div><div class="hint">no validación</div></div><div class="card"><div class="lab">Multi discovery</div><div class="val">${esc(MD.discovery?.episodes)}</div><div class="hint">familias preespecificadas</div></div></div>
<div class="grid"><div class="panel"><h2>Últimas H09</h2><div class="compare" id="h09shadowrows"></div></div><div class="panel"><h2>Últimas Multi-Symbol</h2><div class="compare" id="multishadowrows"></div></div></div>`;
const anchor=document.getElementById('view-status');(anchor||root.firstChild).after(panel);
const table=(rows,multi)=>rows.length?'<table><thead><tr><th>Hora</th><th>Candidato</th>'+(multi?'<th>Símbolo</th>':'')+'<th>Lado</th><th>Contrato</th></tr></thead><tbody>'+rows.slice(-10).reverse().map(r=>'<tr><td>'+esc((r.signal_time||'').slice(11,19))+'</td><td>'+esc(r.candidate_id)+'</td>'+(multi?'<td>'+esc(r.symbol)+'</td>':'')+'<td>'+esc(r.side)+'</td><td>'+esc(r.contract)+'</td></tr>').join('')+'</tbody></table>':'<div class="sub" style="padding:12px 0">Sin señales prospectivas todavía.</div>';
panel.querySelector('#h09shadowrows').innerHTML=table(hsig,false);panel.querySelector('#multishadowrows').innerHTML=table(msig,true);
})();
