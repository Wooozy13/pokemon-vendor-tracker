from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.32";','const APP_VERSION="v11.33";',1)
s=s.replace('<span id="appVersionLabel">v11.32</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.33</span> · Updated Aug 15, 2026',1)

# Three graded sources now: eBay, ALT, Collectr.
s=s.replace('grid-template-columns:repeat(4,minmax(0,1fr))','grid-template-columns:repeat(3,minmax(0,1fr))',1)
s=s.replace("              <button id=\"gradedSourceTcg\" class=\"gradedSourceBtn\" type=\"button\" onclick=\"setGradedPriceSource('tcgplayer')\">TCGPlayer</button>\n",'',1)

# Add slab scan styles.
css='''
/* Graded slab camera scanner */
.slabScanBox{margin-top:12px;padding:14px;border:1px solid #bfdbfe;background:#f8fbff;border-radius:14px}
.slabScanActions{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.slabScanPreview{width:116px;height:84px;object-fit:cover;border:1px solid var(--line);border-radius:10px;background:#fff;display:none;margin-top:10px}
.slabParsedGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px}
.slabRaw{white-space:pre-wrap;max-height:130px;overflow:auto;font-size:11px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:8px;margin-top:8px}
@media(max-width:620px){.slabParsedGrid{grid-template-columns:1fr}.slabScanActions .btn{width:100%}}
'''
if '/* Graded slab camera scanner */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

# Insert camera scanner before the graded manual fields.
needle='''          <div class="grid" style="margin-top:12px">
            <input id="gradedCardName" class="input" placeholder="Card name + card number, e.g. Charizard 199/165">
            <select id="gradedCompany" class="input"><option>PSA</option><option>CGC</option><option>Beckett / BGS</option><option>SGC</option><option>ACE</option><option>Other</option></select>
            <input id="gradedGrade" class="input" placeholder="Grade, e.g. 10">
          </div>'''
replacement='''          <div class="slabScanBox">
            <div class="gradedHeaderRow"><div><strong>📷 Scan slab label</strong><div class="small" style="margin-top:3px">Take a close photo of the grading label. VendorTracker will try to read the card, card number, slab company, grade, and cert/serial.</div></div><span class="comingSoonBadge" style="background:#ecfdf5;color:#166534;border-color:#bbf7d0">Camera ready</span></div>
            <div class="slabScanActions" style="margin-top:10px">
              <label class="btn btnPrimary">Take / choose slab photo<input id="gradedSlabPhoto" type="file" accept="image/*" capture="environment" style="display:none" onchange="scanGradedSlab(this.files?.[0])"></label>
              <button class="btn btnGhost" type="button" onclick="clearGradedSlabScan()">Clear scan</button>
            </div>
            <img id="gradedSlabPreview" class="slabScanPreview" alt="Slab label preview">
            <div id="gradedScanStatus" class="small" style="margin-top:8px">Tip: fill the camera frame with the slab's top label and keep glare off the serial number.</div>
            <details id="gradedRawWrap" class="hidden" style="margin-top:8px"><summary class="small" style="cursor:pointer;font-weight:800">View detected label text</summary><div id="gradedRawText" class="slabRaw"></div></details>
          </div>
          <div class="grid" style="margin-top:12px">
            <input id="gradedCardName" class="input" placeholder="Card name / set, e.g. Charizard ex">
            <input id="gradedCardNumber" class="input" placeholder="Card number, e.g. 199/165">
            <select id="gradedCompany" class="input"><option>PSA</option><option>CGC</option><option>Beckett / BGS</option><option>SGC</option><option>ACE</option><option>Other</option></select>
            <input id="gradedGrade" class="input" placeholder="Grade, e.g. 10">
            <input id="gradedCert" class="input" placeholder="Cert / serial number">
          </div>'''
if needle not in s:
    raise SystemExit('graded details block not found')
s=s.replace(needle,replacement,1)

