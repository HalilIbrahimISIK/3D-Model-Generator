import json

with open('colab_app.ipynb') as f:
    nb = json.load(f)

for c in nb['cells']:
    src = ''.join(c['source'])
    if "git submodule update" in src or "flexicubes" in src.lower():
        # Tüm submodule kodunu yeniden yaz
        lines = src.split('\n')
        new_lines = []
        skip_until_else = False
        
        for i, line in enumerate(lines):
            # "FlexiCubes" ile başlayan bloğu tamamen değiştir
            if 'FlexiCubes' in line and 'print' in line:
                skip_until_else = True
                new_lines.append("    # FlexiCubes'i direkt clone et (submodule calismiyor)")
                new_lines.append("    flexicubes_dir = f'{PROJECT_DIR}/trellis_lib/trellis/representations/mesh/flexicubes'")
                new_lines.append("    if not os.path.exists(f'{flexicubes_dir}/flexicubes.py'):")
                new_lines.append("        print('FlexiCubes indiriliyor...')")
                new_lines.append("        os.system(f'git clone https://github.com/MaxtirError/FlexiCubes.git {flexicubes_dir}')")
                new_lines.append("        os.system(f'rm -rf {flexicubes_dir}/.git')")
                new_lines.append("        with open(f'{flexicubes_dir}/__init__.py', 'w') as init_f:")
                new_lines.append("            init_f.write('from .flexicubes import FlexiCubes\\\\n__all__ = [\\\"FlexiCubes\\\"]\\\\n')")
                new_lines.append("        print('FlexiCubes hazir')")
                new_lines.append("    else:")
                new_lines.append("        print('FlexiCubes zaten mevcut')")
                continue
            
            if skip_until_else:
                # git submodule ile ilgili satırları atla
                if 'os.system' in line and ('submodule' in line or 'flexicubes' in line):
                    continue
                elif line.strip() == '' and i < len(lines) - 3:
                    continue
                else:
                    skip_until_else = False
            
            if not skip_until_else:
                new_lines.append(line)
        
        c['source'] = ['\n'.join(new_lines)]
        print("✅ FlexiCubes direkt clone koduna güncellendi")
        break

with open('colab_app.ipynb', 'w') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("✅ Notebook kaydedildi")

