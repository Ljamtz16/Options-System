(function(){
const A=window.DASHBOARD_DATA||[];
const $=x=>document.getElementById(x);
if(!A.length||!$('date'))return;

const header=$('date').parentElement;
let symbol=$('symbol');
if(!symbol){
  symbol=document.createElement('select');
  symbol.id='symbol';
  const label=document.createElement('span');
  label.className='hint';
  label.textContent=' Simbolo ';
  header.appendChild(label);
  header.appendChild(symbol);
}

const symbols=[...new Set(A.map(x=>x.symbol||'SPY'))].sort();
const dates=[...new Set(A.map(x=>x.decision_date).filter(Boolean))].sort();
const pc2=x=>x==null||x===''?'--':(100*(+x)).toFixed(2)+'%';

$('date').innerHTML=dates.map(d=>{
  const kind=A.find(x=>x.decision_date===d)?.session_kind||(d==='2026-10-02'?'DISCOVERY':'PROSPECTIVE');
  return '<option value="'+d+'">'+d+' — '+kind+'</option>';
}).join('');

symbol.innerHTML=symbols.map(s=>'<option value="'+s+'">'+s+'</option>').join('');

function detailMulti(r){
  const isSpy=r.symbol==='SPY';
  const q=[
    ['Hora',tm(r.captured_at_utc)],['Simbolo',r.symbol],['Precio',r.spot],
    [r.symbol+' from open',pc2(r.symbol_from_open)],['SPY contexto',pc2(r.spy_from_open)],
    ['IWM contexto',pc2(r.iwm_from_open)],['QQQ contexto',pc2(r.qqq_from_open)],
    ['VIX',r.vix_current],['ATM IV',pc2(r.atm_iv)],['IV skew',r.put_call_iv_skew],
    ['Put/Call volume',r.put_call_volume_ratio_1pct],
    ['H03',isSpy?(r.h03?'YES':'No'):'N/A - SPY ONLY'],
    ['CALL',r.call_contract],['CALL ASK',r.call_entry_ask],
    ['CALL 5m',pc2(r.call_ret_5m)],['CALL 15m',pc2(r.call_ret_15m)],
    ['CALL 30m',pc2(r.call_ret_30m)],['CALL 60m',pc2(r.call_ret_60m)],
    ['CALL EOD',pc2(r.call_ret_eod)],['CALL MFE 60m',pc2(r.call_mfe_60m)],
    ['CALL MAE 60m',pc2(r.call_mae_60m)],['CALL TP10 / SL10 60m',r.call_60m_tp10_sl10],
    ['PUT',r.put_contract],['PUT ASK',r.put_entry_ask],
    ['PUT 5m',pc2(r.put_ret_5m)],['PUT 15m',pc2(r.put_ret_15m)],
    ['PUT 30m',pc2(r.put_ret_30m)],['PUT 60m',pc2(r.put_ret_60m)],
    ['PUT EOD',pc2(r.put_ret_eod)],['PUT TP10 / SL10 15m',r.put_15m_tp10_sl10]
  ];
  $('detail').innerHTML=q.map(x=>'<tr><th>'+x[0]+'</th><td>'+(x[1]??'--')+'</td></tr>').join('');
}

function renderMulti(){
  const d=$('date').value,sym=symbol.value;
  const r=A.filter(x=>x.decision_date===d&&(x.symbol||'SPY')===sym);
  const isSpy=sym==='SPY',e=isSpy?eps(r):[],act=isSpy?r.filter(x=>x.h03):[];
  const kind=r[0]?.session_kind||(d==='2026-10-02'?'DISCOVERY':'PROSPECTIVE');
  const cards=[
    ['Snapshots observados',r.length,'una lectura cada ~5 min'],
    ['Simbolo',sym,'activo seleccionado'],
    ['Activaciones H03',isSpy?act.length:'N/A',isSpy?'regla congelada SPY':'H03 es SPY-only'],
    ['Episodios H03',isSpy?e.length:'N/A',isSpy?'rachas independientes agrupadas':'no aplica'],
    ['Sesion',d,kind]
  ];
  $('cards').innerHTML=cards.map(x=>'<div class="card"><div class="lab">'+x[0]+'</div><div class="val">'+x[1]+'</div><div class="hint">'+x[2]+'</div></div>').join('');
  chart($('market'),r,['symbol_from_open','iwm_from_open'],['#62a8ff','#57d6d0']);
  chart($('opts'),r,['atm_iv','put_call_iv_skew','put_call_volume_ratio_1pct'],['#ad8cff','#ffbd59','#57d6d0']);
  $('ticks').innerHTML=r.map(x=>'<div class="tick '+(isSpy&&x.h03?'on':'')+'" title="'+tm(x.captured_at_utc)+'"></div>').join('');
  window.R=r;
  $('eps').innerHTML=!isSpy
    ?'<div class="sub" style="padding:16px 0">H03 no aplica a '+sym+'. La hipotesis congelada es SPY-only.</div>'
    :e.length?e.map((z,i)=>'<div class="ep" onclick="detail(R['+z.start+'])"><div class="eph"><span>Episodio '+(i+1)+'</span><span class="pill">'+z.rows.length+' snapshots</span></div><div class="hint">'+tm(z.rows[0].captured_at_utc)+' -> '+tm(z.rows.at(-1).captured_at_utc)+'</div></div>').join('')
    :'<div class="sub" style="padding:16px 0">No hay episodios H03 en esta sesion.</div>';
  window.detail=detailMulti;
  if(r.length)detailMulti(r[0]);
}

function syncSymbols(){
  const available=[...new Set(A.filter(x=>x.decision_date===$('date').value).map(x=>x.symbol||'SPY'))].sort();
  const previous=symbol.value;
  symbol.innerHTML=available.map(s=>'<option value="'+s+'">'+s+'</option>').join('');
  symbol.value=available.includes(previous)?previous:(available.includes('SPY')?'SPY':available[0]);
  renderMulti();
}

$('date').onchange=syncSymbols;
symbol.onchange=renderMulti;
$('date').value=dates.at(-1);
syncSymbols();
})();