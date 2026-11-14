import glob,re,json
rho=1141.83; out={}
for c in ('h1','h07'):
    rows=[]
    for d in glob.glob(f'{c}/postProcessing/z*'):
        if d.endswith('q'): continue
        z=float(d.split('/z')[-1].replace('_','.'))
        f=sorted(glob.glob(d+'/*/*.dat'))[-1]; L=[l for l in open(f) if l[0]!='#'][-1].split()
        rows.append([z,round(float(L[1])*rho)])
    out[c]=sorted(rows)
json.dump(out,open('planes.json','w')); print(out['h07'])
