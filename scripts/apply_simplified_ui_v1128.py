from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Version
s=re.sub(r'const APP_VERSION="[^"]+";', 'const APP_VERSION="v11.28";', s, count=1)
s=s.replace('id="appVersionLabel">v11.27</span>', 'id="appVersionLabel">v11.28</span>', 1)

# Sidebar: keep common jobs front-and-center, move occasional tools under More.
old_sidebar='''    <aside id="sidebar" class="sidebar"><nav class="sideNav">
      <button class="sideBtn active" data-page="dashboard" onclick="go('dashboard',this)">Dashboard</button>
      <button class="sideBtn" data-page="sell" onclick="go('sell',this)">Sell</button>
      <button class="sideBtn" data-page="inventory" onclick="go('inventory',this)">Inventory</button>
      <button class="sideBtn" data-page="purchases" onclick="go('purchases',this)">Purchases</button>
      <button class="sideBtn" data-page="expenses" onclick="go('expenses',this)">Expenses</button>
      <button class="sideBtn" data-page="shows" onclick="go('shows',this)">Shows</button>
      <button class="sideBtn" data-page="settings" onclick="go('settings',this)">Settings</button>
    </nav></aside>'''
new_sidebar='''    <aside id="sidebar" class="sidebar"><nav class="sideNav simpleSideNav">
      <div class="navLabel">MAIN</div>
      <button class="sideBtn active" data-page="dashboard" onclick="go('dashboard',this)">⌂ <span>Home</span></button>
      <button class="sideBtn" data-page="sell" onclick="go('sell',this)">＄ <span>Sell</span></button>
      <button class="sideBtn" data-page="inventory" onclick="go('inventory',this)">▣ <span>Inventory</span></button>
      <button class="sideBtn" data-page="purchases" onclick="go('purchases',this)">＋ <span>Purchases</span></button>
      <div class="navLabel navLabelMore">MORE</div>
      <button class="sideBtn secondarySide" data-page="shows" onclick="go('shows',this)">★ <span>Shows</span></button>
      <button class="sideBtn secondarySide" data-page="expenses" onclick="go('expenses',this)">⌁ <span>Expenses</span></button>
      <button class="sideBtn secondarySide" data-page="settings" onclick="go('settings',this)">⚙ <span>Settings</span></button>
    </nav></aside>'''
assert old_sidebar in s, 'sidebar block not found'
s=s.replace(old_sidebar,new_sidebar,1)

# Dashboard: simple quick actions and less visual noise.
s=s.replace('''        <div class="pageHeader"><div><h1>Dashboard</h1><p>Your sales, profit and inventory at a glance.</p></div></div>
        <div id="dashCards" class="cards"></div>''','''        <div class="pageHeader"><div><h1>Home</h1><p>The important stuff first. Everything else is still available when you need it.</p></div></div>
        <div class="quickActions">
          <button class="quickAction primary" onclick="go('sell')"><span>＄</span><div><strong>Start selling</strong><small>Open cart & checkout</small></div></button>
          <button class="quickAction" onclick="go('inventory')"><span>＋</span><div><strong>Add inventory</strong><small>Cards or sealed</small></div></button>
          <button class="quickAction" onclick="go('purchases')"><span>⇩</span><div><strong>Record purchase</strong><small>Build a purchase batch</small></div></button>
        </div>
        <div id="dashCards" class="cards simpleDashCards"></div>''',1)

# Recent sales becomes expandable instead of always filling the home screen.
s=s.replace('''        <div class="panel">
          <div class="panelHead"><div><h3>Recent sales</h3><div class="small">Edit quantity, total or payment. Inventory adjusts automatically.</div></div></div>
          <div id="recentSales"></div>
        </div>''','''        <details class="panel simpleDetails">
          <summary><span><strong>Recent sales</strong><small>View or edit recent transactions</small></span><span class="chev">⌄</span></summary>
          <div id="recentSales" class="detailsContent"></div>
        </details>''',1)

