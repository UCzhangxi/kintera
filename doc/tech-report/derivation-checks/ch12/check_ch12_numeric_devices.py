"""Bounded device extension of supplied check_ch12_twins.py cases i/j/k.

Independent NumPy solve/pinv oracle; exactly the supplied seed, sizes and inputs.
Float64 uses supplied tolerance 1e-12; float32 measurements remain INFO.
No generic solver-convergence or performance claim. No shared helper edits.
"""
import json
import numpy as np
from common import kintera as kt, torch, version_line

print(version_line())
torch.set_num_threads(1)
rng=np.random.default_rng(12)
ns,nr,ncell,dt=5,4,64,.3
S=rng.integers(-2,3,size=(ns,nr)).astype(float)
J=rng.normal(size=(ncell,nr,ns));r=rng.normal(size=(ncell,nr))
A=np.eye(ns)[None]/dt-S@J;b=np.einsum('sr,cr->cs',S,r)
ref=np.stack([np.linalg.solve(A[k],b[k]) for k in range(ncell)])
S1=np.array([[1.,0.],[0.,1.],[0.,0.]])
J1=np.array([[[1.,0.,0.],[0.,.5,0.]]]);r1=np.array([[.7,-.4]])
A1=np.eye(3)-S1@J1[0];b1=S1@r1[0];ref1=(np.linalg.pinv(A1)@b1)[None]
print(json.dumps({'seed':12,'cells':64,'ns':5,'nr':4,'dt':.3,'max_cond2':float(np.linalg.cond(A).max()),'singular_rank':int(np.linalg.matrix_rank(A1))}))
if not torch.cuda.is_available():
    raise RuntimeError('CUDA unavailable: bounded paired validation not performed')
for dtype in (torch.float64,torch.float32):
    for name,ss,jj,rr,tstep,oracle in [('regular',S,J,r,.3,ref),('singular',S1,J1,r1,1.,ref1)]:
        # One CPU cast before either run ensures matching rounded input values.
        inputs=[torch.tensor(v,dtype=dtype) for v in (rr,ss,jj)]
        outs=[]
        for device in ('cpu','cuda'):
            z=kt.evolve_implicit(*(v.to(device) for v in inputs),tstep)
            if device=='cuda':torch.cuda.synchronize()
            outs.append(z.cpu().double().numpy())
        aa=np.eye(ss.shape[0])[None]/tstep-ss@jj
        bb=np.einsum('sr,cr->cs',ss,rr)
        for device,z in zip(('cpu','cuda'),outs):
            finite=int(np.isfinite(z).sum());assert finite==z.size,(name,device,'nonfinite output')
            assert np.isfinite(oracle).all(),'nonfinite oracle'
            err=float(np.max(np.abs(z-oracle)));scale=float(np.max(np.abs(oracle)))
            metric=err/scale if name=='regular' else err
            residual=aa@z[...,None]-bb[...,None]
            rec={'case':name,'device':device,'dtype':str(dtype),'count':int(z.size),'finite':finite,'max_abs_to_original_f64_oracle':err,'global_relative_to_original_f64_oracle':err/scale,'max_abs_residual_original_system':float(np.abs(residual).max()),'max_abs_normal_equation_residual':float(np.abs(aa.swapaxes(-1,-2)@residual).max()),'verdict':'PASS' if dtype==torch.float64 and metric<1e-12 else 'INFO' if dtype==torch.float32 else 'FAIL'}
            print(json.dumps(rec),flush=True)
            if dtype==torch.float64:assert metric<1e-12,rec
        delta=np.abs(outs[0]-outs[1]);den=max(float(np.abs(outs[0]).max()),float(np.abs(outs[1]).max()))
        rec={'case':name,'dtype':str(dtype),'pair_count':int(delta.size),'finite_mask_mismatch':int(np.count_nonzero(np.isfinite(outs[0])!=np.isfinite(outs[1]))),'max_abs_cpu_cuda':float(delta.max()),'global_relative_cpu_cuda':float(delta.max()/den),'verdict':'PASS' if dtype==torch.float64 and delta.max()/den<1e-12 else 'INFO' if dtype==torch.float32 else 'FAIL'}
        print(json.dumps(rec),flush=True)
        if dtype==torch.float64:assert rec['verdict']=='PASS',rec
print('COMPLETE: float64 assertions passed; float32 values are INFO, not a new tolerance requirement.')
