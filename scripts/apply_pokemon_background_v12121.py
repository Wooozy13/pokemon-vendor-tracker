from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

marker = '/* VendorTracker v12.12.1 — Pokémon character background */'
css = r'''
/* VendorTracker v12.12.1 — Pokémon character background */
#app{
  background:
    linear-gradient(rgba(6,10,24,.58),rgba(6,10,24,.72)),
    url('https://images.openai.com/static-rsc-4/RRjbZjvB2YRv_n28vVHfHwZY_vkr2r-pPCZD-FsiIgGpu8rSURtpm8QRHC8XYKW6WRA7tGZ8LWTYcAbTjNG3AU_-30XVhDvXdvP6kvc7WmeritkhsMmk0Ye_5vPva56hwh4_DemLN97LgSzqTwYTnUubR3SB0Ks3FnFBIyk8GnMoHk6g9ZivThFDOR8GioI1?purpose=fullsize') center center / cover fixed no-repeat;
}
#app .appLayout,#app .main{background:transparent}
#app .panel,#app .metric,#app .productCard,#app .quickAction,#app .cartPanel{
  background:rgba(255,255,255,.92);
  backdrop-filter:blur(10px) saturate(115%);
  -webkit-backdrop-filter:blur(10px) saturate(115%);
}
#app .pageHeader h1{filter:drop-shadow(0 1px 1px rgba(255,255,255,.55))}
@media(max-width:820px){
  #app{background-attachment:scroll;background-position:center top}
  #app .panel,#app .metric,#app .productCard,#app .quickAction,#app .cartPanel{background:rgba(255,255,255,.94)}
}
'''

if marker not in text:
    text = text.replace('\n</style>', '\n' + css + '\n</style>', 1)

text = text.replace('const APP_VERSION="v12.12.0";', 'const APP_VERSION="v12.12.1";')
text = text.replace('<span id="appVersionLabel">v12.12.0</span> · Updated Aug 17, 2026', '<span id="appVersionLabel">v12.12.1</span> · Updated Aug 20, 2026')

path.write_text(text, encoding='utf-8')
