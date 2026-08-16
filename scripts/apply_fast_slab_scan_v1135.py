from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.34";','const APP_VERSION="v11.35";',1)
s=s.replace('<span id="appVersionLabel">v11.34</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.35</span> · Updated Aug 15, 2026',1)

start=s.index('      <section id="graded" class="page">')
end=s.index('      <section id="settings" class="page">', start)
page='''      <section id="graded" class="page">
        <div class="pageHeader"><div><h1>eBay Slab Comps</h1><p>Snap the slab label or type one quick search to check recent eBay sold comps.</p></div></div>

        <div class="panel">
          <div class="panelHead"><div><h3>Fast slab lookup</h3><div class="small">Take a close photo of the slab label or type something like “Charizard 199/165 PSA 10”.</div></div></div>
          <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
            <label class="btn btnPrimary" style="display:inline-flex;align-items:center;justify-content:center">📷 Scan slab label
              <input id="ebaySlabPhoto" type="file" accept="image/*" capture="environment" style="display:none" onchange="scanEbaySlabPhoto(this.files?.[0])">
            </label>
            <span class="small">Best results: fill the photo with the top grading label and avoid glare.</span>
          </div>
          <img id="ebaySlabPreview" alt="Slab label preview" style="display:none;max-width:260px;max-height:180px;object-fit:contain;border:1px solid var(--line);border-radius:12px;margin-top:12px;background:#f8fafc">
          <div id="ebaySlabOcrStatus" class="small" style="margin-top:8px"></div>
          <div class="lookupRow" style="margin-top:14px">
            <input id="ebaySlabQuick" class="input" placeholder="Card + number + slab + grade, e.g. Charizard 199/165 PSA 10" onkeydown="if(event.key==='Enter'){event.preventDefault();searchEbaySlabComps()}">
            <button id="ebaySlabSearchBtn" class="btn btnPrimary" onclick="searchEbaySlabComps()">Get last 4 sold</button>
          </div>
          <div class="actions" style="margin-top:10px"><button class="btn btnGhost" onclick="openEbaySlabSoldSearch()">Open eBay sold search ↗</button><button class="btn btnGhost" onclick="clearEbaySlabQuick()">Clear</button></div>
          <div id="ebaySlabStatus" class="small" style="margin-top:10px">Automatic last-4 lookup activates once your eBay developer credentials are connected. The sold-search button works now.</div>
        </div>

        <div class="panel">
          <div class="panelHead"><div><h3>Last 4 sold</h3><div class="small">Newest matching eBay sold listings only.</div></div></div>
          <div id="ebaySlabResults" class="gradedCompGrid"><div class="empty" style="grid-column:1/-1">No eBay comps loaded yet.</div></div>
          <div class="gradedSummary" style="margin-top:14px">
            <div class="metric"><div class="metricLabel">4-sale total</div><div class="metricValue" id="ebaySlabTotal">$0.00</div></div>
            <div class="metric"><div class="metricLabel">4-sale average</div><div class="metricValue" id="ebaySlabAverage">$0.00</div></div>
          </div>
        </div>
      </section>\n\n'''
s=s[:start]+page+s[end:]

