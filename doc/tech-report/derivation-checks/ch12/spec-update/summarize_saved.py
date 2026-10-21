"""Summarize existing evidence only; performs no numerical model execution."""
import json, pathlib, os
r=pathlib.Path(os.environ.get('CH12_SAVED','/home/tianhaol/fridica-snapy/worker2/ch12-cpu-cuda'))
for name in ['kinetics64','kinetics32','workspace64','workspace32','workspace32-relaxed']:
    ftol=1e-5 if 'relaxed' in name else 1e-12
    eps=2.220446049250313e-16 if '64' in name else 1.1920928955078125e-7
    for row in map(json.loads,[line for line in (r/(name+'.jsonl')).read_text().splitlines() if line.startswith('{')]):
        if name.startswith('kinetics') and row['label'].split('/')[-1] in ['rate','kf','jacobian','step']:
            print(json.dumps({'saved_file':name,**{k:row[k] for k in ['label','dtype','count','max_abs','max_rel_symmetric','max_abs_over_cpu_max']},'global_relative_over_eps':row['max_abs_over_cpu_max']/eps}))
        if name.startswith('workspace') and row['label']=='TP/fractions':
            print(json.dumps({'saved_file':name,'ftol':ftol,**row,'global_relative_over_ftol':row['max_abs_over_cpu_max']/ftol}))
        if name.startswith('workspace') and row['label'] in ['TP/status','TP/branches']:
            print(json.dumps({'saved_file':name,**row}))
