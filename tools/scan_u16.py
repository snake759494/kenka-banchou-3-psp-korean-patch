import re,os,sys
root=sys.argv[1]
pat=re.compile(rb'(?:(?:[\x20-\x7e]\x00)|(?:[\x00-\xff][\x30\x4e-\x9f\xff\x20]))+\x00\x00',re.S)
tot=0
for dp,_,fs in os.walk(root):
  for f in fs:
    if f.endswith(('.at3','.PMF')):continue
    p=os.path.join(dp,f);d=open(p,'rb').read()
    n=0;c=0;ex=[]
    for m in pat.finditer(d):
      if m.start()%2:continue
      t=m.group()[:-2].decode('utf-16le','replace')
      if len(re.findall('[ぁ-んァ-ヶ]',t))>=1 and len(re.findall('[ぁ-んァ-ヶ一-龠ー、。！？…]',t))>=2:
        n+=1;c+=len(t);ex.append(t)
    if n: print(n,c,p.replace(root,''),ex[:2]);tot+=c
print('TOTAL',tot)
