"""Package source without credentials or personal data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import re
root = Path(__file__).resolve().parents[1]
out = root.parent / 'submission' / '02_Source.zip'
exclude = {'node_modules', '.git', 'xcuserdata', 'DerivedData', '.firebase', '__pycache__', 'Exports', 'functions'}
files = []
for p in sorted(root.rglob('*')):
    if not p.is_file(): continue
    rel = p.relative_to(root)
    if any(v in exclude for v in rel.parts): continue
    if p.name in {'.DS_Store','.Rhistory','GoogleService-Info.plist','google-services.json','serviceAccountKey.json'}: continue
    if p.name.startswith('.env') or any(v in p.name.lower() for v in ['firebase-adminsdk','service-account']): continue
    if p.suffix in {'.sqlite','.db','.csv','.gpx','.p8','.p12','.mobileprovision','.xcuserstate','.zip'}: continue
    if '.sqlite-' in p.name or '.db-' in p.name: continue
    if p.suffix in {'.swift','.json','.md','.py','.sh','.mmd'}:
        source=p.read_text(errors='replace')
        if re.search(r'AIza[0-9A-Za-z_-]{30,}',source) or re.search(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',source):
            raise RuntimeError(f'Credential pattern found in {rel}; remove before packaging')
    files.append(p)
out.parent.mkdir(exist_ok=True)
with ZipFile(out,'w',ZIP_DEFLATED) as z:
    for p in files: z.write(p,Path('CommuteWalk')/p.relative_to(root))
with ZipFile(out) as z:
    assert z.testzip() is None
    for required in ['README.md','cloud/database.rules.json','MotionLogger.xcodeproj/project.pbxproj']:
        assert f'CommuteWalk/{required}' in z.namelist()
print(f'Packaged {len(files)} files ({out.stat().st_size:,} bytes): {out}')
