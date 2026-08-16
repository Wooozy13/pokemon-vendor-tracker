from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.33";','const APP_VERSION="v11.34";',1)
s=s.replace('<span id="appVersionLabel">v11.33</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.34</span> · Updated Aug 15, 2026',1)

# Replace the entire graded page with a simple eBay-only comps tool.
start=s.index('      <section id="graded" class="page">')
end=s.index('      <section id="settings" class="page">', start)
page='''      <section id="graded" class="page">
        <div class="pageHeader"><div><h1>eBay Slab Comps</h1><p>Check the 4 most recent matching eBay sold comps for a graded card.</p></div></div>

        <div class="panel">
          <div class="panelHead"><div><h3>Find graded card</h3><div class="small">Enter the exact card and slab details. VendorTracker will use these to find matching eBay sold listings.</div></div></div>
          <div class="grid">
            <input id="ebaySlabCard" class="input" placeholder="Card name, e.g. Charizard ex">
            <input id="ebaySlabNumber" class="input" placeholder="Card number, e.g. 199/165">
            <select id="ebaySlabCompany" class="input"><option>PSA</option><option>CGC</option><option>Beckett / BGS</option><option>SGC</option><option>ACE</option><option>Other</option></select>
            <input id="ebaySlabGrade" class="input" placeholder="Grade, e.g. 10">
          </div>
          <div class="actions" style="margin-top:12px">
            <button id="ebaySlabSearchBtn" class="btn btnPrimary" onclick="searchEbaySlabComps()">Get last 4 eBay sold comps</button>
            <button class="btn btnGhost" onclick="openEbaySlabSoldSearch()">Open eBay sold search ↗</button>
          </div>
          <div id="ebaySlabStatus" class="small" style="margin-top:10px">Automatic sold-comp lookup will activate once your eBay developer access is connected.</div>
        </div>

        <div class="panel">
          <div class="panelHead"><div><h3>Last 4 sold</h3><div class="small">Newest matching eBay sold listings only.</div></div></div>
          <div id="ebaySlabResults" class="gradedCompGrid">
            <div class="empty" style="grid-column:1/-1">No eBay comps loaded yet.</div>
          </div>
          <div class="gradedSummary" style="margin-top:14px">
            <div class="metric"><div class="metricLabel">4-sale total</div><div class="metricValue" id="ebaySlabTotal">$0.00</div></div>
            <div class="metric"><div class="metricLabel">4-sale average</div><div class="metricValue" id="ebaySlabAverage">$0.00</div></div>
          </div>
        </div>
      </section>

'''
s=s[:start]+page+s[end:]

# Remove source-specific labels from mobile menu description if present.
s=s.replace('Manual sold comps · Auto eBay coming soon','Last 4 eBay sold comps')

js='''
function ebaySlabQuery(){
  const card=document.getElementById('ebaySlabCard')?.value.trim()||'';
  const number=document.getElementById('ebaySlabNumber')?.value.trim()||'';
  const company=document.getElementById('ebaySlabCompany')?.value||'';
  const grade=document.getElementById('ebaySlabGrade')?.value.trim()||'';
  return [card,number,company,grade].filter(Boolean).join(' ').replace(/\\s+/g,' ').trim();
}
function openEbaySlabSoldSearch(){
  const q=ebaySlabQuery();
  if(!q)return toast('Enter the card and slab details first');
  window.open('https://www.ebay.com/sch/i.html?_nkw='+encodeURIComponent(q)+'&LH_Sold=1&LH_Complete=1','_blank','noopener');
}
function renderEbaySlabComps(items){
  const box=document.getElementById('ebaySlabResults');
  const totalEl=document.getElementById('ebaySlabTotal');
  const avgEl=document.getElementById('ebaySlabAverage');
  const clean=(items||[]).slice(0,4).filter(x=>Number.isFinite(Number(x.price)));
  if(!clean.length){
    box.innerHTML='<div class="empty" style="grid-column:1/-1">No matching sold comps found.</div>';
    totalEl.textContent=money(0);avgEl.textContent=money(0);return;
  }
  box.innerHTML=clean.map((x,i)=>`<div class="gradedCompCard">
    <label>Sold comp ${i+1}</label>
    ${x.image?`<img src="${esc(x.image)}" alt="" style="width:100%;aspect-ratio:1.35;object-fit:contain;border-radius:10px;background:#f8fafc;margin-bottom:8px">`:''}
    <strong style="display:block;font-size:20px">${money(x.price)}</strong>
    <div class="small" style="margin-top:5px">${esc(x.title||'eBay sold listing')}</div>
    ${x.soldDate?`<div class="small" style="margin-top:4px">Sold ${esc(x.soldDate)}</div>`:''}
    ${x.url?`<button class="miniBtn btnGhost" style="margin-top:8px" onclick="window.open('${esc(x.url)}','_blank','noopener')">View eBay ↗</button>`:''}
  </div>`).join('');
  const total=clean.reduce((a,x)=>a+Number(x.price||0),0);
  totalEl.textContent=money(total);
  avgEl.textContent=money(total/clean.length);
}
async function searchEbaySlabComps(){
  const q=ebaySlabQuery();
  const status=document.getElementById('ebaySlabStatus');
  const btn=document.getElementById('ebaySlabSearchBtn');
  if(!q){toast('Enter the card and slab details first');return}
  status.textContent='Searching eBay sold comps…';btn.disabled=true;
  try{
    const {data,error}=await sb.functions.invoke('ebay-slab-comps',{body:{query:q,limit:4}});
    if(error)throw error;
    if(!data?.success)throw new Error(data?.error||'eBay sold comp lookup unavailable');
    const items=(data.results||[]).slice(0,4);
    renderEbaySlabComps(items);
    status.textContent=items.length?`Loaded ${items.length} matching eBay sold comp${items.length===1?'':'s'}.`:'No matching eBay sold comps found.';
  }catch(e){
    renderEbaySlabComps([]);
    status.textContent='Automatic eBay sold comps are not connected yet. Once your eBay developer credentials are approved and added to VendorTracker, this button will pull the newest 4 sold automatically.';
  }finally{btn.disabled=false}
}
'''
# Insert before dashboard renderer once.
if 'function searchEbaySlabComps()' not in s:
    s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)

p.write_text(s,encoding='utf-8')
