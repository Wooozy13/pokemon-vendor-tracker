from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0.2";','const APP_VERSION="v12.0.3";',1).replace('<span id="appVersionLabel">v12.0.2</span>','<span id="appVersionLabel">v12.0.3</span>',1)
old='''function runInventoryLookup(){\n  return inventoryType==="sealed"?searchSealedProducts():searchPokemonCards();\n}'''
new='''function runInventoryLookup(){\n  const input=document.getElementById("pName");\n  const submitted=input?.value||"";\n  if(!submitted.trim()) return inventoryType==="sealed"?searchSealedProducts():searchPokemonCards();\n  // Clear immediately after Find is pressed. Search functions already captured/read the submitted value synchronously.\n  const result=inventoryType==="sealed"?searchSealedProducts():searchPokemonCards();\n  if(input && input.value===submitted) input.value="";\n  return result;\n}'''
if old not in s: raise SystemExit('runInventoryLookup target not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
