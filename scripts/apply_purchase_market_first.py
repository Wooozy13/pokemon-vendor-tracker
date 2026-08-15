from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('  <input id="buyLineTotal" class="input" type="number" min="0" step=".01" placeholder="Total paid for this item">\n','')
s=s.replace('  <input id="buyNewLineTotal" class="input" type="number" min="0" step=".01" placeholder="Total paid for this item">\n','')
s=s.replace('<div class="small">Everything here will be saved as one grouped purchase.</div>','<div class="small">Add everything at market value first, then enter what you actually paid for each line before saving.</div>',1)
s=s.replace('<div class="purchaseBatchSummary"><div><div class="small">Batch total</div><strong id="purchaseBatchTotal" style="font-size:24px">$0.00</strong></div><div class="actions">','<div class="purchaseBatchSummary"><div style="display:flex;gap:28px;flex-wrap:wrap"><div><div class="small">Market value</div><strong id="purchaseBatchMarketTotal" style="font-size:24px">$0.00</strong></div><div><div class="small">Total paid</div><strong id="purchaseBatchTotal" style="font-size:24px">$0.00</strong></div></div><div class="actions">',1)

start=s.index('function addExistingPurchaseItem(){')
end=s.index('function recordPurchase(){savePurchaseBatch()}',start)+len('function recordPurchase(){savePurchaseBatch()}')
new=r'''function addExistingPurchaseItem(){
  const id=document.getElementById("buyProduct")?.value,p=db.products.find(x=>x.id===id),qty=Math.max(1,Number(document.getElementById("buyQty")?.value||1));
  if(!p)return toast("Choose an existing inventory item");
  const market=(p.itemType==="sealed")?(p.tcgMarket!=null?Number(p.tcgMarket):null):(currentMarketFromPrices(p.tcgPrices,p.finish)||p.tcgMarket||null);
  purchaseBatchItems.push({id:uid(),existingProductId:p.id,name:p.name,qty,total:null,photo:p.photo||"",market:market!=null?Number(market):null,itemType:p.itemType||"card"});
  document.getElementById("buyQty").value=1;renderPurchaseBatch();
}
function addSelectedPurchaseItem(){
  if(!purchaseSelectedItem)return toast("Select a card or sealed product first");
  const qty=Math.max(1,Number(document.getElementById("buyNewQty")?.value||1)),sell=Math.max(0,Number(document.getElementById("buySellPrice")?.value||0));
  const item=deepClone(purchaseSelectedItem);item.id=uid();item.qty=qty;item.total=null;item.price=sell;item.market=purchaseSelectedMarket();if(item.type==="card")item.condition=document.getElementById("buyCondition")?.value||"Near Mint";
  purchaseBatchItems.push(item);purchaseSelectedItem=null;document.getElementById("buySelectedPreview").innerHTML="";document.getElementById("buyNewItemFields").classList.add("hidden");document.getElementById("buySearch").value="";renderPurchaseBatch();
}
function setPurchasePaid(id,v){
  const x=purchaseBatchItems.find(x=>x.id===id);if(!x)return;
  if(v==="")x.total=null;else x.total=Math.max(0,Number(v||0));
  updatePurchaseBatchTotals();
}
function removePurchaseBatchItem(id){purchaseBatchItems=purchaseBatchItems.filter(x=>x.id!==id);renderPurchaseBatch()}
function clearPurchaseBatch(){purchaseBatchItems=[];renderPurchaseBatch()}
function updatePurchaseBatchTotals(){
  const units=purchaseBatchItems.reduce((a,x)=>a+x.qty,0),paid=purchaseBatchItems.reduce((a,x)=>a+(x.total==null?0:Number(x.total||0)),0),market=purchaseBatchItems.reduce((a,x)=>a+(x.market==null?0:Number(x.market||0)*x.qty),0),missing=purchaseBatchItems.filter(x=>x.total==null).length;
  const count=document.getElementById("purchaseBatchCount");if(count)count.textContent=`${purchaseBatchItems.length} line${purchaseBatchItems.length===1?"":"s"} • ${units} item${units===1?"":"s"}`;
  const paidEl=document.getElementById("purchaseBatchTotal");if(paidEl)paidEl.textContent=money(paid);
  const marketEl=document.getElementById("purchaseBatchMarketTotal");if(marketEl)marketEl.textContent=money(market);
  const saveBtn=document.getElementById("savePurchaseBatchBtn");if(saveBtn){saveBtn.disabled=!purchaseBatchItems.length||missing>0;saveBtn.title=missing?`Enter paid amount for ${missing} line${missing===1?"":"s"}`:""}
}
function renderPurchaseBatch(){
  const box=document.getElementById("purchaseBatchItems");if(!box)return;
  updatePurchaseBatchTotals();
  box.innerHTML=purchaseBatchItems.length?purchaseBatchItems.map(x=>`<div class="purchaseBatchItem">${x.photo?`<img src="${esc(x.photo)}">`:`<div class="thumb"></div>`}<div><strong>${esc(x.name)}</strong><div class="small">${x.existingProductId?"Existing inventory":(x.type==="sealed"?"Sealed":`${esc(x.condition||"Near Mint")} • ${esc(prettyFinish(x.finish||""))}`)}</div><div class="small" style="margin-top:3px">Market each: <strong>${x.market!=null?money(x.market):"Unavailable"}</strong>${x.market!=null?` • Line market ${money(Number(x.market)*x.qty)}`:""}</div></div><div><div class="small">Qty</div><strong>${x.qty}</strong></div><div style="min-width:145px"><div class="small">What you paid</div><input class="input" type="number" min="0" step=".01" placeholder="Required" value="${x.total==null?"":Number(x.total).toFixed(2)}" oninput="setPurchasePaid('${x.id}',this.value)" style="padding:8px"></div><button class="miniBtn btnDanger" onclick="removePurchaseBatchItem('${x.id}')">Remove</button></div>`).join(""):'<div class="empty">No items in this batch yet.</div>';
}
function addBatchItemToInventory(x){
  const paid=Number(x.total||0);
  if(x.existingProductId){const p=db.products.find(v=>v.id===x.existingProductId);if(!p)return null;const oldQty=Number(p.qty||0),oldCost=Number(p.cost||0);p.cost=(oldQty*oldCost+paid)/(oldQty+x.qty);p.qty=oldQty+x.qty;return p}
  if(x.type==="sealed"){
    let p=db.products.find(v=>(v.itemType==="sealed")&&((x.tcgProductId&&String(v.tcgProductId)===String(x.tcgProductId))||v.name===x.name));
    if(!p){p={id:uid(),name:x.name,qty:0,cost:0,price:x.price||x.market||0,photo:x.photo||"",itemType:"sealed",condition:"Sealed",finish:"Sealed",tcgMarket:x.market,tcgUrl:x.tcgUrl||"",tcgProductId:x.tcgProductId||null,setName:x.setName||"",sealedSource:"TCGCSV",lastMarketRefresh:new Date().toISOString()};db.products.push(p)}
    const oldQty=Number(p.qty||0),oldCost=Number(p.cost||0);p.cost=(oldQty*oldCost+paid)/(oldQty+x.qty);p.qty=oldQty+x.qty;if(x.price)p.price=x.price;return p;
  }
  let p=db.products.find(v=>(v.itemType||"card")==="card"&&x.pokemonCardId&&v.pokemonCardId===x.pokemonCardId&&(v.finish||"")===(x.finish||"")&&(v.condition||"Near Mint")===(x.condition||"Near Mint"));
  if(!p){p={id:uid(),name:x.name,qty:0,cost:0,price:x.price||x.market||0,photo:x.photo||"",itemType:"card",condition:x.condition||"Near Mint",finish:x.finish||"",pokemonCardId:x.pokemonCardId||"",cardBaseName:x.cardBaseName||"",setName:x.setName||"",setId:x.setId||"",cardNumber:x.cardNumber||"",rarity:x.rarity||"",tcgUrl:x.tcgUrl||"",tcgUpdatedAt:x.tcgUpdatedAt||"",tcgPrices:x.tcgPrices||{},tcgMarket:x.market,lastMarketRefresh:new Date().toISOString()};db.products.push(p)}
  const oldQty=Number(p.qty||0),oldCost=Number(p.cost||0);p.cost=(oldQty*oldCost+paid)/(oldQty+x.qty);p.qty=oldQty+x.qty;if(x.price)p.price=x.price;return p;
}
function savePurchaseBatch(){
  if(!purchaseBatchItems.length)return toast("Add at least one item to the batch");
  const missing=purchaseBatchItems.filter(x=>x.total==null);if(missing.length)return toast(`Enter what you paid for every item before saving (${missing.length} missing)`);
  const source=document.getElementById("buySource")?.value.trim()||"Unknown seller",payment=document.getElementById("buyPayment")?.value||"Cash",note=document.getElementById("buyBatchNote")?.value.trim()||"",time=new Date().toISOString(),batchId=uid(),total=purchaseBatchItems.reduce((a,x)=>a+Number(x.total||0),0),marketTotal=purchaseBatchItems.reduce((a,x)=>a+(x.market==null?0:Number(x.market||0)*x.qty),0),units=purchaseBatchItems.reduce((a,x)=>a+x.qty,0);
  pushUndo("Record purchase batch");const saved=[];for(const x of purchaseBatchItems){const prod=addBatchItemToInventory(x);saved.push({...deepClone(x),productId:prod?.id||null})}
  db.purchases.unshift({id:batchId,batchId,isBatch:true,name:`${source} • ${purchaseBatchItems.length} line${purchaseBatchItems.length===1?"":"s"}`,qty:units,total,marketTotal,source,payment,note,time,showId:db.currentShow?.id||null,items:saved});
  purchaseBatchItems=[];document.getElementById("buySource").value="";document.getElementById("buyBatchNote").value="";save();toast("Purchase batch saved");
}
function recordPurchase(){savePurchaseBatch()}'''
s=s[:start]+new+s[end:]

s=s.replace('onclick="savePurchaseBatch()">Save purchase batch</button>','id="savePurchaseBatchBtn" onclick="savePurchaseBatch()" disabled>Save purchase batch</button>',1)
s=s.replace('const APP_VERSION="v11.23";','const APP_VERSION="v11.24";')
s=s.replace('<span id="appVersionLabel">v11.23</span>','<span id="appVersionLabel">v11.24</span>')
if '.purchaseBatchItem input.input{' not in s:
    s=s.replace('</style>','.purchaseBatchItem input.input{width:100%}.purchaseBatchSummary button:disabled{opacity:.5;cursor:not-allowed;transform:none}\n</style>',1)

for c in ['purchaseBatchMarketTotal','setPurchasePaid(id,v)','savePurchaseBatchBtn','v11.24']:
    assert c in s,c
assert 'id="buyLineTotal"' not in s
assert 'id="buyNewLineTotal"' not in s
p.write_text(s,encoding='utf-8')
