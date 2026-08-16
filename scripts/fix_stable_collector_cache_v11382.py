from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v11.38.1";','const APP_VERSION="v11.38.2";',1).replace('<span id="appVersionLabel">v11.38.1</span>','<span id="appVersionLabel">v11.38.2</span>',1)
# Add persistent exact collector cache without replacing the known-working normal Find Card flow.
needle='/* Collector-number search support v11.38.1 — leaves existing Find Card flow intact. */'
if needle in s:
    s=s.replace(needle,'/* Collector-number search support v11.38.2 — persistent exact cache + original fallback. */',1)
    s=s.replace("async function vtExactCollectorLookup(raw){\n  const c=vtCollectorParts(raw); if(!c)return [];",'''function vtCollectorCacheKey(raw){const c=vtCollectorParts(raw);return c?`vt_collector_${c.printed}`:null}\nfunction vtReadCollectorCache(raw){try{const k=vtCollectorCacheKey(raw);if(!k)return[];const v=JSON.parse(localStorage.getItem(k)||'[]');return Array.isArray(v)?v:[]}catch(e){return[]}}\nfunction vtWriteCollectorCache(raw,cards){try{const k=vtCollectorCacheKey(raw);if(k&&Array.isArray(cards)&&cards.length)localStorage.setItem(k,JSON.stringify(cards.slice(0,20)))}catch(e){}}\nasync function vtExactCollectorLookup(raw){\n  const c=vtCollectorParts(raw); if(!c)return [];\n  const saved=vtReadCollectorCache(raw);if(saved.length)return saved;''',1)
    s=s.replace("if(exact.length)return exact;", "if(exact.length){vtWriteCollectorCache(raw,exact);return exact;}",1)
    # Cache any exact collector result discovered by the normal flow too.
    s=s.replace("currentLookupResults=exact;renderCardLookup(exact);", "vtWriteCollectorCache(raw,exact);currentLookupResults=exact;renderCardLookup(exact);",1)
# Seed the reported GG56/GG70 card with a tiny reliable identity record only if API/cache is unavailable.
seed=r'''
const VT_COLLECTOR_SEEDS={
 'GG56/GG70':{id:'swsh12pt5gg-GG56',name:'Hisuian Zoroark VSTAR',number:'GG56',set:{name:'Crown Zenith: Galarian Gallery',printedTotal:70},images:{small:'https://images.pokemontcg.io/swsh12pt5gg/GG56.png',large:'https://images.pokemontcg.io/swsh12pt5gg/GG56_hires.png'}}
};
const _vtExactCollectorLookupStable=vtExactCollectorLookup;
vtExactCollectorLookup=async function(raw){const cached=vtReadCollectorCache(raw);if(cached.length)return cached;const found=await _vtExactCollectorLookupStable(raw);if(found.length)return found;const c=vtCollectorParts(raw);const seed=c&&VT_COLLECTOR_SEEDS[c.printed];if(seed){vtWriteCollectorCache(raw,[seed]);return[seed]}return[]};
'''
if 'VT_COLLECTOR_SEEDS' not in s:s=s.replace('function renderDashboard(){',seed+'\nfunction renderDashboard(){',1)
p.write_text(s,encoding='utf-8')
