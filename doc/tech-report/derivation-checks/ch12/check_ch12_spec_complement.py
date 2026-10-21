"""Small C12-c/e/f complements; no rerun of the 102-comparison campaign.

Run modes separately: sparse, launch, conditioning. conditioning is CPU-only
and reuses deterministic inputs from the saved campaign. All stochastic inputs
use torch seed 20261020. Neither dtype comparison is a performance benchmark.
"""
import argparse, ctypes, importlib.util, json, os, pathlib
import numpy as np
from common import kintera as kt, torch, version_line

torch.set_num_threads(1)
torch.set_default_dtype(torch.float64)
ROOT=pathlib.Path(os.environ['KINTERA_REPO'])
SEED=20261020

def emit(**kw): print(json.dumps(kw,allow_nan=False),flush=True)

def sparse():
    # Closed/no-flux c_diffusion, two columns, three layers, two species.
    # Assemble ONCE on CPU, then copy exactly rounded A and rhs to CUDA.
    for dtype in (torch.float64,torch.float32):
        cast=lambda x: torch.tensor(x,dtype=dtype)
        state=kt.AtmState2D(x1f=cast([0,1e5,2.5e5,4e5]),x2f=cast([0,8e4,2e5]),
            temperature=torch.full((2,3),250.,dtype=dtype),
            pressure=cast([[1e5,1e4,1e3]]).expand(2,3).contiguous(),
            concentration=torch.full((2,3,2),.5e-6,dtype=dtype))
        kzz=cast([[1e5,2e5,3e5],[1.5e5,2.5e5,3.5e5]])
        kyy=torch.full((2,3),2e5,dtype=dtype)
        L=kt.build_eddy_diffusion_matrix(state,kzz,kyy=kyy,form='c_diffusion')
        mat=L.affine_with_identity(identity_coeff=1.,scale=-1e5)
        A=mat.global_csr.to_dense();a=A.double().numpy()
        gen=torch.Generator().manual_seed(SEED)
        rhs=torch.rand((2,3,2),generator=gen,dtype=torch.float64).to(dtype)
        b=rhs.double().numpy().flatten();ref=np.linalg.solve(a,b)
        cond=float(np.linalg.cond(a));eps=torch.finfo(dtype).eps
        zs=[]
        for device in ('cpu','cuda'):
            mm=mat if device=='cpu' else kt.SparseSystemMatrix.from_dense(A.to(device),ncol=2,nlyr=3,nspecies=2)
            z=kt.solve_sparse_system(mm,rhs.to(device)).cpu().double().numpy().flatten()
            if device=='cuda':torch.cuda.synchronize()
            assert np.isfinite(z).all()
            residual=a@z-b
            err=float(np.abs(z-ref).max()/np.abs(ref).max())
            # Explicit exploratory bound: 20*kappa_2*eps, not a theorem.
            assert err<=20*cond*eps,(device,err,cond*eps)
            emit(case='assembled_atm2d',dtype=str(dtype),device=device,status='returned',count=12,finite=12,
                max_abs_to_dense=float(np.abs(z-ref).max()),global_relative_to_dense=err,
                max_abs_residual=float(np.abs(residual).max()),
                backward_error_inf=float(np.linalg.norm(residual,np.inf)/(np.linalg.norm(a,np.inf)*np.linalg.norm(z,np.inf)+np.linalg.norm(b,np.inf))))
            zs.append(z)
        diff=np.abs(zs[0]-zs[1]);den=max(np.abs(zs[0]).max(),np.abs(zs[1]).max())
        pair=float(diff.max()/den)
        assert pair<=20*cond*eps
        # Conservation of the assembled no-flux tendency, volume weighting.
        vol=(state.dx2f[:,None]*state.dx1f[None,:]).unsqueeze(-1).expand(2,3,2)
        tend=L.matvec(rhs)
        imbalance=(vol*tend).sum((0,1)).abs().max()
        scale=(vol*tend.abs()).sum((0,1)).max()
        emit(case='assembled_atm2d_pair',dtype=str(dtype),seed=SEED,shape=[2,3,2],nstate=12,nnz=int(mat.global_csr._nnz()),
            dt=1e5,cond2=cond,eps=eps,kappa_eps=cond*eps,max_abs_cpu_cuda=float(diff.max()),
            global_relative_cpu_cuda=pair,relative_over_kappa_eps=pair/(cond*eps),tolerance=20*cond*eps,
            finite_mask_mismatch=0,status_agreement=True,
            max_pointwise_relative=float((diff/np.maximum(np.maximum(np.abs(zs[0]),np.abs(zs[1])),np.finfo(float).tiny)).max()),
            volume_weighted_conservation_relative=float(imbalance/scale),verdict='PASS')

