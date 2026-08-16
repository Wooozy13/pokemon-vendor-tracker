from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.29";','const APP_VERSION="v11.30";',1)
s=s.replace('<span id="appVersionLabel">v11.29</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.30</span> · Updated Aug 15, 2026',1)

# CSS
css='''
/* Graded Price Check */
.comingSoonBadge{display:inline-flex;align-items:center;border-radius:999px;padding:5px 9px;background:#fff7ed;color:#9a3412;border:1px solid #fed7aa;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.04em}
.gradedHeaderRow{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.gradedCompGrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px}
.gradedCompCard{border:1px solid var(--line);background:#fff;border-radius:12px;padding:12px}
.gradedCompCard label{display:block;font-size:11px;font-weight:800;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em}
.gradedSummary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px}
.gradedSummary .metric{padding:14px}
.comingSoonPanel{border:1px dashed #fdba74;background:#fffaf5;border-radius:14px;padding:16px;margin-top:14px}
.comingSoonPanel button:disabled{opacity:.55;cursor:not-allowed;transform:none}
@media(max-width:820px){.gradedCompGrid{grid-template-columns:1fr 1fr}.gradedSummary{grid-template-columns:1fr 1fr}}
@media(max-width:430px){.gradedCompGrid{grid-template-columns:1fr}.gradedSummary{grid-template-columns:1fr 1fr}}
'''
if '/* Graded Price Check */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

# Desktop nav add after Expenses
old='''      <button class="sideBtn secondarySide" data-page="expenses" onclick="go('expenses',this)">⌁ <span>Expenses</span></button>'''
new=old+'''\n      <button class="sideBtn secondarySide" data-page="graded" onclick="go('graded',this)">◈ <span>Graded Price Check</span> <span class="comingSoonBadge" style="margin-left:auto">New</span></button>'''
s=s.replace(old,new,1)

# Graded page before settings
anchor='''      <section id="settings" class="page">'''
page='''      <section id="graded" class="page">
        <div class="pageHeader"><div><h1>Graded Price Check</h1><p>Compare graded-card sold comps and calculate a clean four-sale average.</p></div></div>
        <div class="panel">
          <div class="gradedHeaderRow"><div><h3 style="margin:0">Card details</h3><div class="small">Enter the exact card and slab grade you are checking.</div></div><span class="comingSoonBadge">Automatic eBay comps coming soon</span></div>
          <div class="grid" style="margin-top:12px">
            <input id="gradedCardName" class="input" placeholder="Card name / set / number, e.g. Charizard 199/165">
            <select id="gradedCompany" class="input"><option>PSA</option><option>CGC</option><option>Beckett / BGS</option><option>SGC</option><option>ACE</option><option>Other</option></select>
            <input id="gradedGrade" class="input" placeholder="Grade, e.g. 10">
          </div>
          <div class="actions" style="margin-top:10px"><button class="btn btnGhost" onclick="openManualEbaySoldSearch()">Open eBay sold search ↗</button></div>
        </div>
        <div class="panel">
          <div class="panelHead"><div><h3>Manual last 4 sold</h3><div class="small">Enter four matching sold prices. VendorTracker calculates the total and four-sale average instantly.</div></div></div>
          <div class="gradedCompGrid">
            <div class="gradedCompCard"><label>Sold comp 1</label><input id="gradedComp1" class="input" type="number" min="0" step=".01" placeholder="0.00" oninput="updateGradedCompAverage()"></div>
            <div class="gradedCompCard"><label>Sold comp 2</label><input id="gradedComp2" class="input" type="number" min="0" step=".01" placeholder="0.00" oninput="updateGradedCompAverage()"></div>
            <div class="gradedCompCard"><label>Sold comp 3</label><input id="gradedComp3" class="input" type="number" min="0" step=".01" placeholder="0.00" oninput="updateGradedCompAverage()"></div>
            <div class="gradedCompCard"><label>Sold comp 4</label><input id="gradedComp4" class="input" type="number" min="0" step=".01" placeholder="0.00" oninput="updateGradedCompAverage()"></div>
          </div>
          <div class="gradedSummary">
            <div class="metric"><div class="metricLabel">Total of 4 sold</div><div class="metricValue" id="gradedCompTotal">$0.00</div></div>
            <div class="metric"><div class="metricLabel">4-sale average</div><div class="metricValue" id="gradedCompAverage">$0.00</div></div>
          </div>
          <div class="small" id="gradedCompStatus" style="margin-top:9px">Enter all four sold prices for a complete 4-sale average.</div>
          <div class="actions" style="margin-top:10px"><button class="btn btnGhost" onclick="clearGradedComps()">Clear comps</button></div>
        </div>
        <div class="comingSoonPanel">
          <div class="gradedHeaderRow"><div><strong>Automatic eBay last 4 sold</strong><div class="small" style="margin-top:4px">Once eBay developer access is connected, this will automatically pull the four newest matching sold listings, show each comp, and calculate the average.</div></div><span class="comingSoonBadge">Coming Soon</span></div>
          <button class="btn btnPrimary" style="margin-top:12px" disabled>Search automatic eBay comps — Coming Soon</button>
        </div>
      </section>\n\n'''
if 'id="graded" class="page"' not in s:
    s=s.replace(anchor,page+anchor,1)

# Mobile more menu add graded before settings
old_mobile='''      <button onclick="openMorePage('expenses')"><span>⌁</span><div><strong>Expenses</strong><small>Fees, travel & costs</small></div></button>'''
new_mobile=old_mobile+'''\n      <button onclick="openMorePage('graded')"><span>◈</span><div><strong>Graded Price Check</strong><small>Manual sold comps · Auto eBay coming soon</small></div><span class="comingSoonBadge">New</span></button>'''
s=s.replace(old_mobile,new_mobile,1)

# JS functions before renderDashboard
js='''
function updateGradedCompAverage(){
  const vals=[1,2,3,4].map(i=>{
    const v=document.getElementById('gradedComp'+i)?.value;
    return v===''?null:Math.max(0,Number(v||0));
  });
  const entered=vals.filter(v=>v!==null && Number.isFinite(v));
  const total=entered.reduce((a,v)=>a+v,0);
  const avg=entered.length?total/entered.length:0;
  const t=document.getElementById('gradedCompTotal'),a=document.getElementById('gradedCompAverage'),st=document.getElementById('gradedCompStatus');
  if(t)t.textContent=money(total);if(a)a.textContent=money(avg);
  if(st)st.textContent=entered.length===4?'Using all 4 sold comps.':`${entered.length}/4 sold comps entered — average currently uses the comps entered.`;
}
function clearGradedComps(){[1,2,3,4].forEach(i=>{const e=document.getElementById('gradedComp'+i);if(e)e.value=''});updateGradedCompAverage()}
function openManualEbaySoldSearch(){
  const name=document.getElementById('gradedCardName')?.value.trim()||'';
  const company=document.getElementById('gradedCompany')?.value||'';
  const grade=document.getElementById('gradedGrade')?.value.trim()||'';
  if(!name)return toast('Enter the graded card first');
  const q=encodeURIComponent([name,company,grade].filter(Boolean).join(' '));
  window.open('https://www.ebay.com/sch/i.html?_nkw='+q+'&LH_Sold=1&LH_Complete=1','_blank','noopener');
}
'''
if 'function updateGradedCompAverage()' not in s:
    s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)

p.write_text(s,encoding='utf-8')
