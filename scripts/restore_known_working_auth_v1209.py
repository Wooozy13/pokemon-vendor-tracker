from pathlib import Path
import subprocess,re
p=Path('index.html'); cur=p.read_text(encoding='utf-8')
old=subprocess.check_output(['git','show','b72f87a3f8df790ceae7ef8180dec8ac009675cf:index.html'],text=True)
# Restore the exact Supabase client initialization used by the last known build before the refresh/logout regression.
def client_block(s):
 m=re.search(r'const SUPABASE_URL=.*?\nconst LOCAL_PREFIX=',s,re.S)
 if not m: raise SystemExit('Supabase client block not found')
 return m.group(0)
cur=re.sub(r'// Canonical origin guard v12\.0\.5:.*?\nconst LOCAL_PREFIX=',client_block(old),cur,count=1,flags=re.S)
# Restore exact auth startup/sign-in/sign-out block from known-working build, while leaving v12 UI/features untouched.
def auth_block(s):
 a=s.index('async function init(){')
 b=s.index('async function enterApp(){',a)
 return s[a:b]
cur_a=cur.index('async function init(){');cur_b=cur.index('async function enterApp(){',cur_a)
cur=cur[:cur_a]+auth_block(old)+cur[cur_b:]
cur=cur.replace('const APP_VERSION="v12.0.8";','const APP_VERSION="v12.0.9";',1)
cur=cur.replace('<span id="appVersionLabel">v12.0.8</span>','<span id="appVersionLabel">v12.0.9</span>',1)
# Remove leftover v12 auth diagnostic hooks if present; they are not part of the known-working flow.
cur=re.sub(r'/\* v12\.0\.8 auth diagnostic.*?\*/.*?(?=\n(?:function|async function|const|let) )','',cur,flags=re.S)
p.write_text(cur,encoding='utf-8')
