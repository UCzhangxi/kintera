"""Package and verify already-completed C12 evidence; no model execution."""
import datetime,hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parents[1];S=R/'spec-update';P=R/'integration';O=R.parent/'ch12-cpu-cuda'
old=json.loads((O/'identity.json').read_text());new=json.loads((S/'identity.json').read_text())
assert old['sha256']==new['sha256'],'loaded binary identities changed'
assert new['source_head']=='0d9f67f97d841147e23283d2dcdab302238d2c45'
for name in ['common.py','check_ch12_twins.py']:
    assert (P/name).read_bytes()==(R/'supplied'/name).read_bytes()
for mode in ['sparse','launch','conditioning','saved-summary']:
    assert (S/(mode+'.exit')).read_text().strip()=='0'
rows=[json.loads(x) for x in (S/'sparse.out').read_text().splitlines() if x.startswith('{')]
assert len(rows)==6 and all(x['finite']==12 for x in rows if 'device' in x)
assert all(x['verdict']=='PASS' for x in rows if 'verdict' in x)
rows=[json.loads(x) for x in (S/'launch.out').read_text().splitlines() if x.startswith('{')]
assert len([x for x in rows if x.get('status')=='returned'])==5
assert len([x for x in rows if x.get('status')=='expected_exception'])==1
# Historical audit remains historical; annotate the missing-spec claim now superseded.
report=R/'report.md';marker='> Update: the separate six-entry C12 specification has now arrived. The missing-spec conclusion below is historical; see [six-entry mapping and complementary measurements](spec-update/report.md).\n\n'
if not report.read_text().startswith('> Update:'):report.write_text(marker+report.read_text())

def copy(src,dest):
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)

for p in sorted(O.glob('*.jsonl')):copy(p,P/'saved-preparation'/p.name)
for name in ['probe.py','equilibrium_probe.py','one_cell.py','check_evidence.py','report.md','commands.txt','run.sh','identity.json','build-hashes.txt','pytest.txt','one-cell.yaml','workspace.yaml','test_evaporation_kessler.yaml','test_coagulation_pressure_switch.yaml','live-refs.txt','report-head.txt','report-merge-base.txt','fix-base.txt']:
    copy(O/name,P/'saved-preparation'/name)
for name in ['report.md','run_local.sh','issue54-readable.txt','manifest.json']:
    copy(R/name,P/'provenance'/name)
for name in ['identity.json','metadata.json','check_ch12_twins.cpu.exit','check_ch12_numeric_devices.exit','validate_ch12_output.exit','supplied-vs-local.diff']:
    copy(R/'results'/name,P/'provenance'/name)
for p in S.iterdir():
    if p.is_file() and p.name not in ['.writable','package-validation.out','package-manifest.json','saved-summary.attempt1.out']:
        copy(p,P/'spec-update'/p.name)
copy(S/'report.md',P/'README.md')
for mode in ['sparse','launch','conditioning']:
    copy(S/(mode+'.out'),P/('check_ch12_spec_complement.'+mode+'.out'))
files={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'}
(P/'SHA256SUMS').write_text(''.join(f'{h}  {n}\n' for n,h in files.items()))
manifest={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pin':new['source_head'],'same_loaded_binaries':True,'original_scripts_unchanged':True,'new_model_run_exit_codes':{'sparse':0,'launch':0,'conditioning':0},'commit':None,'file_count':len(files),'total_bytes':sum(p.stat().st_size for p in P.rglob('*') if p.is_file()),'sha256':files}
(S/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='sha256'},indent=2))
