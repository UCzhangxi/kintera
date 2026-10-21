"""Paired real-deck TP and general-equilibrium probes, bounded to 45 and 9 cells."""
from probe import *
from kintera.equilibrium import Nasa9LogK

def run(dtype):
    op=kt.ThermoOptions.from_yaml(str(ROOT/'tests/jupiter.yaml'));names=op.species()
    T=torch.tensor([130.,160.,190.,220.,250.,273.16,290.,310.,350.],dtype=dtype).repeat_interleave(5)
    P=torch.tensor([1e2,1e3,1e4,1e5,1e6],dtype=dtype).repeat(9)
    x=torch.zeros(len(T),len(names),dtype=dtype);x[:,names.index('H2O')]=.02;x[:,names.index('NH3')]=.005;x[:,0]=1-x.sum(-1)
    out=[]
    for dev in ['cpu','cuda']:
        th=kt.ThermoX(op);th.to(torch.device(dev));th.to(dtype)
        state=x.to(dev).clone();diag=torch.zeros(len(T),1,dtype=dtype,device=dev)
        gain=th.forward(T.to(dev),P.to(dev),state,False,diag)
        out.append([state.cpu(),gain.cpu(),diag.cpu()])
        emit(label='jupiter_tp/status',dtype=str(dtype),device=dev,cells=len(T),diag_values={str(float(v)):int((diag==v).sum()) for v in diag.unique()},max_sum_fraction_error=float((state.sum(-1)-1).abs().max()))
    for i,name in enumerate(['fractions','gain']):cmp('jupiter_tp/'+name,out[0][i],out[1][i],dtype)
    emit(label='jupiter_tp/branches',dtype=str(dtype),diag_exact_mismatch=int((out[0][2]!=out[1][2]).sum()),success_mask_mismatch=int(((out[0][2]>=0)!=(out[1][2]>=0)).sum()),positive_fraction_mask_mismatch=int(((out[0][0]>0)!=(out[1][0]>0)).sum()),mismatch_TP=[{'T':float(T[i]),'P':float(P[i]),'cpu':float(out[0][2][i,0]),'cuda':float(out[1][2][i,0])} for i in range(len(T)) if out[0][2][i,0]!=out[1][2][i,0]])
    options=kt.EquilibriumOptions.from_yaml(str(ROOT/'examples/equilibrium_nasa9.yaml'))
    # CPU reference LogK is computed once and copied identically to both devices.
    model=Nasa9LogK(options);t=torch.linspace(3000.,5000.,9,dtype=dtype);p=torch.full_like(t,1e5);m=torch.tensor([.6,.2,.2],dtype=dtype).expand(9,3).clone();lk=model(t,p).to(dtype)
    outs=[]
    for dev in ['cpu','cuda']:
        eq=kt.EquilibriumTP(options);z,g,d=eq(t.to(dev),p.to(dev),m.to(dev),lk.to(dev));outs.append([v.cpu() for v in (z,g,d)])
        emit(label='nasa9/status',dtype=str(dtype),device=dev,diag= d.cpu().tolist(),max_H_balance_error=float(((z-m.to(dev))@torch.tensor([2.,0.,2.],device=dev,dtype=dtype)).abs().max()),max_O_balance_error=float(((z-m.to(dev))@torch.tensor([0.,2.,1.],device=dev,dtype=dtype)).abs().max()))
    for i,name in enumerate(['moles','gain','diagnostics']):cmp('nasa9/'+name,outs[0][i],outs[1][i],dtype)
    emit(label='nasa9/branches',dtype=str(dtype),status_mismatch=int((outs[0][2][...,0]!=outs[1][2][...,0]).sum()),iteration_mismatch=int((outs[0][2][...,1]!=outs[1][2][...,1]).sum()))

if __name__=='__main__':run(getattr(torch,sys.argv[1]))
