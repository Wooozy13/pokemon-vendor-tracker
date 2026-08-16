from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v11.38";','const APP_VERSION="v11.39";',1).replace('<span id="appVersionLabel">v11.38</span>','<span id="appVersionLabel">v11.39</span>',1)
js=r'''
/* Ultra-fast lookup v11.39: race exact queries; don't wait for slow siblings */
async function firstUsefulCardBatch(raw,limit=18){
  const {parsed,queries}=buildFastCardQueries(raw);
  if(!queries.length)return [];
  const cached=readPersistentSearchCache('card',raw);
  if(cached?.length)return cached.slice(0,limit);
  const primary=queries.slice(0,4).map((q,i)=>fetchCardQuery(q,i<2?14:10).then(cards=>({cards,i})).catch(()=>({cards:[],i})));
  let pending=primary.slice(), best=[];
  while(pending.length){
    const tagged=pending.map((promise,index)=>promise.then(value=>({value,index})));
    const {value,index}=await Promise.race(tagged); pending.splice(index,1);
    if(value.cards?.length){
      best=uniqueCards(best.concat(value.cards));
      best.sort((a,b)=>scoreCardResult(b,parsed)-scoreCardResult(a,parsed));
      if(best.length){ writePersistentSearchCache('card',raw,best.slice(0,36)); return best.slice(0,limit); }
    }
  }
  return [];
}
async function searchPokemonCards(){
 const raw=document.getElementById('pName').value.trim(),status=document.getElementById('cardLookupStatus'); if(!raw){status.textContent='Enter a card name first.';return}
 const cached=readPersistentSearchCache('card',raw); if(cached?.length){currentLookupResults=cached;renderCardLookup(cached);document.getElementById('cardLookupModal').classList.remove('hidden');status.textContent=`Found ${cached.length} cached match${cached.length===1?'':'es'}.`;resolveCardText(raw,36).then(x=>{if(x?.length){writePersistentSearchCache('card',raw,x);}}).catch(()=>{});return}
 status.textContent='Searching…';
 try{const cards=await firstUsefulCardBatch(raw,36);currentLookupResults=cards;if(!cards.length){status.textContent='No match found. Try the Pokémon name plus collector number.';return}renderCardLookup(cards);document.getElementById('cardLookupModal').classList.remove('hidden');status.textContent=`Found ${cards.length} match${cards.length===1?'':'es'}.`;resolveCardText(raw,36).then(x=>{if(x?.length)writePersistentSearchCache('card',raw,x)}).catch(()=>{})}catch(e){status.textContent='Card lookup unavailable. Try again.'}
}
async function searchPurchaseItem(){
 const q=document.getElementById('buySearch')?.value.trim(),status=document.getElementById('buyLookupStatus'),box=document.getElementById('buyLookupResults');if(!q)return toast('Enter something to search');status.textContent='Searching…';box.innerHTML='';purchaseSelectedItem=null;document.getElementById('buyNewItemFields')?.classList.add('hidden');
 try{if(purchaseLookupType==='card'){const cards=await firstUsefulCardBatch(q,18);purchaseLookupResults=cards;if(!cards.length){status.textContent='No cards found.';return}status.textContent=`Found ${cards.length} card${cards.length===1?'':'s'}.`;box.innerHTML=cards.map((c,i)=>{const prices=c.tcgplayer?.prices||{},m=Object.values(prices).map(v=>v?.market).find(v=>v!=null);return `<button class="purchaseLookupCard" onclick="selectPurchaseLookup(${i})"><img src="${esc(c.images?.small||c.images?.large||'')}"><strong>${esc(c.name)}</strong><div class="small">${esc(c.set?.name||'')} #${esc(fullCardNumber(c))}</div><div class="marketGood" style="margin-top:5px">${m!=null?money(m):'Market unavailable'}</div></button>`}).join('');resolveCardText(q,18).then(x=>{if(x?.length)writePersistentSearchCache('card',q,x)}).catch(()=>{})}else{const cached=readPersistentSearchCache('sealed',q);const items=cached?.length?cached:await fastSealedProductSearch(q);purchaseLookupResults=items;if(!items.length){status.textContent='No sealed products found.';return}status.textContent=`Found ${items.length} sealed product${items.length===1?'':'s'}.`;box.innerHTML=items.map((x,i)=>`<button class="purchaseLookupCard" onclick="selectPurchaseLookup(${i})"><img src="${esc(x.imageUrl||'')}"><strong>${esc(x.name||'')}</strong><div class="small">${esc(x.groupName||'')}</div><div class="marketGood" style="margin-top:5px">${x.marketPrice!=null?money(x.marketPrice):'Market unavailable'}</div></button>`).join('')}}catch(e){status.textContent='Lookup failed. Try again.'}
}
'''
if '/* Ultra-fast lookup v11.39' not in s:s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)
p.write_text(s,encoding='utf-8')