js='''
function ebaySlabQuery(){
  return (document.getElementById('ebaySlabQuick')?.value||'').trim().replace(/\\s+/g,' ');
}
function openEbaySlabSoldSearch(){
  const q=ebaySlabQuery();
  if(!q)return toast('Scan a slab or type the card first');
  window.open('https://www.ebay.com/sch/i.html?_nkw='+encodeURIComponent(q)+'&LH_Sold=1&LH_Complete=1','_blank','noopener');
}
function clearEbaySlabQuick(){
  const q=document.getElementById('ebaySlabQuick'); if(q)q.value='';
  const img=document.getElementById('ebaySlabPreview'); if(img){img.src='';img.style.display='none'}
  const st=document.getElementById('ebaySlabOcrStatus'); if(st)st.textContent='';
}
function normalizeSlabOcrText(text){
  let t=String(text||'').replace(/[|]/g,' ').replace(/\\s+/g,' ').trim();
  t=t.replace(/BECKETT GRADING SERVICES/ig,'BGS').replace(/BECKETT/ig,'BGS');
  return t;
}
function buildQuickSlabQueryFromOcr(text){
  const raw=normalizeSlabOcrText(text);
  const upper=raw.toUpperCase();
  let company='';
  if(/\\bPSA\\b/.test(upper)) company='PSA';
  else if(/\\bCGC\\b/.test(upper)) company='CGC';
  else if(/\\bBGS\\b/.test(upper)) company='BGS';
  else if(/\\bSGC\\b/.test(upper)) company='SGC';
  else if(/\\bACE\\b/.test(upper)) company='ACE';
  const gradeMatch=raw.match(/(?:GEM\\s*MINT|MINT|NM-MT|GRADE)?\\s*(10|9\\.5|9|8\\.5|8|7\\.5|7|6\\.5|6|5\\.5|5|4\\.5|4|3\\.5|3|2\\.5|2|1\\.5|1)\\b/i);
  const numMatch=raw.match(/\\b(?:#\\s*)?([A-Z]{0,4}\\d{1,4}\\s*\\/\\s*[A-Z]{0,4}\\d{1,4}|[A-Z]{1,4}[- ]?\\d{1,4})\\b/i);
  const yearMatch=raw.match(/\\b(19\\d{2}|20\\d{2})\\b/);
  let cleaned=raw
    .replace(/\\b(?:PSA|CGC|BGS|SGC|ACE)\\b/ig,' ')
    .replace(/(?:GEM\\s*MINT|MINT|NM-MT|GRADE)\\s*(?:10|9\\.5|9|8\\.5|8|7\\.5|7|6\\.5|6|5\\.5|5|4\\.5|4|3\\.5|3|2\\.5|2|1\\.5|1)/ig,' ')
    .replace(/CERT(?:IFICATION)?\\s*(?:NO|#|NUMBER)?\\s*[:#-]?\\s*\\d+/ig,' ')
    .replace(/\\b\\d{7,10}\\b/g,' ')
    .replace(/\\s+/g,' ').trim();
  const parts=[];
  if(yearMatch && !cleaned.includes(yearMatch[1])) parts.push(yearMatch[1]);
  if(cleaned) parts.push(cleaned);
  if(numMatch && !cleaned.toUpperCase().includes(numMatch[1].replace(/\\s+/g,'').toUpperCase())) parts.push(numMatch[1].replace(/\\s+/g,''));
  if(company) parts.push(company);
  if(gradeMatch) parts.push(gradeMatch[1]);
  return parts.join(' ').replace(/\\s+/g,' ').trim();
}
async function scanEbaySlabPhoto(file){
  if(!file)return;
  const preview=document.getElementById('ebaySlabPreview');
  const status=document.getElementById('ebaySlabOcrStatus');
  const quick=document.getElementById('ebaySlabQuick');
  if(preview){preview.src=URL.createObjectURL(file);preview.style.display='block'}
  if(status)status.textContent='Reading slab label…';
  try{
    if(!window.Tesseract)throw new Error('Scanner unavailable');
    const result=await Tesseract.recognize(file,'eng',{logger:m=>{if(status&&m.status==='recognizing text')status.textContent='Reading slab label… '+Math.round((m.progress||0)*100)+'%'}});
    const detected=buildQuickSlabQueryFromOcr(result?.data?.text||'');
    if(!detected)throw new Error('Could not read enough label text');
    if(quick)quick.value=detected;
    if(status)status.textContent='Detected: '+detected+' — check it, then tap Get last 4 sold.';
  }catch(e){
    if(status)status.textContent='Could not confidently read the slab. Try a closer, glare-free photo or type one quick search line.';
  }
}
'''
# Put overrides immediately before dashboard renderer; later declaration wins over older slab helpers.
s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)

p.write_text(s,encoding='utf-8')