# Inventory add form collapses by default. Inventory list remains the main screen.
inv_start='''        <div class="panel">
          <div class="grid">
            <div style="grid-column:span 2">'''
inv_new='''        <details class="panel simpleDetails inventoryAddDetails">
          <summary><span><strong>＋ Add inventory item</strong><small>Search a card, sealed product, or scan photos</small></span><span class="chev">⌄</span></summary>
          <div class="detailsContent"><div class="grid">
            <div style="grid-column:span 2">'''
idx=s.find('<section id="inventory"')
assert idx!=-1, 'inventory section not found'
pos=s.find(inv_start,idx)
assert pos!=-1, 'inventory add panel start not found'
s=s[:pos]+s[pos:].replace(inv_start,inv_new,1)
inv_end='''            <button class="btn btnPrimary" onclick="addProduct()">Add / update product</button>
          </div>
        </div>
        <div class="panel"><div id="inventoryTable"></div></div>'''
inv_end_new='''            <button class="btn btnPrimary" onclick="addProduct()">Add / update product</button>
          </div></div>
        </details>
        <div class="panel inventoryListPanel"><div class="panelHead"><div><h3>Your inventory</h3><div class="small">Tap an item to edit only when you need to.</div></div></div><div id="inventoryTable"></div></div>'''
assert inv_end in s, 'inventory panel end not found'
s=s.replace(inv_end,inv_end_new,1)

# Purchases: label the workflow as three obvious steps; history is collapsed.
s=s.replace('<div class="panelHead"><div><h3>Purchase batch details</h3><div class="small">These details apply to every item in this lot.</div></div></div>',
'''<div class="panelHead"><div class="stepHead"><span class="stepNum">1</span><div><h3>Who are you buying from?</h3><div class="small">Seller, payment method, and optional note.</div></div></div></div>''',1)
s=s.replace('<div class="panelHead"><div><h3>Add an item</h3><div class="small">Restock an existing item or search a new card/sealed product.</div></div></div>',
'''<div class="panelHead"><div class="stepHead"><span class="stepNum">2</span><div><h3>Add items</h3><div class="small">Search cards/sealed or choose something already in inventory.</div></div></div></div>''',1)
s=s.replace('<div class="panelHead"><div><h3>Current batch</h3><div class="small">Add everything at market value first, then enter what you actually paid for each line before saving.</div></div><span id="purchaseBatchCount" class="small">0 items</span></div>',
'''<div class="panelHead"><div class="stepHead"><span class="stepNum">3</span><div><h3>Review & save</h3><div class="small">Check market value, enter what you paid, then save the batch.</div></div></div><span id="purchaseBatchCount" class="small">0 items</span></div>''',1)
s=s.replace('''        <div class="panel"><div class="panelHead"><h3>Purchase history</h3></div><div id="purchaseTable"></div></div>''','''        <details class="panel simpleDetails"><summary><span><strong>Purchase history</strong><small>Past single purchases and batches</small></span><span class="chev">⌄</span></summary><div id="purchaseTable" class="detailsContent"></div></details>''',1)

# Mobile bottom navigation: More opens a compact menu rather than exposing another full page.
old_bottom='''  <nav class="bottomNav">
    <button class="active" data-page="dashboard" onclick="go('dashboard',this)">Dashboard</button><button data-page="sell" onclick="go('sell',this)">Sell</button><button data-page="inventory" onclick="go('inventory',this)">Inventory</button><button data-page="purchases" onclick="go('purchases',this)">Purchases</button><button data-page="shows" onclick="go('shows',this)">Shows</button>
  </nav>'''
