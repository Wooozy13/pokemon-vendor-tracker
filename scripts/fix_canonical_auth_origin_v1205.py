from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0.4";','const APP_VERSION="v12.0.5";',1).replace('<span id="appVersionLabel">v12.0.4</span>','<span id="appVersionLabel">v12.0.5</span>',1)
needle='<script>\nconst SUPABASE_URL='
insert='''<script>\n// Canonical origin guard v12.0.5: keep Supabase auth storage on one origin.\nif(location.hostname==="vendortracker.app"){\n  location.replace("https://www.vendortracker.app"+location.pathname+location.search+location.hash);\n}\nconst SUPABASE_URL='''
if needle not in s: raise SystemExit('Supabase script start not found')
s=s.replace(needle,insert,1)
p.write_text(s,encoding='utf-8')
