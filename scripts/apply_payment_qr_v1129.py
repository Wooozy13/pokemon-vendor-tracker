from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Version
s=s.replace('const APP_VERSION="v11.28";','const APP_VERSION="v11.29";')
s=s.replace('<span id="appVersionLabel">v11.28</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.29</span> · Updated Aug 15, 2026')

# Styles
css='''
/* Payment setup + customer QR */
.paymentSetupGrid{display:grid;gap:12px;margin-top:12px}.paymentSetupCard{border:1px solid var(--line);border-radius:14px;padding:14px;background:#fff}.paymentSetupHead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}.paymentSetupFields{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) auto;gap:8px;align-items:end}.paymentQrPreview{width:76px;height:76px;object-fit:contain;border:1px solid var(--line);border-radius:10px;background:#f8fafc}.payQrModal .modal{width:min(470px,100%)}.customerPayBox{text-align:center;padding:6px}.customerPayAmount{font-size:36px;font-weight:950;letter-spacing:-.04em;margin:6px 0 14px}.customerQr{width:min(280px,80vw);height:min(280px,80vw);object-fit:contain;border:1px solid var(--line);border-radius:18px;background:#fff;padding:10px;margin:0 auto 12px;display:block}.customerPayHandle{font-weight:850;font-size:18px;margin-top:8px}.customerPayLink{display:inline-flex;margin-top:8px}.paymentConfirmActions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:18px}@media(max-width:700px){.paymentSetupFields{grid-template-columns:1fr}.paymentQrPreview{width:90px;height:90px}.customerPayAmount{font-size:32px}}
'''
if '/* Payment setup + customer QR */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

# Settings payment setup panel
anchor='''          <div class="detailsBox" id="buildInfoBox">'''
panel='''          <div class="detailsBox">
            <div class="panelHead"><div><strong>Payment setup</strong><div class="small">Save your own payment info once. Vendor Mode can show it to customers at checkout.</div></div></div>
            <div class="paymentSetupGrid">
              <div class="paymentSetupCard">
                <div class="paymentSetupHead"><strong>Cash App</strong><span class="small">Personal QR / $Cashtag</span></div>
                <div class="paymentSetupFields"><input id="pay_cashapp_handle" class="input" placeholder="$Cashtag or display name"><input id="pay_cashapp_link" class="input" placeholder="Payment/profile link (optional)"><label class="btn btnGhost" style="text-align:center">Upload QR<input id="pay_cashapp_qr" type="file" accept="image/*" style="display:none" onchange="setPaymentQr('cashapp',this)"></label></div>
                <img id="pay_cashapp_preview" class="paymentQrPreview hidden" alt="Cash App QR" style="margin-top:10px">
              </div>
              <div class="paymentSetupCard">
                <div class="paymentSetupHead"><strong>Venmo</strong><span class="small">Username / personal QR</span></div>
                <div class="paymentSetupFields"><input id="pay_venmo_handle" class="input" placeholder="@username or display name"><input id="pay_venmo_link" class="input" placeholder="Payment/profile link (optional)"><label class="btn btnGhost" style="text-align:center">Upload QR<input id="pay_venmo_qr" type="file" accept="image/*" style="display:none" onchange="setPaymentQr('venmo',this)"></label></div>
                <img id="pay_venmo_preview" class="paymentQrPreview hidden" alt="Venmo QR" style="margin-top:10px">
              </div>
              <div class="paymentSetupCard">
                <div class="paymentSetupHead"><strong>Zelle</strong><span class="small">Bank/Zelle QR recommended</span></div>
                <div class="paymentSetupFields"><input id="pay_zelle_handle" class="input" placeholder="Name / phone / email label"><input id="pay_zelle_link" class="input" placeholder="Optional note or link"><label class="btn btnGhost" style="text-align:center">Upload QR<input id="pay_zelle_qr" type="file" accept="image/*" style="display:none" onchange="setPaymentQr('zelle',this)"></label></div>
                <img id="pay_zelle_preview" class="paymentQrPreview hidden" alt="Zelle QR" style="margin-top:10px">
              </div>
            </div>
            <div class="actions" style="margin-top:12px"><button class="btn btnPrimary" onclick="savePaymentSetup()">Save payment setup</button></div>
          </div>
'''
if 'id="pay_cashapp_handle"' not in s:
    s=s.replace(anchor,panel+anchor,1)

# Payment modal before undo bar
modal='''
<div id="customerPaymentModal" class="modalBack hidden payQrModal">
  <div class="modal">
    <div class="modalHead"><div><h2 id="customerPayTitle">Customer payment</h2><div class="small">Have the customer scan or open your saved payment option.</div></div><button class="btn btnGhost" onclick="cancelPendingPayment()">Close</button></div>
    <div class="modalBody customerPayBox">
      <div class="small">Amount due</div><div id="customerPayAmount" class="customerPayAmount">$0.00</div>
      <img id="customerPayQr" class="customerQr hidden" alt="Payment QR code">
      <div id="customerPayHandle" class="customerPayHandle"></div>
      <a id="customerPayLink" class="btn btnSoft customerPayLink hidden" href="#" target="_blank" rel="noopener">Open payment app/profile ↗</a>
      <div id="customerPayNoSetup" class="small hidden" style="margin-top:12px">No QR or payment details are saved for this option yet. Add them in Settings → Payment setup.</div>
      <div class="paymentConfirmActions"><button class="btn btnGhost" onclick="cancelPendingPayment()">Cancel</button><button class="btn btnPrimary" onclick="confirmPendingPayment()">Payment received</button></div>
    </div>
  </div>
</div>
'''
if 'id="customerPaymentModal"' not in s:
    s=s.replace('<div id="undoBar"',modal+'\n<div id="undoBar"',1)

