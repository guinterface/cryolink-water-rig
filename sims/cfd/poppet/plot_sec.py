import numpy as np, matplotlib, sys; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.tri as mtri
c=sys.argv[1]; t=sys.argv[2]; rho=1141.83
U=np.loadtxt(f'{c}/postProcessing/sec/{t}/U_y0.raw'); P=np.loadtxt(f'{c}/postProcessing/sec/{t}/p_y0.raw')
x,z=U[:,0]*1e3,U[:,2]*1e3; m=(z>245)&(z<372)
um=np.linalg.norm(U[:,3:6],axis=1)
fig,ax=plt.subplots(1,2,figsize=(10,7.2),sharey=True)
for a,v,lab,cm in ((ax[0],um,'|U| (m/s)','viridis'),(ax[1],P[:,3]*rho/1000,'p - p_outlet (kPa)','coolwarm')):
    tri=mtri.Triangulation(x[m],z[m]); 
    tr=tri.triangles; e=np.max(np.hypot(np.diff(x[m][tr][:,[0,1,2,0]],axis=1),np.diff(z[m][tr][:,[0,1,2,0]],axis=1)),axis=1); tri.set_mask(e>2.0)
    cs=a.tricontourf(tri,v[m],60,cmap=cm); fig.colorbar(cs,ax=a,label=lab,shrink=.8)
    a.set_aspect('equal'); a.set_xlabel('x (mm)')
ax[0].set_ylabel('z (mm)'); ax[0].set_title('Velocity, mated coupling, 0.28 kg/s LOX'); ax[1].set_title('Static pressure')
for a in ax:
    a.annotate('A guide spider',(10,261),(25,250),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.6))
    a.annotate('B guide spider',(10,352),(22,366),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.6))
    a.annotate('flow',(-30,255),(-30,275),fontsize=8,arrowprops=dict(arrowstyle='<-',lw=.8))
plt.tight_layout(); plt.savefig(f'{c}_section.png',dpi=130)
