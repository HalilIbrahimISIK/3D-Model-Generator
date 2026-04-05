import json, os

nb_path = 'colab_app.ipynb'
with open(nb_path) as f:
    nb = json.load(f)

for c in nb['cells']:
    if c['cell_type'] == 'code' and 'spconv_pkg' in ''.join(c['source']):
        src = ''.join(c['source'])
        
        # utils3d'yi PyPI listeden kaldır
        src = src.replace("'utils3d', 'easydict'", "'easydict'")
        
        # spconv loop bitiminden sonra utils3d'yi GitHub'dan kur
        old = "print('\\n' + '='*50)"
        new = """# utils3d GitHub'dan kurulmali
print('\\nutils3d GitHub dan kuruluyor...')
r = subprocess.run([
    sys.executable, '-m', 'pip', 'install',
    'git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8',
    '-q'
], capture_output=True, text=True)
print(f"  {'OK' if r.returncode == 0 else 'HATA'} utils3d (GitHub)")

print('\\n' + '='*50)"""
        
        src = src.replace(old, new)
        c['source'] = [src]
        print("✅ utils3d GitHub kurulumu eklendi")
        break

with open(nb_path, 'w') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("✅ Notebook kaydedildi")

