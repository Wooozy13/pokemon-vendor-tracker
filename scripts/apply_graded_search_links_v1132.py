from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.31";','const APP_VERSION="v11.32";',1)
s=s.replace('<span id="appVersionLabel">v11.31</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.32</span> · Updated Aug 15, 2026',1)

# Correct TCGPlayer casing everywhere in the graded tool.
s=s.replace('>TCGplayer<','>TCGPlayer<')
s=s.replace("tcgplayer:'TCGplayer'","tcgplayer:'TCGPlayer'")
s=s.replace('TCGplayer selected','TCGPlayer selected')

# Improve card input wording so users know the collector number should be included.
s=s.replace('placeholder="Card name / set / number, e.g. Charizard 199/165"','placeholder="Card name + card number, e.g. Charizard 199/165"',1)

old="""function gradedSearchText(){
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
"""
new="""function gradedSearchText(){
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
"""
if old not in s:
    raise SystemExit('graded search function block not found')
s=s.replace(old,new,1)

# Source-specific notes/buttons.
s=s.replace("if(open)open.textContent=`Open ${name} ↗`;","if(open)open.textContent=source==='ebay'?`Search ${name} sold comps ↗`:source==='alt'?`Open ${name} + copy search ↗`:`Search ${name} ↗`;",1)
s=s.replace("else if(source==='tcgplayer')note.textContent='TCGPlayer selected — use any graded pricing/listing data available for the exact card and grade.';","else if(source==='tcgplayer')note.textContent='TCGPlayer selected — the button automatically searches using the card name/number, slab company, and grade.';",1)
s=s.replace("else note.textContent='Collectr selected — use Collectr graded-card pricing as your reference source.';","else note.textContent='Collectr selected — the button automatically searches app.getcollectr.com using the card name/number, slab company, and grade.';",1)
s=s.replace("else if(source==='alt')note.textContent='ALT selected — use ALT graded-card market/sales data as your comp source.';","else if(source==='alt')note.textContent='ALT selected — VendorTracker builds the exact card/slab/grade search and copies it for ALT because ALT does not publish a stable deep-link search URL.';",1)

p.write_text(s,encoding='utf-8')
