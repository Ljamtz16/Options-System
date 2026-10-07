(function(){
const M=window.RESEARCH_META||{},V=M.prospective_validation||{},S=M.sizing_simulation||{},T=M.stress_testing||{},G=M.risk_gate||{},X=M.execution_gate||{},H=M.readiness||{},P=M.paper_trading||{},PC=M.paper_control||{},PR=M.paper_risk_comparison||{},root=document.querySelector('.w');if(!root)return;
const esc=x=>String(x??'--').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pct=x=>x==null?'--':(100*(+x)).toFixed(1)+'%';
const money=x=>x==null?'--':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(+x);
const ruleText=r=>r.feature?esc(r.feature)+' '+esc(r.op)+' '+esc(r.value):Object.entries(r).map(([k,v])=>esc(k)+' = '+esc(v)).join('<br>');
const header=root.querySelector('header'),cards=root.querySelector('#cards'),grid=root.querySelector('.grid'),compare=document.querySelector('#compare')?.closest('.panel'),foot=root.querySelector('.foot');
const tabs=document.createElement('div');tabs.className='tabs';tabs.innerHTML='<button data-tab="session" class="active">Sesion intradia</button><button data-tab="episodes">Episodios</button><button data-tab="hyp">Hipotesis</button><button data-tab="pros">Validacion prospectiva</button><button data-tab="exec">Execution Gate</button><button data-tab="paper">LIVE_PAPER · local</button><button data-tab="controls">Análisis P2–P3</button><button data-tab="health">Readiness</button><button data-tab="lab">Discovery Lab</button>';
root.insertBefore(tabs,root.children[1]);
const banner=document.createElement('div');banner.className='research-banner';banner.innerHTML='<b>Sesion de descubrimiento: '+esc(M.discovery_session)+'</b> - Los resultados de esta fecha son diagnosticos y no cuentan como evidencia prospectiva. H03 esta congelada desde el cierre de esta sesion.';root.insertBefore(banner,tabs.nextSibling);
const session=[header,cards,grid].filter(Boolean);session.forEach(x=>x.dataset.tabgroup='session');
const make=(id,html)=>{let d=document.createElement('div');d.className='tabpage';d.dataset.tabgroup=id;d.innerHTML=html;root.appendChild(d);return d};
const episodes=make('episodes','');const aside=grid?.querySelector('aside');if(aside)episodes.appendChild(aside);if(compare)episodes.appendChild(compare);if(foot)episodes.appendChild(foot);if(grid)grid.style.gridTemplateColumns='1fr';
make('hyp','<div class="panel"><h2>Hipotesis y candidatos</h2><div class="explain"><b>Separacion metodologica:</b> H01, H02 y H03 estan congeladas para evaluacion prospectiva. H04/H05 y nuevas ideas permanecen exclusivamente en Discovery Lab hasta un freeze explicito.</div><div class="hypgrid" id="hypgrid"></div></div>');
make('pros','<div class="panel"><h2>Validacion prospectiva</h2><div class="explain"><b>Regla:</b> esta pestana excluye automaticamente 2026-10-02 y fechas anteriores. La cuenta virtual parte de $1,000 y H03 usa maximo un contrato por episodio, entrada ASK y salida BID segun la politica congelada.</div><div class="cards" id="proscards"></div><div id="proscheck" class="panel" style="margin-top:12px"></div><div class="panel" style="margin-top:12px"><h2>Operaciones prospectivas por episodio</h2><div class="compare" id="prostrades"></div></div><div class="panel" style="margin-top:12px"><h2>Sizing simulation - not part of frozen hypothesis evidence</h2><div class="explain"><b>Uso:</b> simulacion de ejecucion y riesgo. No cambia H03 ni cuenta como evidencia de efectividad.</div><div class="compare" id="sizingtable"></div></div><div class="panel" style="margin-top:12px"><h2>Risk gate</h2><div class="explain"><b>Estado:</b> <span id="gatestatus"></span> &nbsp; <b>Maximo permitido:</b> <span id="gatefraction"></span> &nbsp; <b>Estrategia:</b> <span id="gatestrategy"></span><br>El gate usa evidencia prospectiva y stress testing; el historico diagnostico no desbloquea sizing.</div><div class="sub" style="margin-top:8px">Execution gate: PASS <b>'+esc((X.counts||{}).PASS||0)+'</b> | BLOCK <b>'+esc((X.counts||{}).BLOCK||0)+'</b> | REVIEW <b>'+esc((X.counts||{}).REVIEW_MISSING_MARKET_QUALITY||0)+'</b></div></div><div class="panel" style="margin-top:12px"><h2>Stress testing - execution risk only</h2><div class="explain"><b>Uso:</b> escenarios deterministas adversos. No estiman la probabilidad de que ocurran y no son evidencia de H03.</div><div class="compare" id="stresstable"></div></div></div>');
make('exec','<div class="panel"><h2>Execution Gate</h2><div class="explain"><b>Objetivo:</b> separar una senal H03 valida de un contrato realmente operable. El filtro considera el risk gate, presupuesto, precio, spread y tamanos bid/ask. Un BLOCK no invalida H03; significa que esa ejecucion concreta no cumple la politica.</div><div class="cards" id="execcards"></div><div class="panel" style="margin-top:12px"><h2>Politica de ejecucion</h2><div class="compare" id="execpolicy"></div></div><div class="panel" style="margin-top:12px"><h2>Decision por episodio</h2><div class="compare" id="exectable"></div></div></div>');
make('paper',`
<div class="panel">
  <h2>LIVE_PAPER · cuenta virtual local</h2>

  <div class="explain">
    <b>Cuenta local de Options-System; sin órdenes de Alpaca.</b>
    Entrada al ASK, seguimiento y salida al BID.
    El límite seleccionado aquí NO modifica el Risk Gate científico.
  </div>

  <div class="explain">Jev y Comparator simulan oportunidades por snapshot. Alpaca Paper mantiene una cuenta separada con fills del broker. Sus P&amp;L no se suman a este saldo.</div>
  <div class="cards" id="papercards"></div>

  <div class="panel" style="margin-top:12px">
    <h2>Capital allocation limit</h2>
    <div class="explain">
      Scientific Risk Gate:
      <b id="paperScientificGate"></b>
      &nbsp;|&nbsp;
      Paper Trading Limit:
      <b id="paperCurrentRisk"></b>
    </div>

    <div id="paperRiskButtons" class="actions">
      <button data-risk="0">0%</button>
      <button data-risk="0.2">20%</button>
      <button data-risk="0.4">40%</button>
      <button data-risk="0.6">60%</button>
      <button data-risk="0.8">80%</button>
    </div>

    <div id="paperControlStatus" class="hint"></div>
  </div>

  <div class="panel" style="margin-top:12px">
    <h2>Open Positions</h2>
    <div class="compare" id="paperOpen"></div>
  </div>

  <div class="panel" style="margin-top:12px">
    <h2>Live Trades / Signals</h2>
    <div class="compare" id="paperLedger"></div>
  </div>

  <div class="panel" style="margin-top:12px">
    <h2>Causal Replay</h2>
    <div id="paperReplay"></div>
  </div>

  <div class="panel" style="margin-top:12px">
    <h2>Causal Replay — Risk Comparison</h2>

    <div class="explain">
      Mismas señales y capturas observadas.
      El presupuesto puede cambiar el contrato seleccionado y sus resultados; se aplica el mismo límite de un contrato.
      Es una simulación contrafactual y no modifica el Risk Gate científico.
    </div>

    <div class="compare" id="paperRiskComparison"></div>
    <div id="paperRiskDetail" style="margin-top:14px"></div>
  </div>
</div>`);

make('controls','<div class="panel"><h2>P2 · controles de entrada</h2><div id="p2analysis"></div></div><div class="panel"><h2>P3 · diagnóstico Jev</h2><div id="p3analysis"></div></div>');
make('health','<div class="panel"><h2>Readiness</h2><div class="explain"><b>Estado general:</b> <span id="healthstatus"></span> &nbsp; <b>Generado:</b> <span id="healthtime"></span><br>Comprueba outputs persistidos del pipeline. El estado de timers/services de la VPS se verifica por systemd y no se infiere desde el navegador.</div><div class="cards" id="healthcards"></div><div class="compare" id="healthchecks"></div></div>');
make('lab','<div class="panel"><h2>Discovery Lab</h2><div class="explain"><b>Uso:</b> combinaciones retrospectivas para generar hipotesis, no para afirmar rendimiento futuro. Baseline = frecuencia del evento; lift = tasa de la combinacion / baseline.</div><div id="labgrid"></div></div>');
document.getElementById('hypgrid').innerHTML=(M.hypotheses||[]).map(h=>'<div class="hypcard '+h.kind+'"><div class="hyphead"><b>'+esc(h.id)+'</b><span class="side '+h.side.toLowerCase()+'">'+h.side+' - '+h.horizon_min+'m</span></div><div class="state">'+esc(h.status)+'</div><div class="rules">'+(Array.isArray(h.rules)?h.rules.map(ruleText).join('<br>'):ruleText(h.rules))+'</div>'+(h.discovery_episode?'<div class="metricline"><span>Episodios discovery</span><b>'+h.discovery_episode.tp_first+'/'+h.discovery_episode.tp_sl_decided+' TP-first</b></div>':'')+'</div>').join('');
const account=V.virtual_account||{initial_cash:1000,final_cash:1000,net_pnl:0,ledger:[]},ledger=account.ledger||[],episodesV=V.prospective_episodes||[];
const executed=ledger.filter(x=>x.account_status==='EXECUTED'),tp=executed.filter(x=>x.tp_sl==='TP_FIRST').length,sl=executed.filter(x=>x.tp_sl==='SL_FIRST').length;
const days=[...new Set(episodesV.map(x=>x.decision_date).filter(Boolean))].sort(),ret=account.initial_cash?account.net_pnl/account.initial_cash:0;
document.getElementById('proscards').innerHTML=[
 ['Capital inicial',money(account.initial_cash),'baseline congelado'],
 ['Capital actual',money(account.final_cash),'despues de costos'],
 ['P&L acumulado',money(account.net_pnl),pct(ret)+' sobre capital inicial'],
 ['Dias prospectivos',days.length,'sesiones con episodios'],
 ['Episodios',episodesV.length,tp+' TP - '+sl+' SL']
].map(x=>'<div class="card"><div class="lab">'+x[0]+'</div><div class="val">'+x[1]+'</div><div class="hint">'+x[2]+'</div></div>').join('');
const checkpoint=n=>days.length>=n?'<span class="good">OK alcanzado</span>':'<span class="hint">PENDING pendiente</span>';
document.getElementById('proscheck').innerHTML='<h2>Protocolo de validacion</h2><div class="metricline"><span>Day 1</span><b>'+checkpoint(1)+'</b></div><div class="metricline"><span>Day 5 - revision intermedia</span><b>'+checkpoint(5)+'</b></div><div class="metricline"><span>Day 10 - checkpoint principal</span><b>'+checkpoint(10)+'</b></div><div class="hint" style="margin-top:10px">Sin ajuste de umbrales, TP/SL o reglas durante la ventana prospectiva.</div>';
document.getElementById('prostrades').innerHTML=ledger.length?'<table><thead><tr><th>Fecha</th><th>Hora UTC</th><th>Hipotesis</th><th>Side</th><th>Contrato</th><th>ASK</th><th>Resultado</th><th>Estado</th><th>Saldo antes</th><th>P&L trade</th><th>Costos</th><th>Saldo despues</th></tr></thead><tbody>'+ledger.map(x=>'<tr><td>'+esc(x.decision_date)+'</td><td>'+esc((x.start||'').slice(11,16))+'</td><td>'+esc(x.hypothesis)+'</td><td>'+esc((x.side||'').toUpperCase())+'</td><td>'+esc(x.contract)+'</td><td>'+money(x.entry_ask)+'</td><td>'+esc(x.tp_sl)+'</td><td>'+esc(x.account_status)+'</td><td>'+money(x.cash_before_trade)+'</td><td>'+money(x.trade_net_pnl)+'</td><td>'+money(x.trade_fees)+'</td><td>'+money(x.cash_after_trade)+'</td></tr>').join('')+'</tbody></table>':'<div class="sub" style="padding:18px 0">Aun no hay episodios prospectivos. Esto es correcto antes de la primera sesion posterior al freeze.</div>';
const sizing=Object.values(S.strategies||{});
document.getElementById('sizingtable').innerHTML=sizing.length?'<table><thead><tr><th>Estrategia</th><th>Capital final</th><th>P&L</th><th>Retorno</th><th>Max DD</th><th>Trades</th><th>Win rate</th><th>Max contratos</th><th>Max uso capital</th><th>Expectancy</th><th>Racha perdidas</th><th>Riesgo</th></tr></thead><tbody>'+sizing.map(x=>'<tr><td>'+esc(x.strategy)+'</td><td>'+money(x.final_cash)+'</td><td>'+money(x.net_pnl)+'</td><td>'+pct(x.return_pct)+'</td><td>'+pct(x.max_drawdown_pct)+'</td><td>'+esc(x.executed_trades)+'</td><td>'+pct(x.win_rate)+'</td><td>'+esc(x.max_contracts)+'</td><td>'+pct(x.max_capital_utilization_pct)+'</td><td>'+money(x.expectancy_per_trade)+'</td><td>'+esc(x.max_consecutive_losses)+'</td><td>'+esc(x.risk_band)+'</td></tr>').join('')+'</tbody></table>':'<div class="sub" style="padding:18px 0">Sizing pendiente de generar.</div>';
document.getElementById('gatestatus').textContent=G.status||'UNKNOWN';document.getElementById('gatefraction').textContent=pct(G.allowed_max_fraction);document.getElementById('gatestrategy').textContent=G.recommended_strategy||'NO_TRADE';
const stress=Object.entries(T.scenarios||{});
document.getElementById('stresstable').innerHTML=stress.length?'<table><thead><tr><th>Escenario</th><th>1 contrato DD</th><th>20% DD</th><th>40% DD</th><th>60% DD</th><th>80% DD</th><th>80% final</th></tr></thead><tbody>'+stress.map(([name,z])=>'<tr><td>'+esc(name)+'</td><td>'+pct(z.strategies?.fixed_1_contract?.max_drawdown_pct)+'</td><td>'+pct(z.strategies?.pct_20?.max_drawdown_pct)+'</td><td>'+pct(z.strategies?.pct_40?.max_drawdown_pct)+'</td><td>'+pct(z.strategies?.pct_60?.max_drawdown_pct)+'</td><td>'+pct(z.strategies?.pct_80?.max_drawdown_pct)+'</td><td>'+money(z.strategies?.pct_80?.final_cash)+'</td></tr>').join('')+'</tbody></table>':'<div class="sub" style="padding:18px 0">Stress test pendiente de generar.</div>';
const XC=X.counts||{},XE=X.episodes||[],samplePolicy=XE.find(e=>e.execution_gate?.policy)?.execution_gate?.policy||{};
document.getElementById('execcards').innerHTML=[['PASS',XC.PASS||0],['BLOCK',XC.BLOCK||0],['REVIEW',XC.REVIEW_MISSING_MARKET_QUALITY||0],['Risk gate',pct(X.allowed_max_fraction||G.allowed_max_fraction)]].map(([k,v])=>'<div class="card"><span>'+esc(k)+'</span><b>'+esc(v)+'</b></div>').join('');
document.getElementById('execpolicy').innerHTML='<table><tbody><tr><th>Precio max contrato</th><td>'+money(samplePolicy.max_contract_price)+'</td><th>Spread max</th><td>'+pct(samplePolicy.max_spread_pct)+'</td></tr><tr><th>Bid minimo</th><td>'+money(samplePolicy.min_bid)+'</td><th>Bid size minimo</th><td>'+esc(samplePolicy.min_bid_size??'--')+'</td></tr><tr><th>Ask size minimo</th><td>'+esc(samplePolicy.min_ask_size??'--')+'</td><th>Calidad requerida</th><td>'+esc(samplePolicy.require_market_quality??true)+'</td></tr></tbody></table>';
document.getElementById('exectable').innerHTML=XE.length?'<table><thead><tr><th>Fecha / inicio</th><th>Side</th><th>Contrato</th><th>Bid</th><th>Ask</th><th>Spread</th><th>Bid size</th><th>Ask size</th><th>Presupuesto</th><th>Max contratos</th><th>Decision</th><th>Motivo</th></tr></thead><tbody>'+XE.map(e=>{const g=e.execution_gate||{},q=g.market_quality||{};return '<tr><td>'+esc(e.decision_date||e.start||'--')+'</td><td>'+esc(e.side||'--')+'</td><td>'+esc(g.contract||e.contract||'--')+'</td><td>'+money(q.bid??e.entry_bid)+'</td><td>'+money(g.entry_ask??e.entry_ask)+'</td><td>'+pct(q.spread_pct)+'</td><td>'+esc(q.entry_bid_size??e.entry_bid_size??'--')+'</td><td>'+esc(q.entry_ask_size??e.entry_ask_size??'--')+'</td><td>'+money(g.risk_budget)+'</td><td>'+esc(g.max_contracts_by_risk_budget??0)+'</td><td><b>'+esc(g.status||'--')+'</b></td><td>'+esc((g.reasons||[]).concat(g.missing_market_quality||[]).join(', ')||'--')+'</td></tr>'}).join('')+'</tbody></table>':'<div class="sub" style="padding:18px 0">Aun no hay episodios prospectivos para evaluar. El primer registro aparecera cuando H03 se active despues del freeze.</div>';
document.getElementById('healthstatus').textContent=H.overall_status||'UNKNOWN';document.getElementById('healthtime').textContent=H.generated_at_utc||'--';
document.getElementById('healthcards').innerHTML=[['Fallos',H.failures||0],['Esperando',H.waiting||0],['Snapshots',H.snapshot_count||0],['Episodios prospectivos',H.prospective_episode_count||0]].map(([k,v])=>'<div class="card"><span>'+esc(k)+'</span><b>'+esc(v)+'</b></div>').join('');
document.getElementById('healthchecks').innerHTML=(H.checks||[]).length?'<table><thead><tr><th>Check</th><th>Estado</th><th>Detalle</th></tr></thead><tbody>'+(H.checks||[]).map(c=>'<tr><td>'+esc(c.label)+'</td><td><b>'+esc(c.status)+'</b></td><td>'+esc(c.detail)+'</td></tr>').join('')+'</tbody></table>':'<div class="sub" style="padding:18px 0">Readiness pendiente de generar.</div>';

const riskAnalysis=M.entry_controls_analysis||{},calibration=M.jev_calibration_analysis||{};
document.getElementById('p2analysis').innerHTML='<div class="explain">'+esc(riskAnalysis.status)+' · '+(riskAnalysis.prospective_signal_days?.length||0)+' días. Escenarios comparativos; no activan límites nuevos. Un contrato por entrada.</div><table><tr><th>Escenario</th><th>Cerradas</th><th>Bloqueadas</th><th>Pendientes</th><th>P&L realizado</th><th>Máximo DD diario</th></tr>'+Object.entries(riskAnalysis.scenarios||{}).map(([k,x])=>'<tr><td>'+esc(k)+'</td><td>'+esc(x.closed_trades)+'</td><td>'+esc(x.blocked_signals)+'</td><td>'+esc(x.pending_reconciliation_positions)+'</td><td>'+money(x.realized_net_pnl)+'</td><td>'+pct(Math.max(0,...Object.values(x.daily||{}).map(d=>d.max_drawdown_fraction)))+'</td></tr>').join('')+'</table>';
document.getElementById('p3analysis').innerHTML='<div class="explain">'+esc(calibration.status)+' · '+(calibration.diagnostics?.qualified_directional_decisions||0)+' CALL/PUT elegibles según su umbral guardado y '+(calibration.diagnostics?.closed_profit_labels||0)+' resultados de ganancia · Umbral Jev '+pct(calibration.trading_threshold??.60)+'. P(respuesta) no equivale a P(ganancia). Se calibra un objetivo empírico separado, P&L bruto positivo, con política congelada y validación en días posteriores. No se aplica automáticamente.</div><table><tr><th>Símbolo</th><th>Muestras sin solapamiento</th><th>Días</th><th>Estado</th></tr>'+(calibration.segments||[]).map(x=>'<tr><td>'+esc(x.identity?.symbol)+'</td><td>'+esc(x.independent_labels)+'</td><td>'+esc(x.independent_days)+'</td><td>'+esc(x.status)+'</td></tr>').join('')+'</table>';
const replay=P.causal_replay_summary||{};
const liveLedger=P.live_ledger||[];
const openPaper=P.open_positions||[];
const replayPnl=+(replay.net_account_pnl||0);
const totalRealized=+(P.realized_net_pnl||0);
const liveRealized=totalRealized-replayPnl;

if(P.epoch_id){
 const epoch=document.createElement('div');epoch.className='explain';
 const previous=P.previous_epoch_summary||{},plan=P.observation_plan||{};
 epoch.innerHTML='<b>Etapa '+esc(P.epoch_id)+'</b> · Inicio '+esc(P.epoch_start_utc)+
  ' · Capital inicial '+money(P.initial_cash)+' · 1 contrato por entrada · Presupuesto de prima '+pct(P.epoch_initial_configuration?.premium_budget_fraction)+
  '<br>Etapa anterior archivada: saldo '+money(previous.prior_cash)+' · P&L '+money(previous.prior_net_account_pnl)+
  '. Los resultados mostrados pertenecen a la etapa actual.<br>Revisión principal: '+esc(plan.primary_review_sessions)+' sesiones; seguimiento ampliado 60–90 sesiones.';
 document.getElementById('papercards').before(epoch);
}

document.getElementById('papercards').innerHTML=[
 ['Equity'+(P.equity_is_estimate?' estimada':''),money(P.equity??P.cash??P.initial_cash),(P.pending_reconciliation_positions||0)+' pendientes de reconciliar'],
 ['Cash',money(P.cash),'efectivo disponible'],
 ['Net P&L',money(P.net_account_pnl),pct((P.net_account_pnl||0)/(P.initial_cash||1000))],
 ['Live realized',money(liveRealized),'desde live_start_utc'],
 ['Unrealized',money(P.unrealized_pnl||0),(openPaper.length||0)+' posiciones abiertas']
].map(x=>'<div class="card"><div class="lab">'+x[0]+'</div><div class="val">'+x[1]+'</div><div class="hint">'+x[2]+'</div></div>').join('');

document.getElementById('paperScientificGate').textContent=pct(P.scientific_risk_fraction??G.allowed_max_fraction);
document.getElementById('paperCurrentRisk').textContent=pct(PC.risk_fraction??P.paper_risk_fraction??0.2);

function paintPaperRisk(v){
 document.querySelectorAll('#paperRiskButtons button').forEach(b=>{
   b.classList.toggle('active',Math.abs(Number(b.dataset.risk)-Number(v))<1e-9);
 });
 document.getElementById('paperCurrentRisk').textContent=pct(v);
}

paintPaperRisk(PC.risk_fraction??P.paper_risk_fraction??0.2);

window.setPaperRisk=async function(v){
 const status=document.getElementById('paperControlStatus');
 status.textContent='Guardando...';

 try{
   const r=await fetch('/api/paper-control',{
     method:'POST',
     headers:{'Content-Type':'application/json'},
     body:JSON.stringify({risk_fraction:Number(v)})
   });

   const d=await r.json();

   if(!r.ok)throw new Error(d.error||'HTTP '+r.status);

   paintPaperRisk(d.risk_fraction);

   status.innerHTML=
     '<span class="good">Guardado: '+pct(d.risk_fraction)+
     ' · se aplicará a nuevas señales del Paper Trading.</span>';
 }catch(e){
   status.innerHTML='<span class="bad">Error: '+esc(e.message)+'</span>';
 }
};

document.querySelectorAll('#paperRiskButtons button').forEach(b=>{
 b.addEventListener('click',()=>window.setPaperRisk(Number(b.dataset.risk)));
});

document.getElementById('paperOpen').innerHTML=openPaper.length
?'<table><thead><tr><th>Entrada UTC</th><th>Hipótesis</th><th>Contrato</th><th>Qty</th><th>Estado</th><th>ASK</th><th>Último BID</th><th>Return</th><th>MFE</th><th>MAE</th></tr></thead><tbody>'+
openPaper.map(x=>'<tr><td>'+esc(x.entry_time||x.signal_time)+'</td><td>'+esc(x.hypothesis)+'</td><td>'+esc(x.contract)+'</td><td>'+esc(x.quantity)+'</td><td>'+esc(x.status)+'</td><td>'+money(x.entry_ask)+'</td><td>'+money(x.last_bid)+'</td><td>'+pct(x.unrealized_return)+'</td><td>'+pct(x.mfe)+'</td><td>'+pct(x.mae)+'</td></tr>').join('')+
'</tbody></table>'
:'<div class="sub" style="padding:18px 0">No hay posiciones abiertas.</div>';

document.getElementById('paperLedger').innerHTML=liveLedger.length
?'<table><thead><tr><th>Hora UTC</th><th>Hipótesis</th><th>Contrato</th><th>Qty</th><th>Gate</th><th>Estado</th><th>Entrada ask</th><th>Salida UTC</th><th>Bid salida</th><th>Salida</th><th>P&L neto</th><th>Cash después</th></tr></thead><tbody>'+
[...liveLedger].reverse().map(x=>'<tr><td>'+esc(x.signal_time)+'</td><td>'+esc(x.hypothesis)+'</td><td>'+esc(x.contract)+'</td><td>'+esc(x.quantity||0)+'</td><td>'+esc(x.execution_gate?.status||'--')+'</td><td>'+esc(x.status)+'</td><td>'+money(x.entry_ask)+'</td><td>'+esc(x.exit_time)+'</td><td>'+money(x.exit_bid)+'</td><td>'+esc(x.exit_reason||'--')+'</td><td>'+money(x.net_pnl)+'</td><td>'+money(x.cash_after)+'</td></tr>').join('')+
'</tbody></table>'
:'<div class="sub" style="padding:18px 0">Aún no hay trades LIVE_PAPER posteriores al corte.</div>';

document.getElementById('paperReplay').innerHTML=
 '<div class="metricline"><span>Señales replay</span><b>'+esc(replay.signals_seen||0)+'</b></div>'+
 '<div class="metricline"><span>Bloqueadas</span><b>'+esc(replay.blocked_signals||0)+'</b></div>'+
 '<div class="metricline"><span>Cerradas</span><b>'+esc(replay.closed_trades||0)+'</b></div>'+
 '<div class="metricline"><span>P&L replay</span><b>'+money(replay.net_account_pnl||0)+'</b></div>'+
 '<div class="metricline"><span>Inicio LIVE</span><b>'+esc(P.live_start_utc||'--')+'</b></div>';


const riskScenarios=Object.values(PR.scenarios||{}).sort(
 (a,b)=>(a.risk_fraction||0)-(b.risk_fraction||0)
);

window.renderPaperRiskDetail=function(fraction){
 const z=riskScenarios.find(
   x=>Math.abs(Number(x.risk_fraction)-Number(fraction))<1e-9
 );

 if(!z)return;

 const rows=z.ledger||[];

 document.getElementById('paperRiskDetail').innerHTML=
 '<h2>Detalle '+pct(z.risk_fraction)+'</h2>'+
 (
   rows.length
   ?'<table><thead><tr>'+
     '<th>Hora UTC</th>'+
     '<th>Hipótesis</th>'+
     '<th>Contrato</th>'+
     '<th>ASK</th>'+
     '<th>Gate</th>'+
     '<th>Estado</th>'+
     '<th>Salida</th>'+
     '<th>P&L neto</th>'+
     '</tr></thead><tbody>'+
     rows.map(x=>
       '<tr>'+
       '<td>'+esc(x.signal_time)+'</td>'+
       '<td>'+esc(x.hypothesis)+'</td>'+
       '<td>'+esc(x.contract)+'</td>'+
       '<td>'+money(x.entry_ask)+'</td>'+
       '<td>'+esc(x.execution_gate?.status||'--')+'</td>'+
       '<td>'+esc(x.status)+'</td>'+
       '<td>'+esc(x.exit_reason||'--')+'</td>'+
       '<td>'+money(x.net_pnl)+'</td>'+
       '</tr>'
     ).join('')+
     '</tbody></table>'
   :'<div class="sub">Sin señales.</div>'
 );

 document.querySelectorAll('.paper-risk-row').forEach(r=>{
   r.classList.toggle(
     'active',
     Math.abs(Number(r.dataset.risk)-Number(fraction))<1e-9
   );
 });
};

document.getElementById('paperRiskComparison').innerHTML=
 riskScenarios.length
 ?'<table>'+
  '<thead><tr>'+
   '<th>Risk</th>'+
   '<th>Señales</th>'+
   '<th>Ejecutadas</th>'+
   '<th>Bloqueadas</th>'+
   '<th>TP10</th>'+
   '<th>SL10</th>'+
   '<th>Horizon</th>'+
   '<th>P&L neto</th>'+
   '<th>Return</th>'+
   '<th>Equity final</th>'+
  '</tr></thead>'+
  '<tbody>'+
  riskScenarios.map(x=>
   '<tr class="paper-risk-row" data-risk="'+x.risk_fraction+'" '+
   'onclick="renderPaperRiskDetail('+x.risk_fraction+')" '+
   'style="cursor:pointer">'+
    '<td><b>'+pct(x.risk_fraction)+'</b></td>'+
    '<td>'+esc(x.signals_seen)+'</td>'+
    '<td>'+esc(x.executed_trades)+'</td>'+
    '<td>'+esc(x.blocked_signals)+'</td>'+
    '<td>'+esc(x.tp10)+'</td>'+
    '<td>'+esc(x.sl10)+'</td>'+
    '<td>'+esc(x.horizon)+'</td>'+
    '<td>'+money(x.net_pnl)+'</td>'+
    '<td>'+pct(x.return_pct)+'</td>'+
    '<td>'+money(x.final_equity)+'</td>'+
   '</tr>'
  ).join('')+
  '</tbody></table>'
 :'<div class="sub">Risk comparison pendiente.</div>';

if(riskScenarios.length){
 const selected=Number(
   PC.risk_fraction ?? P.paper_risk_fraction ?? 0.2
 );
 const preferred=
   riskScenarios.find(x=>Math.abs(x.risk_fraction-selected)<1e-9)
   || riskScenarios[0];

 renderPaperRiskDetail(preferred.risk_fraction);
}

document.getElementById('labgrid').innerHTML=Object.entries(M.discovery||{}).map(([name,v])=>'<div class="discovery"><h3>'+esc(name.replace('label_','').replaceAll('_',' '))+'</h3><table><thead><tr><th>#</th><th>Reglas</th><th>n</th><th>Tasa</th><th>Baseline</th><th>Lift</th><th>1a mitad</th><th>2a mitad</th></tr></thead><tbody>'+v.top_stable.map((z,i)=>'<tr><td>'+(i+1)+'</td><td>'+z.rules.map(ruleText).join('<br>')+'</td><td>'+z.n+'</td><td>'+pct(z.rate)+'</td><td>'+pct(z.baseline)+'</td><td>'+Number(z.lift).toFixed(2)+'x</td><td>'+pct(z.first_half?.rate)+'</td><td>'+pct(z.second_half?.rate)+'</td></tr>').join('')+'</tbody></table></div>').join('');
function show(id){document.querySelectorAll('[data-tabgroup]').forEach(x=>x.style.display=x.dataset.tabgroup===id?(x.classList.contains('tabpage')?'block':''):'none');tabs.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));}
tabs.addEventListener('click',e=>{let b=e.target.closest('button');if(b)show(b.dataset.tab)});show('session');
})();


