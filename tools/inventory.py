import os,sys,re,struct,json
sys.path.insert(0,os.path.dirname(__file__))
from zar import parse_zar
R='work/iso/PSP_GAME/USRDIR/DATA'
zstats={};bad=[]
allz={}
for dp,_,fs in os.walk(R):
  for f in fs:
    if f.endswith(('.at3','.PMF')):continue
    p=os.path.join(dp,f);d=open(p,'rb').read()
    for m in re.finditer(b'ZAR\0PSP\0',d):
      try:
        n,idx,s=parse_zar(d[m.start():])
        allz[(p[len(R)+1:],m.start())]=s
      except Exception as e: bad.append((p,m.start(),str(e)))
tot=sum(len(t) for v in allz.values() for _,_,t in v)
uniq=set(t for v in allz.values() for _,_,t in v)
print('zar',len(allz),'strings',sum(len(v) for v in allz.values()),'chars',tot,'uniq',len(uniq),sum(len(t) for t in uniq))
print('bad',len(bad),bad[:5])
json.dump({f'{k[0]}@{k[1]:x}':[t for _,_,t in v] for k,v in allz.items()},open('work/zar_all.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