def launch():
    # Use loaded cudart rather than guess M from architecture or 48 KiB example.
    cudarts=sorted({line.split()[-1] for line in pathlib.Path('/proc/self/maps').read_text().splitlines() if '/libcudart.so' in line})
    torch.cuda.init()
    cudarts=sorted({line.split()[-1] for line in pathlib.Path('/proc/self/maps').read_text().splitlines() if '/libcudart.so' in line})
    limits=[]
    for path in cudarts:
        lib=ctypes.CDLL(path); vals=[]
        for attr in (8,97): # cudaDevAttrMaxSharedMemoryPerBlock, ...Optin
            value=ctypes.c_int();rc=lib.cudaDeviceGetAttribute(ctypes.byref(value),attr,0)
            assert rc==0,(path,attr,rc)
            vals.append(value.value)
        limits.append(max(vals));emit(case='shared_memory_device_attributes',library=path,ordinary=vals[0],optin=vals[1])
    assert limits and len(set(limits))==1,limits
    M=limits[0];bsize=lambda ns:32*ns*ns+48*ns
    first=next(n for n in range(1,1000) if bsize(n)>M)
    for ns in sorted({39,first-1,first}):
        S=torch.eye(ns,dtype=torch.float64);J=torch.zeros((1,ns,ns),dtype=torch.float64)
        r=torch.arange(1,ns+1,dtype=torch.float64)[None]/ns
        # A=I, exact dyadic operations in LU: oracle r for dt=1.
        for device in ('cpu','cuda'):
            if device=='cuda' and bsize(ns)>M:
                try:kt.evolve_implicit(r.cuda(),S.cuda(),J.cuda(),1.)
                except RuntimeError as ex:
                    message=str(ex).splitlines()[0]
                    assert 'exceeds device maximum' in message,message
                    emit(case='implicit_launch',ns=ns,device=device,bytes=bsize(ns),M=M,status='expected_exception',message=message)
                else:raise AssertionError('oversize CUDA workspace unexpectedly returned')
            else:
                z=kt.evolve_implicit(r.to(device),S.to(device),J.to(device),1.).cpu()
                assert torch.isfinite(z).all() and torch.equal(z,r)
                emit(case='implicit_launch',ns=ns,device=device,bytes=bsize(ns),M=M,status='returned',finite=z.numel(),max_abs_oracle=0.,predicted_threads=min(32,max(1,M//bsize(ns))) if device=='cuda' else None)
    # Saved ThermoX test has ns17/nr8: translate audited sizing functions.
    alloc=lambda count,size:((count*size+7)//8)*8
    n,nr=17,8;s=n+nr
    lu=alloc(s,8)
    kkt=sum([alloc(s*s,8),alloc(nr*nr,8),alloc(nr,8),alloc(s,8),alloc(n,8),alloc(n,4),alloc(s,4),alloc(s,4)])+lu
    feasible=alloc(nr*nr,8)+alloc(nr,8)+alloc(nr,4)+kkt
    outer=sum(alloc(c,8) for c in [nr,nr*n,nr,n*nr,nr,n,nr*nr,n])
    b=outer+feasible
    emit(case='saved_ThermoX_workspace_prediction',ns=n,nreaction=nr,dtype='float64',bytes=b,M=M,predicted_threads=min(32,max(1,M//b)),note='Source-derived launch size, not profiler instrumentation; saved 200-cell CUDA execution supplies numerical evidence')

def conditioning():
    # CPU-only reconstruction. Mirrors saved probe.py input generation exactly.
    for dtype in (torch.float64,torch.float32):
        for name in ['test_evaporation_kessler','test_coagulation_pressure_switch','jupiter']:
            if name=='jupiter':path=ROOT/'tests/jupiter.yaml'
            else:
                spec=importlib.util.spec_from_file_location(name,ROOT/'tests'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
                # Existing saved cards, no sibling write or shared helper edits.
                path=pathlib.Path(os.environ['CH12_SAVED'])/(name+'.yaml')
            op=kt.KineticsOptions.from_yaml(str(path));n=len(op.species());gen=torch.Generator().manual_seed(SEED)
            T=(80+40*torch.rand(64,generator=gen)).to(dtype) if name!='jupiter' else (180+40*torch.rand(64,generator=gen)).to(dtype)
            P=(10**(3.5+torch.rand(64,generator=gen))).to(dtype)
            p0=torch.tensor(1e4,dtype=dtype);P[:3]=torch.stack([torch.nextafter(p0,torch.tensor(0.,dtype=dtype)),p0,torch.nextafter(p0,torch.tensor(float('inf'),dtype=dtype))])
            C=(1e-3*torch.rand(64,n,generator=gen)).to(dtype)
            if 'kessler' in name:
                sat=torch.tensor([m.svp(float(t))/(m.R*float(t)) for t in T],dtype=dtype)
                C[:,op.species().index('CH4')]=sat*torch.linspace(.5,1.5,64,dtype=dtype)
            kin=kt.Kinetics(op);kin.to(dtype)
            r,dc,dt,k=kin.forward_with_rate_constants(T,P,C)
            J=kin.jacobian(T,C,torch.ones_like(T),r,dc,dt)
            # Dense condition of mathematical system from rounded S,J; CPU only.
            A=np.eye(n)[None]/10.-kin.stoich.double().numpy()@J.double().numpy()
            cond=np.linalg.cond(A);eps=torch.finfo(dtype).eps
            saved=pathlib.Path(os.environ['CH12_SAVED'])/('kinetics64.jsonl' if dtype==torch.float64 else 'kinetics32.jsonl')
            rows=[json.loads(line) for line in saved.read_text().splitlines()]
            row=next(x for x in rows if x['label']==name+'/step')
            g=row['max_abs_over_cpu_max']
            emit(case='saved_kinetics_condition',deck=name,dtype=str(dtype),seed=SEED,cells=64,ns=n,nr=int(kin.stoich.shape[1]),dt=10.,cond2_min=float(cond.min()),cond2_max=float(cond.max()),eps=eps,max_kappa_eps=float(cond.max()*eps),saved_step_global_relative=g,global_relative_over_max_kappa_eps=g/float(cond.max()*eps),note='Global max norm comparison, not a per-cell bound; no CUDA campaign rerun')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['sparse','launch','conditioning']);a=p.parse_args()
    print(version_line(),flush=True);globals()[a.mode]()
    print('COMPLETE '+a.mode,flush=True)