/* ALL_FROZEN_HYPOTHESES_MONITOR_V01 */
(function () {
  function pct(x) {
    if (x === null || x === undefined || Number.isNaN(Number(x))) return "—";
    return (Number(x) * 100).toFixed(2) + "%";
  }

  function num(x) {
    if (x === null || x === undefined || Number.isNaN(Number(x))) return "—";
    return String(x);
  }

  function label(id) {
    if (id === "CALL_FLOW_REVERSAL_V01") return "H01 · CALL Flow Reversal";
    if (id === "PUT_SKEW_SHORT_V01") return "H02 · PUT Skew Short";
    if (id === "H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01") return "H03 · CALL Relative Weakness";
    return id;
  }

  function renderAllFrozenHypothesesMonitor() {
    const meta = window.RESEARCH_META || {};
    const tracker = meta.tracker_summary || {};
    const prospective = tracker.prospective_only || {};

    const ids = Object.keys(prospective);
    if (!ids.length) return;

    const old = document.getElementById("all-frozen-hypotheses-monitor");
    if (old) old.remove();

    const rows = ids.map(function (id) {
      const x = prospective[id] || {};
      const n = Number(x.n || 0);
      const rowClass = n > 0 ? "hyp-live-active" : "hyp-live-empty";

      return `
        <tr class="${rowClass}">
          <td><strong>${label(id)}</strong><br><span>${id}</span></td>
          <td>${num(x.n)}</td>
          <td>${pct(x.mean_return)}</td>
          <td>${pct(x.win_rate)}</td>
          <td>${pct(x.gt10_rate)}</td>
          <td>${pct(x.ltm10_rate)}</td>
          <td>${pct(x.tp10_before_sl10_rate)}</td>
          <td>${num(x.tp10_sl10_decided_n)}</td>
        </tr>`;
    }).join("");

    const card = document.createElement("section");
    card.id = "all-frozen-hypotheses-monitor";
    card.innerHTML = `
      <style>
        #all-frozen-hypotheses-monitor {
          margin: 14px 0 18px 0;
          padding: 16px;
          border: 1px solid rgba(96, 165, 250, 0.28);
          border-radius: 14px;
          background: rgba(15, 23, 42, 0.88);
          color: #e5e7eb;
          box-shadow: 0 8px 28px rgba(0,0,0,.20);
        }
        #all-frozen-hypotheses-monitor h2 {
          margin: 0 0 6px 0;
          font-size: 18px;
        }
        #all-frozen-hypotheses-monitor .sub {
          margin-bottom: 14px;
          color: #94a3b8;
          font-size: 13px;
        }
        #all-frozen-hypotheses-monitor .table-wrap {
          overflow-x: auto;
        }
        #all-frozen-hypotheses-monitor table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }
        #all-frozen-hypotheses-monitor th,
        #all-frozen-hypotheses-monitor td {
          padding: 10px 8px;
          border-bottom: 1px solid rgba(148, 163, 184, 0.18);
          text-align: left;
          vertical-align: top;
          white-space: nowrap;
        }
        #all-frozen-hypotheses-monitor td:first-child,
        #all-frozen-hypotheses-monitor th:first-child {
          white-space: normal;
          min-width: 260px;
        }
        #all-frozen-hypotheses-monitor td span {
          color: #94a3b8;
          font-size: 11px;
        }
        #all-frozen-hypotheses-monitor .hyp-live-active {
          background: rgba(22, 163, 74, 0.10);
        }
        #all-frozen-hypotheses-monitor .hyp-live-empty {
          opacity: .78;
        }
      </style>

      <h2>All Frozen Hypotheses Monitor</h2>
      <div class="sub">
        Monitor prospectivo intradía para H01/H02/H03. H03 permanece congelada;
        estos datos no modifican reglas ni thresholds.
        Rows prospectivas: <strong>${num(tracker.prospective_rows)}</strong>.
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Hipótesis</th>
              <th>n</th>
              <th>Mean return</th>
              <th>Win rate</th>
              <th>GT +10%</th>
              <th>LT -10%</th>
              <th>TP10 before SL10</th>
              <th>Decided n</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;

    const anchor =
      document.querySelector(".tabs") ||
      document.querySelector("[role='tablist']") ||
      document.querySelector("nav") ||
      document.body.firstElementChild;

    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(card, anchor.nextSibling);
    } else {
      document.body.prepend(card);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(renderAllFrozenHypothesesMonitor, 250);
    });
  } else {
    setTimeout(renderAllFrozenHypothesesMonitor, 250);
  }
})();
