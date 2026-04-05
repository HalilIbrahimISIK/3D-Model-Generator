import json, os

nb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'colab_app.ipynb')
with open(nb_path) as f:
    nb = json.load(f)

for c in nb['cells']:
    if c['cell_type'] == 'code' and 'spconv_pkg' in ''.join(c['source']):
        src = ''.join(c['source'])
        # 'easydict' satırına 'utils3d' ve diğer eksik paketleri ekle
        old = "    'easydict', 'imageio', 'imageio-ffmpeg', 'plyfile',\n"
        new = "    'utils3d', 'easydict', 'imageio', 'imageio-ffmpeg', 'plyfile',\n"
        src = src.replace(old, new)
        # 'gradio' satırına ek bağımlılıklar ekle
        old2 = "    'groq', 'gradio>=4.0', 'plotly', 'jaxtyping', 'einops',\n"
        new2 = "    'groq', 'gradio>=4.0', 'plotly', 'jaxtyping', 'einops',\n    'open3d', 'kaolin',\n"
        # kaolin kurulumu farklı, bunu ayrı ele alalım - sadece utils3d yeterli
        src = src.replace(old2, "    'groq', 'gradio>=4.0', 'plotly', 'jaxtyping', 'einops',\n")
        c['source'] = [src]
        print("Kurulum hucresi guncellendi - utils3d eklendi")
        break

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

# Dogrulama
with open(nb_path) as f:
    nb2 = json.load(f)
for c in nb2['cells']:
    if c['cell_type'] == 'code' and 'spconv_pkg' in ''.join(c['source']):
        for line in c['source'][0].split('\n'):
            if 'utils3d' in line or 'easydict' in line or 'groq' in line:
                print(' ', repr(line))
        break

