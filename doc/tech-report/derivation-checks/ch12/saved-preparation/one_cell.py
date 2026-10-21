"""Minimal deck-derived TP status disagreement; no implementation changes."""
from probe import *
m=module('test_cuda_workspace')
for tol in ['1.e-12','1.e-5']:
    path=OUT/'one-cell.yaml';path.write_text(m.CARD.replace('ftol: 1.e-12','ftol: '+tol))
    op=kt.ThermoOptions.from_yaml(str(path));outs=[]
    for dev in ['cpu','cuda']:
        th=kt.ThermoX(op);th.to(torch.device(dev));th.to(torch.float32)
        T=m.TEMP[1:2].to(dtype=torch.float32,device=dev)
        x=torch.zeros(1,17,dtype=torch.float32,device=dev);x[:,1:9]=.02;x[:,0]=1-x.sum(-1)
        d=torch.zeros(1,1,dtype=torch.float32,device=dev)
        g=th.forward(T,torch.full_like(T,1e5),x,False,d)
        outs.append((x.cpu(),g.cpu(),d.cpu()))
        emit(label='one_cell/status',ftol=tol,device=dev,T=float(T[0]),P=1e5,diag=float(d[0,0]),finite=bool(torch.isfinite(x).all()))
    cmp('one_cell/fractions/'+tol,outs[0][0],outs[1][0],torch.float32)
    cmp('one_cell/gain/'+tol,outs[0][1],outs[1][1],torch.float32)