# Remove TCGPlayer from source handling and update source notes.
s=s.replace("  const names={ebay:'eBay',alt:'ALT',tcgplayer:'TCGPlayer',collectr:'Collectr'};","  const names={ebay:'eBay',alt:'ALT',collectr:'Collectr'};",1)
s=s.replace("  ['Ebay','Alt','Tcg','Collectr'].forEach(k=>document.getElementById('gradedSource'+k)?.classList.remove('active'));","  ['Ebay','Alt','Collectr'].forEach(k=>document.getElementById('gradedSource'+k)?.classList.remove('active'));",1)
s=s.replace("  const id={ebay:'gradedSourceEbay',alt:'gradedSourceAlt',tcgplayer:'gradedSourceTcg',collectr:'gradedSourceCollectr'}[source];","  const id={ebay:'gradedSourceEbay',alt:'gradedSourceAlt',collectr:'gradedSourceCollectr'}[source];",1)
s=s.replace("    else if(source==='tcgplayer')note.textContent='TCGPlayer selected — the button automatically searches using the card name/number, slab company, and grade.';\n",'',1)

old='''function gradedSearchText(){
  const card=document.getElementById('gradedCardName')?.value.trim()||'';
  const company=document.getElementById('gradedCompany')?.value||'';
  const grade=document.getElementById('gradedGrade')?.value.trim()||'';
  return [card,company,grade].filter(Boolean).join(' ').replace(/\\s+/g,' ').trim();
}
function openGradedSourceSearch(){
  const q=gradedSearchText();
  if(!q)return toast('Enter the card number, slab type, and grade first');
  const encoded=encodeURIComponent(q);
  if(gradedPriceSource==='ebay')return window.open('https://www.ebay.com/sch/i.html?_nkw='+encoded+'&LH_Sold=1&LH_Complete=1','_blank','noopener');
  if(gradedPriceSource==='tcgplayer')return window.open('https://www.tcgplayer.com/search/all/product?q='+encoded+'&view=grid','_blank','noopener');
  if(gradedPriceSource==='collectr')return window.open('https://app.getcollectr.com/?query='+encoded,'_blank','noopener');
  // ALT supports searching graded cards by description/grade on web, but does not publish a stable deep-link query format.
  // Open ALT and copy the exact generated search text so the user can paste it immediately without retyping.
  if(navigator.clipboard?.writeText){navigator.clipboard.writeText(q).catch(()=>{});toast('ALT search copied — paste it into ALT search');}
  return window.open('https://www.alt.xyz/','_blank','noopener');
}
'''
new='''function gradedSearchText(){
  const card=document.getElementById('gradedCardName')?.value.trim()||'';
  const number=document.getElementById('gradedCardNumber')?.value.trim()||'';
  const company=document.getElementById('gradedCompany')?.value||'';
  const grade=document.getElementById('gradedGrade')?.value.trim()||'';
  const cert=document.getElementById('gradedCert')?.value.trim()||'';
  const identity=[card,number].filter(Boolean).join(' ').trim() || cert;
  return [identity,company,grade].filter(Boolean).join(' ').replace(/\\s+/g,' ').trim();
}
function openGradedSourceSearch(){
  const q=gradedSearchText();
  if(!q)return toast('Scan a slab or enter the card, slab type, and grade first');
  const encoded=encodeURIComponent(q);
  if(gradedPriceSource==='ebay')return window.open('https://www.ebay.com/sch/i.html?_nkw='+encoded+'&LH_Sold=1&LH_Complete=1','_blank','noopener');
  if(gradedPriceSource==='collectr')return window.open('https://app.getcollectr.com/?query='+encoded,'_blank','noopener');
  if(navigator.clipboard?.writeText){navigator.clipboard.writeText(q).catch(()=>{});toast('ALT search copied — paste it into ALT search');}
  return window.open('https://www.alt.xyz/','_blank','noopener');
}
'''
if old not in s:
    raise SystemExit('graded search block not found')
s=s.replace(old,new,1)

