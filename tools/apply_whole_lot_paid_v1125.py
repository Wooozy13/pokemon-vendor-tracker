from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Add whole-lot controls to Current Batch summary.
old = '''<div class="purchaseBatchSummary"><div style="display:flex;gap:28px;flex-wrap:wrap"><div><div class="small">Market value</div><strong id="purchaseBatchMarketTotal" style="font-size:24px">$0.00</strong></div><div><div class="small">Total paid</div><strong id="purchaseBatchTotal" style="font-size:24px">$0.00</strong></div></div><div class="actions"><button class="btn btnGhost" onclick="clearPurchaseBatch()">Clear batch</button><button class="btn btnPrimary" id="savePurchaseBatchBtn" onclick="savePurchaseBatch()" disabled>Save purchase batch</button></div></div>'''
new = '''<div class="purchaseBatchSummary" style="align-items:flex-end"><div style="display:flex;gap:28px;flex-wrap:wrap;align-items:flex-end"><div><div class="small">Market value</div><strong id="purchaseBatchMarketTotal" style="font-size:24px">$0.00</strong></div><div><div class="small">Total paid</div><strong id="purchaseBatchTotal" style="font-size:24px">$0.00</strong></div><div style="min-width:220px"><div class="small" style="margin-bottom:5px">Whole-lot paid amount</div><div style="display:flex;gap:7px"><input id="purchaseWholeLotPaid" class="input" type="number" min="0" step=".01" placeholder="e.g. 800.00"><button class="btn btnSoft" type="button" onclick="distributeWholeLotPaid()">Distribute</button></div><div class="small" style="margin-top:5px">Splits the lot cost by each line's share of market value.</div></div></div><div class="actions"><button class="btn btnGhost" onclick="clearPurchaseBatch()">Clear batch</button><button class="btn btnPrimary" id="savePurchaseBatchBtn" onclick="savePurchaseBatch()" disabled>Save purchase batch</button></div></div>'''
if old not in s:
    raise SystemExit('Current batch summary anchor not found')
s = s.replace(old, new, 1)

# Insert whole-lot distribution function before renderPurchaseBatch.
anchor = 'function renderPurchaseBatch(){'
if anchor not in s:
    raise SystemExit('renderPurchaseBatch anchor not found')
func = r'''function distributeWholeLotPaid(){
  if(!purchaseBatchItems.length)return toast("Add items to the batch first");
  const el=document.getElementById("purchaseWholeLotPaid");
  const whole=Math.max(0,Number(el?.value||0));
  if(!whole)return toast("Enter the whole-lot amount you paid");
  const marketLines=purchaseBatchItems.map(x=>Math.max(0,Number(x.market||0))*Math.max(1,Number(x.qty||1)));
  const marketTotal=marketLines.reduce((a,v)=>a+v,0);
  if(marketTotal<=0)return toast("Market pricing is required to distribute the lot cost");
  let remaining=Math.round(whole*100)/100;
  purchaseBatchItems.forEach((x,i)=>{
    let amount;
    if(i===purchaseBatchItems.length-1){
      amount=Math.round(remaining*100)/100;
    }else{
      amount=Math.round((whole*(marketLines[i]/marketTotal))*100)/100;
      remaining=Math.round((remaining-amount)*100)/100;
    }
    x.total=amount;
  });
  renderPurchaseBatch();
  toast(`Distributed ${money(whole)} across ${purchaseBatchItems.length} line${purchaseBatchItems.length===1?"":"s"}`);
}
'''
if 'function distributeWholeLotPaid(){' not in s:
    s = s.replace(anchor, func + anchor, 1)

# Clear whole-lot input when batch is cleared.
old_clear = 'function clearPurchaseBatch(){purchaseBatchItems=[];renderPurchaseBatch()}'
new_clear = 'function clearPurchaseBatch(){purchaseBatchItems=[];const w=document.getElementById("purchaseWholeLotPaid");if(w)w.value="";renderPurchaseBatch()}'
if old_clear in s:
    s = s.replace(old_clear, new_clear, 1)

# Clear whole-lot input after saving a batch.
old_save_tail = 'purchaseBatchItems=[];document.getElementById("buySource").value="";document.getElementById("buyBatchNote").value="";save();toast("Purchase batch saved");'
new_save_tail = 'purchaseBatchItems=[];document.getElementById("buySource").value="";document.getElementById("buyBatchNote").value="";const w=document.getElementById("purchaseWholeLotPaid");if(w)w.value="";save();toast("Purchase batch saved");'
if old_save_tail in s:
    s = s.replace(old_save_tail, new_save_tail, 1)

# Bump version marker.
s = re.sub(r'const APP_VERSION="v11\.24";', 'const APP_VERSION="v11.25";', s, count=1)
s = s.replace('<span id="appVersionLabel">v11.24</span>', '<span id="appVersionLabel">v11.25</span>', 1)

p.write_text(s, encoding='utf-8')
print('Applied whole-lot paid amount v11.25')
