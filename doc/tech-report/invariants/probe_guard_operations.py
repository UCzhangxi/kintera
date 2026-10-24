"""Compile isolated native guard operations; this is NOT report-case reachability.

Boundary quantities are bound explicitly. Native clamps are extracted from source;
other probes are reviewed operation fixtures, not whole native solver calls.
Only source-extracted probes qualify automatically for the strict coverage gate.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import torch
from torch.utils.cpp_extension import include_paths, library_paths

HERE=Path(__file__).resolve().parent
PIN='e357792d50639d68e9090b542edf038d2b029aa2'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def extract_call(source, row):
    text=(source/row['path']).read_text()
    start=sum(len(x)+1 for x in text.splitlines()[:row['line']-1])
    m=re.search(r'\.clamp(?:_min|_max)?_?\(|torch::clamp\(',text[start:])
    assert m is not None, row['id']
    pos=start+m.start(); opening=text.index('(',pos); level=1; end=opening+1
    while level:
        level+=(text[end]=='(')-(text[end]==')'); end+=1
    call=text[pos:end]
    if call.startswith('torch::clamp'):
        inside=call[len('torch::clamp('):-1]; level=0
        for i,ch in enumerate(inside):
            level+=(ch=='(')-(ch==')')
            if ch==',' and level==0: break
        call='.clamp('+inside[i+1:].strip()+')'
    # Explicit four-coordinate interpolation fixture; its upper index is 4-2.
    call=call.replace('coord.size(-1) - 2','2')
    return call

def clamp_fixture(row):
    call=row['native_call']
    tiny=math.ulp(0.) if row['path'].endswith('evaporation_extent.cpp') else sys.float_info.min if row['path'].endswith('evaporation.cpp') else 1e-300
    low,high=None,None
    bounds=call[call.index('(')+1:-1]
    def value(s):
        return {'tiny':tiny,'std::log(maxval) - 1':math.log(sys.float_info.max)-1,'options->gas_floor()':1e-20}.get(s.strip(),None) if not re.fullmatch(r'[\d.eE+\- ]+',s) else float(s)
    vals=[value(s) for s in bounds.split(',')]
    assert all(v is not None for v in vals),call
    if 'clamp_max' in call: high=vals[0]
    else:
        low=vals[0]
        if len(vals)>1:high=vals[1]
    inputs=[-1.,0.,1.]
    for bound in (low,high):
        if bound is not None:inputs += [math.nextafter(bound,-math.inf),bound,math.nextafter(bound,math.inf)]
    inputs=list(dict.fromkeys(inputs))
    expected=[min(high,max(low,x) if low is not None else x) if high is not None else max(low,x) for x in inputs]
    return dict(inputs=inputs,expected=expected,body='double tiny='+repr(tiny)+'; double maxval=std::numeric_limits<double>::max(); struct Opt {double gas_floor(){return 1e-20;}} opt; auto options=&opt; return x'+call+';',meaning='Source-extracted clamp on the intermediate shown in the cited statement; scalar binary64 boundary fixtures. No claim about full-solver reachability.',source_extracted=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.source,text=True).strip();assert sha==PIN
    inv=json.loads((HERE/'guard-inventory.json').read_text())
    for f in inv['files']:assert digest(a.source/f['path'])==f['sha256'],f['path']
    registry=json.loads((HERE/'guard-classification.json').read_text())
    a.build.mkdir(parents=True,exist_ok=True)
    rows=[r for r in registry['rows'] if r.get('policy')=='native_clamp']
    fixtures=[]
    for r in rows:
        lines=(a.source/r['path']).read_text().splitlines();assert lines[r['line']-1].strip()==r['code']
        assert extract_call(a.source,r)==r['native_call'], r['id']
        f=clamp_fixture(r);fixtures.append((r,f))
    cpp=['#include <torch/torch.h>','#include <iostream>','#include <iomanip>','#include <limits>','#include <cmath>','int main(){torch::set_num_threads(1);std::cout<<std::setprecision(17);']
    for i,(r,f) in enumerate(fixtures):
        vals=','.join(repr(v) for v in f['inputs'])
        cpp += ['{auto x=torch::tensor(std::vector<double>{'+vals+'},torch::kFloat64);', 'auto probe=[&](torch::Tensor x){'+f['body']+'};','auto y=probe(x).contiguous(); auto data=y.data_ptr<double>();',f'std::cout<<"{i}"; for(int j=0;j<y.numel();j++) std::cout<<" "<<data[j]; std::cout<<"\\n";','}']
    cpp+=['}']; cppfile=a.build/'operations.cpp';cppfile.write_text('\n'.join(cpp)+'\n')
    binary=a.build/'operations'
    cmd=['c++','-std=c++17','-O0','-g0',f'-D_GLIBCXX_USE_CXX11_ABI={int(torch._C._GLIBCXX_USE_CXX11_ABI)}',str(cppfile),'-o',str(binary)]
    cmd += ['-I'+x for x in include_paths()]+['-L'+x for x in library_paths()]+['-Wl,-rpath,'+x for x in library_paths()]+['-ltorch','-ltorch_cpu','-lc10']
    subprocess.run(cmd,check=True)
    result=subprocess.run([str(binary.resolve())],capture_output=True,text=True,check=True)
    (a.build/'native.stdout').write_text(result.stdout)
    observed={int(line.split()[0]):list(map(float,line.split()[1:])) for line in result.stdout.splitlines()}
    evidence=[]
    for i,(r,f) in enumerate(fixtures):
        got=observed[i]; expected=f['expected']; passed=got==expected
        evidence.append(dict(id=r['id'],citation=r['citation'],inputs=f['inputs'],expected=expected,observed=got,pass_=passed,absolute_tolerance=0,relative_tolerance=0,scope=f['meaning'],native_call=r['native_call'],source_file_sha256=digest(a.source/r['path'])))
    out=dict(probe_sha256=digest(Path(__file__)),source=sha,torch=torch.__version__,compiler_command=cmd,generated_source_sha256=digest(cppfile),registry_sha256=digest(HERE/'guard-classification.json'),rows=evidence,passed=sum(r['pass_'] for r in evidence),total=len(evidence))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'passed':out['passed'],'total':out['total']}));return int(out['passed']!=out['total'])
if __name__=='__main__':raise SystemExit(main())
