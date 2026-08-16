from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.30";','const APP_VERSION="v11.31";',1)
s=s.replace('<span id="appVersionLabel">v11.30</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.31</span> · Updated Aug 15, 2026',1)

css='''
/* Graded pricing sources */
.gradedSourceTabs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:12px}
.gradedSourceBtn{border:1px solid var(--line);background:#fff;border-radius:11px;padding:11px 10px;font-weight:850;color:#475569}
.gradedSourceBtn.active{background:#eff6ff;color:#1d4ed8;border-color:#93c5fd;box-shadow:0 0 0 2px #dbeafe inset}
.gradedSourceNote{margin-top:9px;padding:10px 12px;background:#f8fafc;border:1px solid var(--line);border-radius:10px}
.gradedSourceActions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
@media(max-width:620px){.gradedSourceTabs{grid-template-columns:1fr 1fr}}
'''
if '/* Graded pricing sources */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

old='''          <div class="actions" style="margin-top:10px"><button class="btn btnGhost" onclick="openManualEbaySoldSearch()">Open eBay sold search ↗</button></div>'''
new='''          <div style="margin-top:14px"><div class="small" style="font-weight:800">Pricing source</div>
            <div class="gradedSourceTabs">
              <button id="gradedSourceEbay" class="gradedSourceBtn active" type="button" onclick="setGradedPriceSource('ebay')">eBay</button>
              <button id="gradedSourceAlt" class="gradedSourceBtn" type="button" onclick="setGradedPriceSource('alt')">ALT</button>
              <button id="gradedSourceTcg" class="gradedSourceBtn" type="button" onclick="setGradedPriceSource('tcgplayer')">TCGplayer</button>
              <button id="gradedSourceCollectr" class="gradedSourceBtn" type="button" onclick="setGradedPriceSource('collectr')">Collectr</button>
            </div>
            <div id="gradedSourceNote" class="gradedSourceNote small">eBay selected — enter the latest four matching sold prices below.</div>
            <div class="gradedSourceActions">
              <button id="gradedOpenSourceBtn" class="btn btnGhost" onclick="openGradedSourceSearch()">Open eBay sold search ↗</button>
            </div>
          </div>'''
s=s.replace(old,new,1)

s=s.replace('<h3>Manual last 4 sold</h3><div class="small">Enter four matching sold prices. VendorTracker calculates the total and four-sale average instantly.</div>', '<h3 id="gradedCompHeading">Manual eBay last 4 sold</h3><div id="gradedCompHelp" class="small">Enter four matching sold prices from eBay. VendorTracker calculates the total and four-sale average instantly.</div>',1)

oldpanel='''          <div class="gradedHeaderRow"><div><strong>Automatic eBay last 4 sold</strong><div class="small" style="margin-top:4px">Once eBay developer access is connected, this will automatically pull the four newest matching sold listings, show each comp, and calculate the average.</div></div><span class="comingSoonBadge">Coming Soon</span></div>
          <button class="btn btnPrimary" style="margin-top:12px" disabled>Search automatic eBay comps — Coming Soon</button>'''
newpanel='''          <div class="gradedHeaderRow"><div><strong id="gradedAutoTitle">Automatic eBay graded pricing</strong><div id="gradedAutoHelp" class="small" style="margin-top:4px">Once the eBay integration is connected, this will automatically pull matching sold comps and calculate the four-sale average.</div></div><span class="comingSoonBadge">Coming Soon</span></div>
          <button id="gradedAutoBtn" class="btn btnPrimary" style="margin-top:12px" disabled>Automatic eBay pricing — Coming Soon</button>'''
s=s.replace(oldpanel,newpanel,1)

js='''
let gradedPriceSource='ebay';
function setGradedPriceSource(source){
  gradedPriceSource=source;
  const names={ebay:'eBay',alt:'ALT',tcgplayer:'TCGplayer',collectr:'Collectr'};
  const name=names[source]||'eBay';
  ['Ebay','Alt','Tcg','Collectr'].forEach(k=>document.getElementById('gradedSource'+k)?.classList.remove('active'));
  const id={ebay:'gradedSourceEbay',alt:'gradedSourceAlt',tcgplayer:'gradedSourceTcg',collectr:'gradedSourceCollectr'}[source];
  document.getElementById(id)?.classList.add('active');
  const note=document.getElementById('gradedSourceNote');
  const head=document.getElementById('gradedCompHeading');
  const help=document.getElementById('gradedCompHelp');
  const open=document.getElementById('gradedOpenSourceBtn');
  const autoTitle=document.getElementById('gradedAutoTitle');
  const autoHelp=document.getElementById('gradedAutoHelp');
  const autoBtn=document.getElementById('gradedAutoBtn');
  if(head)head.textContent=`Manual ${name} graded comps`;
  if(help)help.textContent=`Enter up to four matching graded-card prices from ${name}. VendorTracker calculates the total and average instantly.`;
  if(open)open.textContent=`Open ${name} ↗`;
  if(note){
    if(source==='ebay')note.textContent='eBay selected — use recent sold listings for the strongest comp-based estimate.';
    else if(source==='alt')note.textContent='ALT selected — use ALT graded-card market/sales data as your comp source.';
    else if(source==='tcgplayer')note.textContent='TCGplayer selected — use any graded pricing/listing data available for the exact card and grade.';
    else note.textContent='Collectr selected — use Collectr graded-card pricing as your reference source.';
  }
  if(autoTitle)autoTitle.textContent=`Automatic ${name} graded pricing`;
  if(autoHelp)autoHelp.textContent=`Automatic ${name} lookup will be connected when the required API/integration is available. Manual comps above work now.`;
  if(autoBtn)autoBtn.textContent=`Automatic ${name} pricing — Coming Soon`;
}
function gradedSearchText(){
  const name=document.getElementById('gradedCardName')?.value.trim()||'';
  const company=document.getElementById('gradedCompany')?.value||'';
  const grade=document.getElementById('gradedGrade')?.value.trim()||'';
  return [name,company,grade].filter(Boolean).join(' ');
}
function openGradedSourceSearch(){
  const q=gradedSearchText();
  if(!q)return toast('Enter the graded card first');
  if(gradedPriceSource==='ebay')return window.open('https://www.ebay.com/sch/i.html?_nkw='+encodeURIComponent(q)+'&LH_Sold=1&LH_Complete=1','_blank','noopener');
  if(gradedPriceSource==='tcgplayer')return window.open('https://www.tcgplayer.com/search/all/product?q='+encodeURIComponent(q)+'&view=grid','_blank','noopener');
  if(gradedPriceSource==='alt')return window.open('https://www.alt.xyz/','_blank','noopener');
  return window.open('https://www.collectr.com/','_blank','noopener');
}
'''
if "let gradedPriceSource='ebay';" not in s:
    s=s.replace('function updateGradedCompAverage(){',js+'\nfunction updateGradedCompAverage(){',1)

p.write_text(s,encoding='utf-8')
