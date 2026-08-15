from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Add unified save function once.
if 'function saveInventoryChanges(id)' not in s:
    marker='function saveInventoryMoney(id){'
    i=s.index(marker)
    unified='''function saveInventoryChanges(id){
  const p=db.products.find(x=>x.id===id);if(!p)return;
  const qty=Math.max(0,Number(document.getElementById("inv_qty_"+id)?.value||0));
  const cost=Math.max(0,Number(document.getElementById("inv_cost_"+id)?.value||0));
  const price=Math.max(0,Number(document.getElementById("inv_price_"+id)?.value||0));
  pushUndo("Update inventory item");
  p.qty=qty;
  p.cost=cost;
  p.price=price;
  if((p.itemType||"card")!=="sealed"){
    const conditionEl=document.getElementById("inv_condition_"+id);
    const finishEl=document.getElementById("inv_finish_"+id);
    if(conditionEl)p.condition=conditionEl.value||"Near Mint";
    if(finishEl)p.finish=finishEl.value||p.finish||"";
    const market=currentMarketFromPrices(p.tcgPrices,p.finish);
    if(market!=null)p.tcgMarket=market;
  }
  save();toast("Changes saved");
}

'''
    s=s[:i]+unified+s[i:]

# Remove immediate save behavior from printing dropdown.
s=s.replace('id="inv_finish_${p.id}" onchange="updateInventoryCondition(\'${p.id}\')"','id="inv_finish_${p.id}"')

# Remove Qty Set button.
s=s.replace('''       <button class="miniBtn btnSuccess" onclick="setInventoryQty('${p.id}')">Set</button>\n''','')

# Remove price Save button.
s=s.replace('''       <button class="miniBtn btnSuccess" onclick="saveInventoryMoney('${p.id}')">Save</button>\n''','')

# Replace Save condition with one unified Save changes button.
s=s.replace('''     ${sealed?"":`<button class="miniBtn btnSuccess" onclick="updateInventoryCondition('${p.id}')">Save condition</button>`}\n''','''     <button class="miniBtn btnSuccess" onclick="saveInventoryChanges('${p.id}')">Save changes</button>\n''')

# Bump build.
s=s.replace('const APP_VERSION="v11.25";','const APP_VERSION="v11.26";')
s=s.replace('<span id="appVersionLabel">v11.25</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.26</span> · Updated Aug 15, 2026')

# Verification.
assert 'function saveInventoryChanges(id)' in s
assert 'Save changes</button>' in s
assert '>Set</button>' not in s[s.index('function renderInventory()'):s.index('function renderPurchases()')]
assert '>Save</button>' not in s[s.index('function renderInventory()'):s.index('function renderPurchases()')]
assert 'Save condition</button>' not in s[s.index('function renderInventory()'):s.index('function renderPurchases()')]
assert 'v11.26' in s

p.write_text(s,encoding='utf-8')
