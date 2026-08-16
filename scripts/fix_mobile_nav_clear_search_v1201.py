from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0";','const APP_VERSION="v12.0.1";',1).replace('<span id="appVersionLabel">v12.0</span>','<span id="appVersionLabel">v12.0.1</span>',1)
css=r'''
/* v12.0.1 mobile navigation fixes */
@media(max-width:820px){
 .sidebar.mobileOpen{display:block!important;position:fixed;top:60px;left:0;bottom:0;width:min(82vw,300px);height:auto;z-index:75;overflow:auto;box-shadow:18px 0 50px rgba(15,23,42,.25)}
 body.vtMenuOpen:after{content:"";position:fixed;inset:60px 0 0 0;background:rgba(15,23,42,.35);z-index:70}
 .bottomNav{overflow:hidden}.bottomNav button{background-image:none!important;background-color:transparent!important;box-shadow:none!important}
 .bottomNav button::before,.bottomNav button::after{background-image:none!important}
}
'''
s=s.replace('</style>',css+'\n</style>',1)
js=r'''
/* v12.0.1 mobile drawer + clear submitted lookup text */
function vtCloseMobileMenu(){document.querySelector('.sidebar')?.classList.remove('mobileOpen');document.body.classList.remove('vtMenuOpen')}
function vtToggleMobileMenu(){const s=document.querySelector('.sidebar');if(!s)return;s.classList.toggle('mobileOpen');document.body.classList.toggle('vtMenuOpen',s.classList.contains('mobileOpen'))}
document.addEventListener('click',e=>{if(innerWidth>820)return;const menu=e.target.closest('.menuBtn');if(menu){e.preventDefault();e.stopPropagation();vtToggleMobileMenu();return}if(e.target.closest('.sideBtn')){setTimeout(vtCloseMobileMenu,0);return}if(document.body.classList.contains('vtMenuOpen')&&!e.target.closest('.sidebar'))vtCloseMobileMenu()});
const _vtShowPage1201=showPage;showPage=function(name){const out=_vtShowPage1201(name);if(innerWidth<=820)vtCloseMobileMenu();return out};
function vtClearLookupInput(id){const el=document.getElementById(id);if(el)el.value=''}
const _vtSearchPokemonCards1201=searchPokemonCards;searchPokemonCards=async function(){const el=document.getElementById('pName');const submitted=el?.value||'';try{return await _vtSearchPokemonCards1201()}finally{if(el&&el.value===submitted)el.value=''}};
if(typeof searchSealedProducts==='function'){const _vtSearchSealed1201=searchSealedProducts;searchSealedProducts=async function(){const el=document.getElementById('sealedSearch')||document.getElementById('pName');const submitted=el?.value||'';try{return await _vtSearchSealed1201()}finally{if(el&&el.value===submitted)el.value=''}}}
if(typeof searchPurchaseItem==='function'){const _vtPurchaseSearch1201=searchPurchaseItem;searchPurchaseItem=async function(){const el=document.getElementById('buySearch');const submitted=el?.value||'';try{return await _vtPurchaseSearch1201()}finally{if(el&&el.value===submitted)el.value=''}}}
'''
if 'v12.0.1 mobile drawer' not in s:s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)
p.write_text(s,encoding='utf-8')