new_bottom='''  <nav class="bottomNav simpleBottomNav">
    <button class="active" data-page="dashboard" onclick="go('dashboard',this)">Home</button><button data-page="sell" onclick="go('sell',this)">Sell</button><button data-page="inventory" onclick="go('inventory',this)">Inventory</button><button data-page="purchases" onclick="go('purchases',this)">Purchases</button><button id="mobileMoreBtn" onclick="toggleMoreMenu()">More</button>
  </nav>
  <div id="moreMenu" class="moreMenu hidden" onclick="if(event.target===this)toggleMoreMenu(false)">
    <div class="moreSheet">
      <div class="moreHandle"></div><div class="moreTitle">More</div>
      <button onclick="openMorePage('shows')"><span>★</span><div><strong>Shows</strong><small>Event history & profit</small></div></button>
      <button onclick="openMorePage('expenses')"><span>⌁</span><div><strong>Expenses</strong><small>Fees, travel & costs</small></div></button>
      <button onclick="openMorePage('settings')"><span>⚙</span><div><strong>Settings</strong><small>Account, backups & version</small></div></button>
      <button class="moreCancel" onclick="toggleMoreMenu(false)">Cancel</button>
    </div>
  </div>'''
assert old_bottom in s, 'bottom nav not found'
s=s.replace(old_bottom,new_bottom,1)

# Simplify dashboard metrics to the four most useful numbers.
old_metrics=''' document.getElementById("dashCards").innerHTML=[
   ["Total sales",money(revenue)],
   ["Gross profit",money(revenue-cogs)],
   ["Cash",money(pay("Cash"))],
   ["Cash App",money(pay("Cash App"))],
   ["Zelle",money(pay("Zelle"))],
   ["Venmo",money(pay("Venmo"))],
   ["Apple Pay",money(pay("Apple Pay"))],
   ["Card",money(pay("Card"))],
   ["Inventory cost",money(inv)]
 ].map(x=>`<div class="metric"><div class="metricLabel">${x[0]}</div><div class="metricValue money">${x[1]}</div></div>`).join("");'''
new_metrics=''' document.getElementById("dashCards").innerHTML=[
   ["Sales",money(revenue)],
   ["Gross profit",money(revenue-cogs)],
   ["Inventory cost",money(inv)],
   ["Expenses",money(expenses)]
 ].map(x=>`<div class="metric"><div class="metricLabel">${x[0]}</div><div class="metricValue money">${x[1]}</div></div>`).join("");'''
assert old_metrics in s, 'dashboard metrics block not found'
s=s.replace(old_metrics,new_metrics,1)

# go() should work cleanly for quick-action calls that don't pass a button.
# Add More menu helpers before startShow.
anchor='''function startShow(){'''
helpers='''function toggleMoreMenu(force){
 const m=document.getElementById("moreMenu");if(!m)return;
 const show=force===undefined?m.classList.contains("hidden"):!!force;
 m.classList.toggle("hidden",!show);
 document.body.classList.toggle("moreMenuOpen",show);
}
function openMorePage(id){toggleMoreMenu(false);go(id)}

function startShow(){'''
assert anchor in s, 'startShow anchor not found'
s=s.replace(anchor,helpers,1)

