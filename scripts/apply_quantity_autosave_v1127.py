from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Inventory quantity: save as soon as the number input is committed/blurred.
old_inv = '''<input id="inv_qty_${p.id}" class="input" type="number" min="0" value="${p.qty}" style="width:82px;padding:7px">'''
new_inv = '''<input id="inv_qty_${p.id}" class="input" type="number" min="0" value="${p.qty}" style="width:82px;padding:7px" onchange="setInventoryQty('${p.id}')">'''
if old_inv in s:
    s = s.replace(old_inv, new_inv, 1)
elif 'id="inv_qty_${p.id}"' in s and 'onchange="setInventoryQty' not in s:
    raise SystemExit('Inventory qty input found but expected markup changed')

# Recent-sales quantity: use the existing editSale logic so inventory is reconciled correctly.
old_sale = '''<input class="input" style="width:80px;padding:7px" id="sale_qty_${x.id}" type="number" min="1" value="${x.qty}">'''
new_sale = '''<input class="input" style="width:80px;padding:7px" id="sale_qty_${x.id}" type="number" min="1" value="${x.qty}" onchange="editSale('${x.id}')">'''
if old_sale in s:
    s = s.replace(old_sale, new_sale, 1)
elif 'id="sale_qty_${x.id}"' in s and 'onchange="editSale' not in s:
    raise SystemExit('Sale qty input found but expected markup changed')

# Avoid creating duplicate undo/save events if quantity did not actually change.
old_fn = '''function setInventoryQty(id){
  const p=db.products.find(x=>x.id===id);if(!p)return;
  const el=document.getElementById("inv_qty_"+id);
  const qty=Math.max(0,Number(el?.value||0));
  pushUndo("Set inventory quantity");
  p.qty=qty;
  save();toast("Quantity updated");
}'''
new_fn = '''function setInventoryQty(id){
  const p=db.products.find(x=>x.id===id);if(!p)return;
  const el=document.getElementById("inv_qty_"+id);
  const qty=Math.max(0,Number(el?.value||0));
  if(qty===Number(p.qty||0))return;
  pushUndo("Set inventory quantity");
  p.qty=qty;
  save();toast("Quantity saved");
}'''
if old_fn in s:
    s = s.replace(old_fn, new_fn, 1)

# Bump visible build/version.
s = re.sub(r'const APP_VERSION="v11\.\d+";', 'const APP_VERSION="v11.27";', s, count=1)
s = re.sub(r'<span id="appVersionLabel">v11\.\d+</span>', '<span id="appVersionLabel">v11.27</span>', s, count=1)

# Verify the patch is present.
checks = [
    'onchange="setInventoryQty(\'${p.id}\')"',
    'onchange="editSale(\'${x.id}\')"',
    '<span id="appVersionLabel">v11.27</span>',
]
for check in checks:
    if check not in s:
        raise SystemExit(f'Missing expected patch: {check}')

p.write_text(s, encoding='utf-8')
