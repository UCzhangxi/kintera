import pathlib,re,json
D=pathlib.Path(__file__).resolve().parents[1]
R=D.parents[1]; E=D/'.reproduce/logs'
E.mkdir(parents=True,exist_ok=True)
rows=[]
def add(p,line,cmd,kind,context=''):
 rel=str(p.relative_to(R)); m=re.search(r'(?:chapters/|kintera_report/)(\d\d[b]?|ch\d\d)',rel)
 ch=('ch'+m[1] if not m[1].startswith('ch') else m[1]) if m else 'shared'
 rows.append(dict(file=rel,line=line,command=' '.join(cmd.split()),kind=kind,chapter=ch,context=context))
for p in sorted((D/'book/chapters').rglob('*.qmd')):
 if p.name.startswith('app') or 'appendices' in p.parts: continue
 t=p.read_text()
 # footnotes extend until next blank paragraph; includes multiline commands
 for m in re.finditer(r'(?m)^\[\^[^\]]+\]:[^\n]*(?:\n(?!\s*\n|\[\^)[^\n]*)*',t):
  s=m[0]
  if 'run:' not in s:continue
  tail=s.split('run:',1)[1]
  cmds=[]
  for c in re.finditer(r'`([^`]+)`',tail):
   v=' '.join(c[1].split())
   if re.match(r'(?:\w+=\S+ )*(?:python[3]?\b|bash\b|cmake\b|ctest\b|pytest\b|git\b|grep\b|cuobjdump\b|pip\b|\./|ThermoX.forward)',v):cmds.append(v)
  if not cmds:cmds=['[NO EXECUTABLE COMMAND] '+ ' '.join(tail.split())]
  for c in cmds:add(p,t[:m.start()].count('\n')+1,c,'provenance',s)
 # shell code blocks
 for m in re.finditer(r'```(?:bash|sh|shell)\n(.*?)```',t,re.S):
  add(p,t[:m.start()].count('\n')+1,m[1],'shell-block',m[0])
for p in sorted((D/'derivation-checks').rglob('*.py')):
 if p.name.startswith(('check_','validate_')):
  rel=p.relative_to(D)
  modes=['']
  if p.name=='check_ch12_spec_complement.py':modes=['conditioning','sparse','launch']
  if p.name=='check_ch12_atm2d_reach.py':modes=['','--newton-only']
  if p.name=='validate_ch12_output.py':modes=['<fresh check_ch12_twins output>']
  for mode in modes:
   add(p,1,f'python {rel} {mode}','derivation-script')
   m=re.search(r'check_ch(\d+)(b?)',p.name)
   if m:rows[-1]['chapter']='ch'+m[1].zfill(2)+m[2]
for p in sorted((D/'src').rglob('*.json')):
 try: obj=json.loads(p.read_text())
 except:continue
 prov=obj.get('provenance',{}) if isinstance(obj,dict) else {}
 for k in ['command','run']:
  if isinstance(prov,dict) and k in prov:add(p,1,str(prov[k]),'data-provenance',json.dumps(prov))
(E/'inventory-initial.json').write_text(json.dumps(rows,indent=2))
with (E/'inventory-readable.txt').open('w') as f:
 for i,r in enumerate(rows):f.write(f"{i:03} {r['chapter']} {r['file']}:{r['line']}\n  {r['command']}\n")
print(len(rows))
