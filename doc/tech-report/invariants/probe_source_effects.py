"""Measure verbatim pinned native fragments with explicit intermediate inputs.

No source statement is rewritten. Harness declarations bind physical inputs and
observe outputs; the guarded operator/function itself is extracted from source.
This establishes local physical effects, not whole-report branch reachability.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import torch
from torch.utils.cpp_extension import include_paths,library_paths

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def extract(source, fragment):
    lines=(source/fragment['path']).read_text().splitlines()
    raw='\n'.join(lines[fragment['start']-1:fragment['end']])
    assert raw==fragment['source_text'], 'Source fragment changed: '+fragment['path']
    if fragment['kind']=='lines':return raw
    token=fragment['token'];start=raw.index(token);opening=raw.index('(',start)
    level=1;end=opening+1
    while level:
        level+=(raw[end]=='(')-(raw[end]==')');end+=1
    if fragment['kind']=='condition':return raw[opening+1:end-1]
    assert fragment['kind']=='call'
    return raw[start:end]

def literal(value):
    if isinstance(value,str):
        return {'nan':'std::numeric_limits<double>::quiet_NaN()','inf':'std::numeric_limits<double>::infinity()','-inf':'-std::numeric_limits<double>::infinity()'}[value]
    return repr(float(value))

def generate(source, fixtures):
    cpp=['#include <torch/torch.h>','#include <iostream>','#include <iomanip>','#include <limits>','#include <cmath>','#include <cstdio>', '#define DISPATCH_MACRO', '#define ADD_ARG(type,name) type name']
    metadata=[]
    for i,f in enumerate(fixtures):
        fragments=[extract(source,x) for x in f['fragments']]
        for row in f['rows']:
            file,line=row.rsplit(':',1);line=int(line)
            assert any(x['path']==file and x['start']<=line<=x['end'] for x in f['fragments']), 'Claimed row absent from compiled fragments: '+row
        body=f['result'];used=set()
        for j,part in enumerate(fragments):
            if '{{'+str(j)+'}}' in body:
                body=body.replace('{{'+str(j)+'}}',part);used.add(j)
        cpp.append('namespace fixture_'+str(i)+' { using T=double;')
        if f['kind']=='function':cpp.append(fragments[0]);used.add(0)
        tensor=f['kind'] in ('tensor','reject')
        cpp.append(('torch::Tensor execute(torch::Tensor input)' if tensor else 'double execute(double z)')+' {')
        cpp.append(f['bindings'])
        cpp.extend(part for j,part in enumerate(fragments) if j not in used)
        cpp.extend([body,'}','}'])
        metadata.append(dict(name=f['name'],rows=f['rows'],fragments=[dict(**x,extracted=part,sha256=hashlib.sha256(part.encode()).hexdigest()) for x,part in zip(f['fragments'],fragments)]))
    cpp+=['int main(){torch::set_num_threads(1);std::cout<<std::setprecision(17);']
    for i,f in enumerate(fixtures):
        vals=','.join(literal(v) for v in f['inputs']);cpp.append('{')
        if f['kind'] in ('tensor','reject'):
            cpp.append('auto input=torch::tensor(std::vector<double>{'+vals+'},torch::kFloat64);')
            if f['kind']=='reject':
                cpp.append('bool rejected=false;try{fixture_'+str(i)+'::execute(input);}catch(c10::Error const& e){if(std::string(e.what()).find("General evaporation requires finite concentrations")==std::string::npos) throw;rejected=true;}')
                cpp.append('std::cout<<"RESULT '+str(i)+' "<<(rejected?0.:1.)<<"\\n";')
            else:
                cpp.append('auto out=fixture_'+str(i)+'::execute(input).flatten().to(torch::kFloat64).contiguous();auto data=out.data_ptr<double>();')
                cpp.append('std::cout<<"RESULT '+str(i)+'";for(int j=0;j<out.numel();j++)std::cout<<" "<<data[j];std::cout<<"\\n";')
        else:
            cpp.append('std::vector<double> result;for(double z:std::vector<double>{'+vals+'}) result.push_back(fixture_'+str(i)+'::execute(z));')
            cpp.append('std::cout<<"RESULT '+str(i)+'";for(double v:result)std::cout<<" "<<v;std::cout<<"\\n";')
        cpp.append('}')
    cpp+=['}'];return '\n'.join(cpp)+'\n',metadata

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    manifest=HERE/'guard-source-fixtures.json';spec=json.loads(manifest.read_text())
    pin=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.source,text=True).strip();assert pin==spec['source']
    inventory=json.loads((HERE/'guard-inventory.json').read_text())
    for f in inventory['files']:assert sha(a.source/f['path'])==f['sha256'],f['path']
    cpp,metadata=generate(a.source,spec['fixtures']);a.build.mkdir(parents=True,exist_ok=True)
    source=a.build/'source-effects.cpp';source.write_text(cpp);exe=a.build/'source-effects'
    cmd=['c++','-std=c++17','-O0','-g0',f'-D_GLIBCXX_USE_CXX11_ABI={int(torch._C._GLIBCXX_USE_CXX11_ABI)}',str(source),'-o',str(exe)]
    cmd+=['-I'+x for x in include_paths()]+['-L'+x for x in library_paths()]+['-Wl,-rpath,'+x for x in library_paths()]+['-ltorch','-ltorch_cpu','-lc10']
    subprocess.run(cmd,check=True)
    run=subprocess.run([str(exe.resolve())],capture_output=True,text=True,check=True);(a.build/'stdout.txt').write_text(run.stdout);(a.build/'stderr.txt').write_text(run.stderr)
    observed={int(line.split()[1]):list(map(float,line.split()[2:])) for line in run.stdout.splitlines() if line.startswith('RESULT ')}
    results=[]
    for i,f in enumerate(spec['fixtures']):
        got=observed[i];want=f['expected'];rtol=f['relative_tolerance'];atol=f['absolute_tolerance']
        good=len(got)==len(want) and all(math.isfinite(x) and abs(x-y)<=atol+rtol*abs(y) for x,y in zip(got,want))
        results.append(dict(**metadata[i],inputs=f['inputs'],expected=want,observed=got,relative_tolerance=rtol,absolute_tolerance=atol,passed=good))
    output=dict(source=pin,torch=torch.__version__,probe_sha256=sha(Path(__file__)),manifest_sha256=sha(manifest),registry_sha256=sha(HERE/'guard-classification.json'),generated_source_sha256=sha(source),compiler_command=cmd,results=results,passed=all(r['passed'] for r in results))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(fixtures=len(results),operations=sum(len(r['rows']) for r in results),failed=[r['name'] for r in results if not r['passed']])))
    return int(not output['passed'])
if __name__=='__main__':raise SystemExit(main())
