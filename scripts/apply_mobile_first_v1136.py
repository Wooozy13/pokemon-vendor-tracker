from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.35";','const APP_VERSION="v11.36";',1)
s=s.replace('<span id="appVersionLabel">v11.35</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.36</span> · Updated Aug 15, 2026',1)

css='''
/* Mobile-first usability v11.36 */
@media(max-width:820px){
  html,body{max-width:100%;overflow-x:hidden}
  body{font-size:15px}
  .appTop{height:58px;padding:0 12px;gap:8px}
  .appTop .brand{font-size:15px}.appTop .brandMark{width:31px;height:31px;border-radius:9px}
  .syncPill{font-size:10px;padding:5px 7px;white-space:nowrap}
  .main{padding:14px 12px 94px;max-width:100%;overflow:hidden}
  .pageHeader{margin-bottom:14px;gap:6px}.pageHeader h1{font-size:25px}.pageHeader p{font-size:13px;line-height:1.45}
  .panel{margin-top:10px;padding:14px;border-radius:14px}
  .panelHead{align-items:flex-start;margin-bottom:10px}.panelHead h3{font-size:17px}
  .grid{grid-template-columns:1fr!important;gap:9px}
  .cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
  .metric{padding:12px;border-radius:12px}.metricLabel{font-size:11px}.metricValue{font-size:21px}
  .input{min-height:48px;padding:12px;font-size:16px;border-radius:11px}
  select.input{padding-right:32px}
  .btn{min-height:46px;padding:11px 14px;border-radius:11px;font-size:14px}
  .actions{display:grid;grid-template-columns:1fr;gap:8px;width:100%}.actions>.btn,.actions>button{width:100%}
  .lookupRow{display:grid!important;grid-template-columns:1fr!important;gap:8px!important}
  .lookupRow .btn{width:100%}
  .typeToggle{width:100%;max-width:none!important}.typeToggle button{min-height:44px}
  .productGrid,.purchaseLookupGrid{grid-template-columns:1fr!important;gap:10px}
  .productCard{padding:13px}
  .paymentBtns{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.paymentBtns button{min-height:48px;font-size:14px}
  .simpleDetails summary{min-height:52px;padding:2px 0}.simpleDetails .detailsContent{padding-top:10px}
  .tableWrap{overflow:visible;border:0;border-radius:0}
  table{min-width:0;width:100%}
  .purchaseBatchSummary{display:flex!important;flex-direction:column!important;align-items:stretch!important;gap:12px!important}
  .purchaseBatchSummary>div{width:100%!important}
  .purchaseBatchSummary>div:first-child{display:grid!important;grid-template-columns:1fr 1fr!important;gap:10px!important}
  .purchaseBatchSummary>div:first-child>div{min-width:0!important}
  .purchaseBatchSummary>div:first-child>div:last-child{grid-column:1/-1}
  #purchaseWholeLotPaid{min-width:0}
  .gradedCompGrid{grid-template-columns:1fr!important}
  .gradedSummary{grid-template-columns:1fr 1fr!important}
  .slabFastActions{display:grid!important;grid-template-columns:1fr!important;gap:8px!important}
  .slabFastActions .btn{width:100%}
  .bottomNav{height:72px;padding-bottom:max(6px,env(safe-area-inset-bottom));grid-template-columns:repeat(5,1fr);box-shadow:0 -8px 24px rgba(15,23,42,.08)}
  .bottomNav button{min-height:58px;padding:8px 2px;font-size:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px}
  .moreSheet{border-radius:20px 20px 0 0;padding-bottom:max(18px,env(safe-area-inset-bottom))}
  .moreSheet button{min-height:58px}
  .toast{left:12px;right:12px;bottom:86px;text-align:center}
  .undoBar{left:12px;right:12px;transform:none;bottom:86px;max-width:none}
  .paymentSetupGrid{grid-template-columns:1fr!important}.paymentSetupFields{grid-template-columns:1fr!important}
  .authMain{padding:22px 16px}.authOverlay{padding:8px}.authShell{border-radius:18px}
}
@media(max-width:560px){
  .cards{grid-template-columns:1fr 1fr}
  .main{padding-left:10px;padding-right:10px}
  .panel{padding:12px}
  .pageHeader h1{font-size:23px}
  .metricValue{font-size:19px}
  .gradedSummary{grid-template-columns:1fr!important}
  .paymentBtns{grid-template-columns:1fr 1fr}
  .purchaseBatchSummary>div:first-child{grid-template-columns:1fr!important}
  .purchaseBatchSummary>div:first-child>div:last-child{grid-column:auto}
}
@media(max-width:390px){
  .cards{grid-template-columns:1fr 1fr}
  .metric{padding:10px}.metricValue{font-size:18px}
  .appTop{padding:0 9px}.appTop .brand span:last-child{display:none}
}
'''
if '/* Mobile-first usability v11.36 */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

# Improve mobile nav labels with simple icons while preserving existing page logic.
s=s.replace('<button class="active" data-page="dashboard" onclick="go(\'dashboard\',this)">Home</button><button data-page="sell" onclick="go(\'sell\',this)">Sell</button><button data-page="inventory" onclick="go(\'inventory\',this)">Inventory</button><button data-page="purchases" onclick="go(\'purchases\',this)">Purchases</button><button id="mobileMoreBtn" onclick="toggleMoreMenu()">More</button>',
'''<button class="active" data-page="dashboard" onclick="go('dashboard',this)"><span style="font-size:19px">⌂</span><span>Home</span></button><button data-page="sell" onclick="go('sell',this)"><span style="font-size:19px">$</span><span>Sell</span></button><button data-page="inventory" onclick="go('inventory',this)"><span style="font-size:19px">▣</span><span>Inventory</span></button><button data-page="purchases" onclick="go('purchases',this)"><span style="font-size:19px">＋</span><span>Buy</span></button><button id="mobileMoreBtn" onclick="toggleMoreMenu()"><span style="font-size:19px">•••</span><span>More</span></button>''',1)

# Give the slab fast-action area a class for mobile stacking if present.
s=s.replace('<div class="actions" style="margin-top:12px">\n            <button id="ebaySlabSearchBtn"', '<div class="actions slabFastActions" style="margin-top:12px">\n            <button id="ebaySlabSearchBtn"',1)

p.write_text(s,encoding='utf-8')
