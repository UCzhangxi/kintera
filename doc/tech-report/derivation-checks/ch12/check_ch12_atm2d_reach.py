"""Bounded K42 reach probes. Same CPU-assembled A and effective RHS on both devices.
Exact-pin in-tree example builders and targeted transport/BE boundary cases.
No claim that modified cases are shipped production decks; no general absence proof.
"""
import importlib.util,json,os,pathlib
import numpy as np
import torch,kintera as kt
from check_ch12_k42 import PIN,emit,measure
ROOT=pathlib.Path(os.environ['KINTERA_REPO'])
torch.set_num_threads(1);torch.set_default_dtype(torch.float64)
def module(name,folder='examples'):
    spec=importlib.util.spec_from_file_location(name,ROOT/folder/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def assess(label,mat,rhs,**extra):
    A=mat.global_csr.to_dense();b=mat.apply_rhs_overrides(rhs).numpy().flatten();a=A.numpy()
    sv=np.linalg.svd(a,compute_uv=False)
    out={'case':label,'dtype':str(A.dtype),'n':len(b),'numerical_rank':int(np.linalg.matrix_rank(a)),
        'smin':float(sv[-1]),'smax':float(sv[0]),'max_abs_Aones':float(np.abs(a@np.ones(len(b))).max()),
        'structural_zero_rows':int((a==0).all(axis=1).sum()),'structural_zero_cols':int((a==0).all(axis=0).sum()),**extra}
    for device in ['cpu','cuda']:
        mm=mat if device=='cpu' else kt.SparseSystemMatrix.from_dense(A.cuda(),ncol=mat.ncol,nlyr=mat.nlyr,nspecies=mat.nspecies)
        rr=rhs if device=='cpu' else torch.tensor(b).reshape(mat.ncol,mat.nlyr,mat.nspecies).cuda()
        observed=[]
        def solve():
            z=kt.solve_sparse_system(mm,rr).cpu().numpy().flatten()
            if device=='cuda':torch.cuda.synchronize()
            observed.append(z.copy());return z
        out[device]=measure(a,b,solve)
        if observed and len(b)==3:
            out[device]["solution"]=observed[0].tolist()
            if label.startswith("target_BE_"):
                out[device]["max_abs_error_to_ones"]=float(np.abs(observed[0]-1.).max())
                out[device]["relative_mass_error"]=float(abs(observed[0].astype(float).sum()-3.)/3.)
    emit(out);return out

def state(dtype=torch.float64):
    # Unit spacing makes the closed 1-D Laplacian exact in binary arithmetic.
    return kt.AtmState2D(x1f=torch.arange(4,dtype=dtype),x2f=torch.tensor([0.,1.],dtype=dtype),
        temperature=torch.full((1,3),250.,dtype=dtype),pressure=torch.full((1,3),1e4,dtype=dtype),concentration=torch.ones((1,3,1),dtype=dtype))

def main():
    emit({'pin':PIN,'domain':'small example grids; exact 1-column 3-layer closed Laplacian; finite positive BE timesteps; dtype float64 unless stated; GPU0'})
    # Real example builders at reduced grids. One representative actual solve each.
    m=module('plot_atm2d_steady_diffusion_dirichlet_2d');mat,analytic,_=m.build_case(6,5,device=torch.device('cpu'))
    rhs=torch.zeros((6,5,1));rhs[:,:,0]=analytic;rhs[1:-1,1:-1]=0
    assess('in_tree_2d_dirichlet_example_6x5',mat,rhs,dt=.2,scope='unchanged example builder, reduced grid, first march solve')
    m=module('plot_atm2d_steady_advection_diffusion');mat,_=m.build_implicit_system(17,.02,.3,.5,1.,.2)
    rhs=torch.zeros((1,17,1));rhs[0,0]=1;rhs[0,-1]=.2
    assess('in_tree_advection_example_17',mat,rhs,dt=.5,scope='unchanged example builder, reduced grid, first march solve')
    # Exactly the state helper and dt branches of the in-tree assembly-reference test.
    test=module('test_atm2d','tests');s=test._make_state(ncol=1,nlyr=6,ns=4)
    torch.manual_seed(11);s.concentration=torch.rand(1,6,4)+.5;k=torch.full((1,6),1e5)
    for dt in [1e-3,10.]:
        mat,rhs=kt.build_implicit_step_system(s,k,dt)
        assess('in_tree_assembly_reference_dt_'+str(dt),mat,rhs,dt=dt,scope='test_atm2d.py test_build_implicit_step_system_matches_dense_reference inputs; added solve')
    # An actual in-tree boundary test leaves one species unpinned (kind none).
    # Reuse its exact construction by wrapping assembly for capture; the test itself still runs.
    captured=[];original=kt.build_eddy_diffusion_matrix
    def capture(*a,**kw):
        z=original(*a,**kw);captured.append(z);return z
    kt.build_eddy_diffusion_matrix=capture
    try:test.test_boundary_conditions_apply_on_left_and_top_edges()
    finally:kt.build_eddy_diffusion_matrix=original
    assess('in_tree_mixed_boundary_test_matrix',captured[0],torch.zeros((3,4,3)),scope='unchanged in-tree boundary test builds matrix; added solve, test normally only checks assembly')
    # No boundary pin: singular operator is expected; standalone solve is targeted.
    s=state();k=torch.ones((1,3));L=kt.build_transport_matrix(s,k,form='c_diffusion')
    assert torch.equal(L.global_csr.to_dense(),torch.tensor([[-1.,1.,0.],[1.,-2.,1.],[0.,1.,-1.]]))
    assess('target_closed_operator_incompatible_rhs',L,torch.ones((1,3,1)),exact_null_vector=[1,1,1],scope='supported assembler; no gauge/identity, not a shipped standalone solve')
    assess('target_closed_operator_compatible_rhs',L,torch.tensor([[[1.],[0.],[-1.]]]),exact_null_vector=[1,1,1],scope='supported assembler; nonunique consistent system')
    bc=kt.SpeciesBoundaryConditions2D(bottom=kt.SpeciesBoundaryCondition(kind='neumann',value=0.),top=kt.SpeciesBoundaryCondition(kind='neumann',value=0.))
    N=kt.build_transport_matrix(s,k,form='c_diffusion',boundary_conditions=bc)
    assess('target_all_neumann_operator',N,torch.ones((1,3,1)),exact_null_vector=[1,1,1],scope='supported Neumann rows with no Dirichlet anchor')
    # Add the normal BE identity shift, then probe when finite precision erases it.
    for dtype,dts in [(torch.float64,[.1,1.,1e12,1e16,1e18]),(torch.float32,[.1,1.,1e6,1e8,1e10])]:
        s=state(dtype);k=torch.ones((1,3),dtype=dtype)
        negL=-kt.build_transport_matrix(s,k,form='c_diffusion').global_csr.to_dense()
        for dt in dts:
            mat,rhs=kt.build_implicit_step_system(s,k,dt,transport_form='c_diffusion')
            A=mat.global_csr.to_dense();shift_lost=bool(torch.equal(A,negL)) if dt>=1 else False
            assess('target_BE_'+str(dtype)+'_dt_'+str(dt),mat,rhs,dt=dt,shift_lost=shift_lost,scope='targeted legal API input; positive finite dt, no source terms, constant concentration; true BE solution is ones')
    print('COMPLETE: classification evidence, not proof of general reach or absence.',flush=True)


def newton_cases():
    from kintera.atm2d.newton.coupled import newton_implicit_step
    from kintera.atm2d.timestep import default_accept
    for dtype,dt in [(torch.float64,1e18),(torch.float32,1e8)]:
        for device in ['cpu','cuda']:
            s0=state(dtype)
            s=kt.AtmState2D(**{name:getattr(s0,name).to(device) for name in ['x1f','x2f','temperature','pressure','concentration']})
            before=s.concentration.clone();rec={'case':'target_coupled_Newton','dtype':str(dtype),'dt':dt,'device':device,'max_iterations':4,'scope':'same three-layer constant-state targeted case, defaults except bounded iteration cap'}
            try:
                result=newton_implicit_step(s,dt,kzz=torch.ones((1,3),dtype=dtype,device=device),source_terms=None,transport_form='c_diffusion',max_iterations=4,record_residuals=True)
                z=result.concentration.detach().cpu().double().numpy().flatten()
                rec.update(status='finite_return' if np.isfinite(z).all() else 'nonfinite_return',converged=result.converged,iterations=result.iterations,solution=z.tolist(),max_abs_error_to_ones=float(np.abs(z-1).max()),relative_mass_error=float(abs(z.sum()-3)/3),relative_change_history=result.residual_history,default_accept=default_accept(result.concentration,before).accepted)
            except RuntimeError as ex:rec.update(status='raised',error=str(ex).splitlines()[0])
            rec['input_state_restored']=bool(torch.equal(s.concentration,before));emit(rec)
    print('COMPLETE newton: targeted API reach, not a production-deck survey.',flush=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--newton-only',action='store_true');args=parser.parse_args()
    newton_cases() if args.newton_only else main()
