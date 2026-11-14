import glob,statistics as st,json,re,sys
rho=1141.83; nu=1.71e-7; mdot=0.28; A_line=3.14159265*0.011**2; U=mdot/rho/A_line; q=0.5*rho*U**2
psat=101348.2; dpsdT=10598.2   # CoolProp, LOX 90.19 K
def win(c,lo,hi):
    a=[l.split() for l in open(glob.glob(f'{c}/postProcessing/pIn/*/*.dat')[0]) if l[0]!='#']
    b=[l.split() for l in open(glob.glob(f'{c}/postProcessing/pOut/*/*.dat')[0]) if l[0]!='#']
    v=[(float(x[1])-float(y[1]))*rho for x,y in zip(a,b) if lo<=float(x[0])<hi]
    return st.mean(v),st.pstdev(v)
def pmin(c):
    f=sorted(glob.glob(f'{c}/postProcessing/mm/*/fieldMinMax.dat'))[-1]
    L=[l for l in open(f) if '\tp ' in l or l.split()[1:2]==['p']][-1].split('\t')
    return float(L[2])*rho, L[3].strip()
out={}
for c,lo,hi in (('h1',2000,4001),('h1',1500,2168),('h07',1500,2168)):
    try: m,s=win(c,lo,hi)
    except Exception as e: continue
    r={'cells':{'h1':1038573,'h07':2915966}[c],'dp_Pa':round(m),'dp_sd_Pa':round(s),'window':[lo,hi-1]}
    try:
        pm,loc=pmin(c); r['p_min_rel_outlet_Pa']=round(pm); r['p_min_loc_m']=loc
        r['p_min_below_inlet_Pa']=round(m-pm); r['subcooling_needed_K']=round((m-pm)/dpsdT,2)
    except Exception as e: r['p_min']='not post-processed'
    r['K_line_head']=round(m/q,2)
    Qgpm=mdot/rho*15850.3; r['Cv_equiv']=round(Qgpm*((rho/999.0)/(m/6894.76))**0.5,2)
    out[f'{c}_{lo}_{hi-1}']=r
out['inputs']={'mdot_kg_s':mdot,'T_K':90.19,'p_bar':4.0,'rho':rho,'nu':nu,'U_line_m_s':round(U,4),'q_line_Pa':round(q,1),
 'turbulence':'k-omega SST, wall functions, steady simpleFoam','psat_90K_Pa':psat,'dpsat_dT_Pa_K':dpsdT}
out['volumes_cm3']={'coupling_wetted':202.3,'B_outer_pocket_r_gt_19mm':117.1,'A_side_port':2.59}
out['springs_hand_Pa']=12
a=out['h1_1500_2167']['dp_Pa']; b=out['h07_1500_2167']['dp_Pa']; r=(2915966/1038573)**(1/3)
out['mesh_study']={'refinement_ratio':round(r,3),'diff_pct':round(100*(a-b)/b,1),
 'richardson_p2_Pa':round(b+(b-a)/(r**2-1)),'richardson_p1_Pa':round(b+(b-a)/(r-1)),
 'note':'h07 stopped at iteration 2167 (session moved host); both meshes compared on the same 1500-2167 window'}
json.dump(out,open('results.json','w'),indent=1); print(json.dumps(out,indent=1))