# DB default payment setup
s=s.replace('function blankDB(){return {products:[],sales:[],purchases:[],expenses:[],shows:[],currentShow:null}}',
'''function blankDB(){return {products:[],sales:[],purchases:[],expenses:[],shows:[],currentShow:null,paymentSetup:{}}}''')

# Globals
if 'let pendingCheckoutPayment=null;' not in s:
    s=s.replace('let saleCart=[];','let saleCart=[];\nlet pendingCheckoutPayment=null;',1)

# Checkout buttons use requestCheckout
for method in ['Cash','Cash App','Zelle','Venmo','Apple Pay','Card']:
    s=s.replace(f'onclick="checkoutCart(\'{method}\')"',f'onclick="requestCheckout(\'{method}\')"')

# Rename existing checkoutCart function to finalizeCheckout
s=s.replace('function checkoutCart(payment){','function finalizeCheckout(payment){',1)

# Payment functions before finalizeCheckout
marker='function finalizeCheckout(payment){'
funcs=r'''function ensurePaymentSetup(){
  if(!db.paymentSetup || typeof db.paymentSetup!=="object")db.paymentSetup={};
  ["cashapp","venmo","zelle"].forEach(k=>{if(!db.paymentSetup[k])db.paymentSetup[k]={handle:"",link:"",qr:""}});
  return db.paymentSetup;
}
function paymentKeyFromName(name){return ({"Cash App":"cashapp","Venmo":"venmo","Zelle":"zelle"})[name]||""}
function loadPaymentSetupForm(){
  const setup=ensurePaymentSetup();
  ["cashapp","venmo","zelle"].forEach(k=>{
    const x=setup[k]||{};
    const h=document.getElementById(`pay_${k}_handle`),l=document.getElementById(`pay_${k}_link`),img=document.getElementById(`pay_${k}_preview`);
    if(h)h.value=x.handle||"";if(l)l.value=x.link||"";
    if(img){if(x.qr){img.src=x.qr;img.classList.remove("hidden")}else{img.src="";img.classList.add("hidden")}}
  });
}
async function setPaymentQr(key,input){
  const file=input?.files?.[0];if(!file)return;
  try{
    const data=await dataUrlFromFile(file);ensurePaymentSetup();db.paymentSetup[key].qr=data;
    const img=document.getElementById(`pay_${key}_preview`);if(img){img.src=data;img.classList.remove("hidden")}
    toast("QR loaded — press Save payment setup");
  }catch(e){toast("Could not read QR image")}
}
function savePaymentSetup(){
  const setup=ensurePaymentSetup();
  ["cashapp","venmo","zelle"].forEach(k=>{
    setup[k].handle=document.getElementById(`pay_${k}_handle`)?.value.trim()||"";
    setup[k].link=document.getElementById(`pay_${k}_link`)?.value.trim()||"";
  });
  pushUndo("Update payment setup");save();toast("Payment setup saved");
}
function requestCheckout(payment){
  if(!saleCart.length)return toast("Cart is empty");
  const key=paymentKeyFromName(payment);
  if(!key)return finalizeCheckout(payment);
  const subtotal=cartSubtotal(),discountPct=cartDiscount(),grand=Math.max(0,subtotal-subtotal*(discountPct/100));
  const setup=ensurePaymentSetup()[key]||{};
  pendingCheckoutPayment=payment;
  const modal=document.getElementById("customerPaymentModal"),qr=document.getElementById("customerPayQr"),handle=document.getElementById("customerPayHandle"),link=document.getElementById("customerPayLink"),none=document.getElementById("customerPayNoSetup");
  document.getElementById("customerPayTitle").textContent=payment;
  document.getElementById("customerPayAmount").textContent=money(grand);
  if(setup.qr){qr.src=setup.qr;qr.classList.remove("hidden")}else{qr.src="";qr.classList.add("hidden")}
  handle.textContent=setup.handle||"";
  if(setup.link && /^https?:\/\//i.test(setup.link)){link.href=setup.link;link.classList.remove("hidden")}else{link.href="#";link.classList.add("hidden")}
  none.classList.toggle("hidden",!!(setup.qr||setup.handle||setup.link));
  modal.classList.remove("hidden");
}
function cancelPendingPayment(){pendingCheckoutPayment=null;document.getElementById("customerPaymentModal")?.classList.add("hidden")}
function confirmPendingPayment(){
  const payment=pendingCheckoutPayment;if(!payment)return;
  document.getElementById("customerPaymentModal")?.classList.add("hidden");pendingCheckoutPayment=null;finalizeCheckout(payment);
}
'''
if 'function ensurePaymentSetup()' not in s:
    s=s.replace(marker,funcs+'\n'+marker,1)

# Load setup whenever app renders/settings opens; renderAll safe hook
s=s.replace('renderDashboard();renderSaleProducts();renderCart();renderInventory();renderPurchases();renderExpenses();renderShows();',
'''renderDashboard();renderSaleProducts();renderCart();renderInventory();renderPurchases();renderExpenses();renderShows();loadPaymentSetupForm();''',1)

p.write_text(s,encoding='utf-8')