# Add simplified UI styles before closing style tag.
css='''
/* Simplified navigation v11.28 */
.navLabel{font-size:10px;font-weight:900;letter-spacing:.12em;color:#64748b;padding:8px 12px 5px}.navLabelMore{margin-top:14px}.simpleSideNav .sideBtn{display:flex;align-items:center;gap:10px;font-size:14px}.simpleSideNav .sideBtn span{display:inline}.secondarySide{color:#94a3b8}
.quickActions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:16px}.quickAction{border:1px solid var(--line);background:#fff;border-radius:16px;padding:16px;text-align:left;display:flex;align-items:center;gap:12px;box-shadow:0 4px 14px rgba(15,23,42,.03)}.quickAction>span{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:#eff6ff;color:#1d4ed8;font-size:20px;font-weight:900}.quickAction strong,.quickAction small{display:block}.quickAction small{color:var(--muted);margin-top:2px}.quickAction.primary{background:#0f172a;color:#fff;border-color:#0f172a}.quickAction.primary>span{background:#fff;color:#0f172a}.quickAction.primary small{color:#cbd5e1}
.simpleDashCards{grid-template-columns:repeat(4,minmax(0,1fr))}.simpleDetails{padding:0;overflow:hidden}.simpleDetails>summary{list-style:none;cursor:pointer;padding:17px 18px;display:flex;align-items:center;justify-content:space-between;gap:12px}.simpleDetails>summary::-webkit-details-marker{display:none}.simpleDetails>summary span:first-child{display:flex;flex-direction:column;gap:3px}.simpleDetails>summary small{color:var(--muted);font-size:12px;font-weight:500}.simpleDetails .chev{font-size:20px;color:#64748b;transition:.18s}.simpleDetails[open] .chev{transform:rotate(180deg)}.simpleDetails .detailsContent{padding:0 18px 18px}.inventoryAddDetails{margin-bottom:16px}.inventoryListPanel{margin-top:0}
.stepHead{display:flex;align-items:center;gap:10px}.stepNum{width:30px;height:30px;border-radius:50%;background:#0f172a;color:#fff;display:grid;place-items:center;font-size:13px;font-weight:900;flex:0 0 auto}.stepHead h3{margin:0}.stepHead .small{margin-top:2px}
.moreMenu{position:fixed;inset:0;background:rgba(15,23,42,.38);z-index:120;display:flex;align-items:flex-end;justify-content:center}.moreSheet{background:#fff;width:min(520px,100%);border-radius:22px 22px 0 0;padding:10px 14px calc(14px + env(safe-area-inset-bottom));box-shadow:0 -20px 55px rgba(15,23,42,.22)}.moreHandle{width:42px;height:4px;background:#cbd5e1;border-radius:99px;margin:2px auto 12px}.moreTitle{font-size:19px;font-weight:900;padding:0 5px 8px}.moreSheet>button{width:100%;border:0;background:#fff;border-bottom:1px solid #eef2f7;padding:13px 8px;display:flex;gap:12px;align-items:center;text-align:left}.moreSheet>button>span{width:36px;height:36px;border-radius:10px;background:#f1f5f9;display:grid;place-items:center;font-size:18px}.moreSheet>button strong,.moreSheet>button small{display:block}.moreSheet>button small{color:var(--muted);margin-top:2px}.moreSheet .moreCancel{justify-content:center;border:0;margin-top:7px;font-weight:850;color:#475569;background:#f8fafc;border-radius:10px}.moreMenuOpen{overflow:hidden}
@media(max-width:1050px){.simpleDashCards{grid-template-columns:repeat(2,1fr)}}
@media(max-width:820px){.quickActions{grid-template-columns:1fr}.quickAction{padding:13px}.simpleDashCards{grid-template-columns:repeat(2,1fr)!important}.simpleBottomNav button[data-page="dashboard"]::before{content:"⌂"}.simpleBottomNav button[data-page="sell"]::before{content:"$"}.simpleBottomNav button[data-page="inventory"]::before{content:"▣"}.simpleBottomNav button[data-page="purchases"]::before{content:"+"}.simpleBottomNav #mobileMoreBtn::before{content:"•••"}.pageHeader h1{font-size:27px}.panel{border-radius:14px}.main{padding-top:16px}.inventoryAddDetails>summary{padding:15px}.purchaseLookupGrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:821px){.moreMenu{display:none!important}}
'''
assert '</style>' in s
s=s.replace('</style>',css+'\n</style>',1)

# Verification tokens
required=['v11.28','backup-v11.27-before-ui-simplify' if False else 'quickActions','moreMenu','Add inventory item','Purchase history','openMorePage','simpleDashCards']
for token in required:
    assert token in s, token

p.write_text(s,encoding='utf-8')
