from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v11.38.2";','const APP_VERSION="v12.0";',1).replace('<span id="appVersionLabel">v11.38.2</span>','<span id="appVersionLabel">v12.0</span>',1)
css=r'''
/* VendorTracker v12 — show-floor UI */
:root{--vt-ink:#111827;--vt-blue:#3157f6;--vt-violet:#7557ff;--vt-mint:#2dd4bf;--vt-canvas:#f3f6fb;--vt-card:rgba(255,255,255,.92)}
body{background:radial-gradient(circle at 15% 0,#e9efff 0,transparent 28%),radial-gradient(circle at 95% 10%,#eee9ff 0,transparent 24%),var(--vt-canvas)}
.appTop{height:72px;padding:0 24px;background:rgba(255,255,255,.82);backdrop-filter:blur(18px);border-bottom:1px solid rgba(203,213,225,.7)}
.brandMark{border-radius:12px;background:linear-gradient(145deg,var(--vt-blue),var(--vt-violet));box-shadow:0 8px 22px rgba(79,70,229,.28)}
.syncPill{padding:6px 10px;background:#e8fff8;color:#08745f}.appLayout{grid-template-columns:218px minmax(0,1fr)}
.sidebar{background:linear-gradient(180deg,#10182b,#111827 58%,#17203a);padding:20px 12px}.sideNav{gap:7px}.sideBtn{padding:12px 14px;border-radius:12px;font-size:14px}.sideBtn.active{background:linear-gradient(135deg,#3157f6,#6247e8);box-shadow:0 8px 24px rgba(49,87,246,.25)}
.main{padding:30px 32px 44px;max-width:1500px}.pageHeader{margin-bottom:20px}.pageHeader h1{font-size:32px}.pageHeader p{font-size:14px}.panel,.metric,.productCard{background:var(--vt-card);border:1px solid rgba(203,213,225,.72);box-shadow:0 10px 32px rgba(15,23,42,.045)}
.panel{border-radius:20px;padding:20px}.metric{border-radius:18px}.productCard{border-radius:18px}.btn{min-height:44px;border-radius:12px}.btnPrimary{background:linear-gradient(135deg,var(--vt-blue),#2449dc);box-shadow:0 7px 16px rgba(49,87,246,.16)}
.input{min-height:46px;border-radius:12px;border-color:#d7deea}.input:focus{border-color:#7089ff;box-shadow:0 0 0 4px rgba(80,105,255,.12)}
.addInventoryPanel{border:0;background:linear-gradient(135deg,rgba(255,255,255,.98),rgba(245,247,255,.96));box-shadow:0 14px 42px rgba(40,55,110,.08)}
.invTypeToggle{background:#e9eef7;padding:5px;border-radius:14px}.invTypeToggle button{border-radius:10px;min-height:43px}.lookupGrid{gap:12px}.lookupCard{border-radius:16px;transition:.15s}.lookupCard:hover{transform:translateY(-2px);box-shadow:0 10px 22px rgba(15,23,42,.08)}
.quickAdd{display:none}
@media(min-width:821px){.page.active{animation:vtIn .18s ease-out}@keyframes vtIn{from{opacity:.4;transform:translateY(3px)}to{opacity:1;transform:none}}}
@media(max-width:820px){
 body{background:#f5f7fb}.appTop{height:60px;padding:0 14px}.appTop .brandMark{width:32px;height:32px}.appTop .brand span:last-child{font-size:15px}.appLayout{display:block}.main{padding:16px 12px calc(94px + env(safe-area-inset-bottom));max-width:none}.pageHeader{margin:4px 4px 15px}.pageHeader h1{font-size:26px}.pageHeader p{font-size:13px}.panel{padding:15px;border-radius:18px;margin-top:12px}.cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.metric{padding:13px}.metricValue{font-size:21px}.grid{grid-template-columns:1fr}.btn,.input,select{min-height:48px}.btn{padding:12px 15px}.actions{display:grid;grid-template-columns:1fr 1fr}.actions .btn,.actions .miniBtn{width:100%}.productGrid{grid-template-columns:1fr}.productCard{padding:14px}.paymentBtns{grid-template-columns:repeat(2,1fr)}
 .bottomNav{grid-template-columns:repeat(5,1fr);padding:6px 5px calc(7px + env(safe-area-inset-bottom));border-top:1px solid #dbe2ee;box-shadow:0 -10px 30px rgba(15,23,42,.08);background:rgba(255,255,255,.96);backdrop-filter:blur(18px)}.bottomNav button{min-height:50px;border-radius:12px;font-size:11px;font-weight:750}.bottomNav button.active{background:#edf2ff;color:#2748dc}
 .addInventoryPanel{margin-top:8px}.invTypeToggle{display:grid;grid-template-columns:1fr 1fr;width:100%}.lookupGrid{grid-template-columns:repeat(2,minmax(0,1fr))}.lookupCard{padding:9px}.lookupCard img{height:130px}.tableWrap{border:0;overflow:visible}table.mobileCards{min-width:0}table.mobileCards thead{display:none}table.mobileCards,table.mobileCards tbody,table.mobileCards tr,table.mobileCards td{display:block;width:100%}table.mobileCards tr{background:#fff;border:1px solid #e0e6ef;border-radius:16px;margin-bottom:10px;padding:10px;box-shadow:0 5px 16px rgba(15,23,42,.035)}table.mobileCards td{border:0;padding:5px 4px}table.mobileCards td:before{content:attr(data-label);display:block;font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#7b8799;font-weight:800;margin-bottom:2px}
 .toast{left:12px;right:12px;bottom:calc(84px + env(safe-area-inset-bottom));text-align:center}.undoBar{bottom:calc(84px + env(safe-area-inset-bottom));width:calc(100% - 24px)}
}
@media(max-width:420px){.cards{grid-template-columns:1fr 1fr}.metricLabel{font-size:10px}.metricValue{font-size:19px}.lookupGrid{grid-template-columns:1fr 1fr}.pageHeader h1{font-size:24px}}
'''
s=s.replace('</style>',css+'\n</style>',1)
js=r'''
/* v12 usability helpers: preserve behavior, improve mobile semantics */
function vtMobileTableLabels(){document.querySelectorAll('.tableWrap table').forEach(t=>{if(innerWidth<=820)t.classList.add('mobileCards');else t.classList.remove('mobileCards');const heads=[...t.querySelectorAll('thead th')].map(x=>x.textContent.trim());t.querySelectorAll('tbody tr').forEach(r=>[...r.children].forEach((td,i)=>{if(heads[i])td.dataset.label=heads[i]}))})}
const _vtShowPageV12=showPage;showPage=function(name){const out=_vtShowPageV12(name);requestAnimationFrame(vtMobileTableLabels);return out};
window.addEventListener('resize',vtMobileTableLabels);setTimeout(vtMobileTableLabels,400);
'''
if 'v12 usability helpers' not in s:s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)
p.write_text(s,encoding='utf-8')
