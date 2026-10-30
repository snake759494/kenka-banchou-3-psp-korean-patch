import re,os,sys
pat=re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]){4,}')
pat16=re.compile(rb'(?:[\x41-\x93\xa1-\xf3]\x30|[\x00-\x7f]\x4e|[\x00-\xff][\x4e-\x9f]){0}')
root=sys.argv[1]
for dp,_,fs in os.walk(root):
  for f in fs:
    p=os.path.join(dp,f);d=open(p,'rb').read()
    n=0;ex=[]
    for m in pat.finditer(d):
      try:t=m.group().decode('cp932')
      except:continue
      if re.search('[ぁ-ん]',t): n+=1; ex.append(t)
    # utf16
    u=0
    for m in re.finditer(rb'(?:[\x41-\x93]\x30){3,}',d): u+=1
    if n or u: print(n,u,p.replace(root,''),ex[:2])
