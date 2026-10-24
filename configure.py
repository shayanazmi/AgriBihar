#!/usr/bin/env python3
"""Set the AI Worker address in ONE command, keeping config.js and the Content-Security-Policy in sync.
Usage:  python configure.py https://agribihar-ai.yourname.workers.dev/ask
        python configure.py --off          (switch the AI assistant off)"""
import re,sys,urllib.parse
if len(sys.argv)!=2:sys.exit(__doc__)
a=sys.argv[1]
if a=='--off':url='';origin=''
else:
    u=urllib.parse.urlparse(a)
    if u.scheme!='https' or not u.netloc or 'YOUR-WORKER' in a or u.username or u.password:sys.exit('Please give a full https:// address of your Worker, e.g. https://agribihar-ai.yourname.workers.dev/ask')
    url=a;origin=f'{u.scheme}://{u.netloc}'
cfg=open('config.js').read();cfg=re.sub(r"AI_URL:'[^']*'","AI_URL:'"+url+"'",cfg);open('config.js','w').write(cfg)
h=open('index.html').read();h2=re.sub(r"connect-src 'self'[^;\"]*",("connect-src 'self' "+origin).strip(),h,count=1)
if h2==h and origin and origin not in h:sys.exit('Could not find the connect-src rule in index.html')
open('index.html','w').write(h2);print('AI_URL =',url or '(off)');print('connect-src allows:',origin or "'self' only")