# OCR + parsing. Tesseract is already loaded by VendorTracker for photo scanning.
scan_js=r'''
function normalizeSlabOcrText(text){return String(text||'').replace(/[|]/g,'I').replace(/\r/g,'').replace(/[ \t]+/g,' ').trim()}
function detectSlabCompany(text){
  const t=text.toUpperCase();
  if(/\bPSA\b|PROFESSIONAL SPORTS AUTHENTICATOR/.test(t))return 'PSA';
  if(/\bCGC\b|CERTIFIED GUARANTY/.test(t))return 'CGC';
  if(/\bBGS\b|BECKETT/.test(t))return 'Beckett / BGS';
  if(/\bSGC\b|SPORTSCARD GUARANTY/.test(t))return 'SGC';
  if(/\bACE\b/.test(t))return 'ACE';
  return '';
}
function detectSlabGrade(text){
  const t=text.toUpperCase();
  let m=t.match(/(?:GEM\s*(?:MT|MINT)|PRISTINE|MINT|NM[ -]?MT|NEAR MINT)[^0-9]{0,8}(10(?:\.0)?|9\.5|9|8\.5|8|7\.5|7|6\.5|6|5\.5|5|4\.5|4|3\.5|3|2\.5|2|1\.5|1)\b/);
  if(m)return m[1];
  m=t.match(/\b(?:GRADE|GRD)\s*[:#-]?\s*(10(?:\.0)?|9\.5|9|8\.5|8|7\.5|7|6\.5|6|5\.5|5|4\.5|4|3\.5|3|2\.5|2|1\.5|1)\b/);
  if(m)return m[1];
  const lines=t.split('\n').map(x=>x.trim()).filter(Boolean);
  for(const line of lines){if(/^(10(?:\.0)?|9\.5|9|8\.5|8|7\.5|7|6\.5|6|5\.5|5|4\.5|4|3\.5|3|2\.5|2|1\.5|1)$/.test(line))return line}
  return '';
}
function detectSlabCert(text){
  const t=text.toUpperCase();
  let m=t.match(/(?:CERT(?:IFICATION)?|SERIAL|CERT\s*#|NO\.?)[^0-9]{0,8}([0-9][0-9 .-]{5,13}[0-9])/);
  if(m)return m[1].replace(/[^0-9]/g,'');
  const candidates=(t.match(/\b\d{7,10}\b/g)||[]).filter(v=>!/^20\d{2}/.test(v));
  return candidates.sort((a,b)=>b.length-a.length)[0]||'';
}
function detectSlabCardNumber(text){
  const t=text.toUpperCase();
  let m=t.match(/\b([A-Z]*\d{1,4}[A-Z]?\s*\/\s*[A-Z]*\d{1,4}[A-Z]?)\b/);
  if(m)return m[1].replace(/\s+/g,'');
  m=t.match(/(?:CARD\s*(?:NO|#)|#)\s*([A-Z]*\d{1,4}[A-Z]?)/);
  return m?m[1]:'';
}
function detectSlabCardName(text,company,grade,cert,cardNumber){
  const reject=/^(PSA|CGC|BGS|BECKETT|SGC|ACE|GEM|MINT|PRISTINE|NEAR MINT|NM|GRADE|CERT|CERTIFICATION|SERIAL|AUTHENTIC|POKEMON|POKÉMON)$/i;
  const lines=String(text||'').split('\n').map(x=>x.trim().replace(/\s+/g,' ')).filter(x=>x.length>=3);
  const filtered=lines.filter(line=>{
    const up=line.toUpperCase();
    if(reject.test(up))return false;
    if(company && up.includes(company.split(' ')[0].toUpperCase()))return false;
    if(cert && up.replace(/\D/g,'').includes(cert))return false;
    if(cardNumber && up.replace(/\s/g,'').includes(cardNumber.toUpperCase()))return false;
    if(/^\d+(?:\.\d+)?$/.test(line))return false;
    if(/^(19|20)\d{2}$/.test(line))return false;
    if(/CERT|SERIAL|GRADE|AUTHENTIC/i.test(line))return false;
    return /[A-Za-z]{3}/.test(line);
  });
  if(!filtered.length)return '';
  const scored=filtered.map((line,i)=>({line,score:(/[A-Za-z]{5}/.test(line)?20:0)+Math.min(line.length,45)-(i*0.5)})).sort((a,b)=>b.score-a.score);
  return scored[0]?.line||'';
}
function applySlabOcrFields(text){
  const cleaned=normalizeSlabOcrText(text);
  const company=detectSlabCompany(cleaned);
  const grade=detectSlabGrade(cleaned);
  const cert=detectSlabCert(cleaned);
  const number=detectSlabCardNumber(cleaned);
  const name=detectSlabCardName(cleaned,company,grade,cert,number);
  if(company){const sel=document.getElementById('gradedCompany');if(sel)sel.value=company}
  if(grade)document.getElementById('gradedGrade').value=grade;
  if(cert)document.getElementById('gradedCert').value=cert;
  if(number)document.getElementById('gradedCardNumber').value=number;
  if(name)document.getElementById('gradedCardName').value=name;
  return {company,grade,cert,number,name};
}
async function scanGradedSlab(file){
  if(!file)return;
  const status=document.getElementById('gradedScanStatus');
  const preview=document.getElementById('gradedSlabPreview');
  const raw=document.getElementById('gradedRawText');
  const rawWrap=document.getElementById('gradedRawWrap');
  try{
    if(preview){preview.src=URL.createObjectURL(file);preview.style.display='block'}
    if(status)status.textContent='Reading slab label… keep this page open for a moment.';
    if(!window.Tesseract)throw new Error('OCR engine unavailable');
    const result=await Tesseract.recognize(file,'eng',{logger:m=>{if(status&&m.status==='recognizing text')status.textContent=`Reading slab label… ${Math.round((m.progress||0)*100)}%`;}});
    const text=normalizeSlabOcrText(result?.data?.text||'');
    if(raw)raw.textContent=text||'No text detected.';
    if(rawWrap)rawWrap.classList.remove('hidden');
    const found=applySlabOcrFields(text);
    const count=[found.name,found.number,found.company,found.grade,found.cert].filter(Boolean).length;
    if(status)status.textContent=count?`Scan complete — filled ${count} field${count===1?'':'s'}. Check the details below, then choose ALT, eBay, or Collectr.`:'Could not confidently read the label. Try a closer, glare-free photo.';
    if(count)toast('Slab details detected');
  }catch(e){
    console.error(e);
    if(status)status.textContent='Could not read that slab photo. Try a closer photo with better lighting and less glare.';
  }
}
function clearGradedSlabScan(){
  const ids=['gradedCardName','gradedCardNumber','gradedGrade','gradedCert'];ids.forEach(id=>{const e=document.getElementById(id);if(e)e.value=''});
  const f=document.getElementById('gradedSlabPhoto');if(f)f.value='';
  const p=document.getElementById('gradedSlabPreview');if(p){p.removeAttribute('src');p.style.display='none'}
  const r=document.getElementById('gradedRawText');if(r)r.textContent='';
  document.getElementById('gradedRawWrap')?.classList.add('hidden');
  const st=document.getElementById('gradedScanStatus');if(st)st.textContent="Tip: fill the camera frame with the slab's top label and keep glare off the serial number.";
}
function openAllGradedSources(){
  const q=gradedSearchText();if(!q)return toast('Scan a slab or enter its details first');
  const encoded=encodeURIComponent(q);
  window.open('https://www.ebay.com/sch/i.html?_nkw='+encoded+'&LH_Sold=1&LH_Complete=1','_blank','noopener');
  window.open('https://app.getcollectr.com/?query='+encoded,'_blank','noopener');
  if(navigator.clipboard?.writeText)navigator.clipboard.writeText(q).catch(()=>{});
  window.open('https://www.alt.xyz/','_blank','noopener');
  toast('Opened eBay + Collectr; ALT search copied');
}
'''
if 'async function scanGradedSlab(file)' not in s:
    s=s.replace("let gradedPriceSource='ebay';",scan_js+"\nlet gradedPriceSource='ebay';",1)

# Add one-click lookup across the three remaining sources.
s=s.replace('''            <div class="gradedSourceActions">
              <button id="gradedOpenSourceBtn" class="btn btnGhost" onclick="openGradedSourceSearch()">Open eBay sold search ↗</button>
            </div>''','''            <div class="gradedSourceActions">
              <button id="gradedOpenSourceBtn" class="btn btnGhost" onclick="openGradedSourceSearch()">Open eBay sold search ↗</button>
              <button class="btn btnPrimary" type="button" onclick="openAllGradedSources()">Look up on ALT + eBay + Collectr ↗</button>
            </div>''',1)

# Remove any remaining graded-only TCGPlayer wording/source option, but do not touch inventory TCGplayer pricing.
s=s.replace("tcgplayer:'TCGPlayer',",'')

p.write_text(s,encoding='utf-8')
