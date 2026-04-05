import json

with open('colab_app.ipynb') as f:
    nb = json.load(f)

for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])
    if "PROJECT_DIR = '/content/3D-Model-Generator'" in src:
        c['source'] = [
            "import os, sys\n",
            "\n",
            "os.environ['SPCONV_ALGO']  = 'native'\n",
            "os.environ['ATTN_BACKEND'] = 'sdpa'\n",
            "\n",
            "PROJECT_DIR = '/content/3D-Model-Generator'\n",
            "GITHUB_REPO = 'https://github.com/HalilIbrahimISIK/3D-Model-Generator.git'\n",
            "\n",
            "if not os.path.exists(PROJECT_DIR):\n",
            "    print('GitHub dan klonlaniyor...')\n",
            "    os.system(f'git clone {GITHUB_REPO} {PROJECT_DIR}')\n",
            "    print('Proje klonlandi')\n",
            "else:\n",
            "    print('Proje zaten mevcut')\n",
            "\n",
            "# FlexiCubes her durumda kontrol et (proje onceden varsa bile eksik olabilir)\n",
            "flexicubes_dir = f'{PROJECT_DIR}/trellis_lib/trellis/representations/mesh/flexicubes'\n",
            "if not os.path.exists(f'{flexicubes_dir}/flexicubes.py'):\n",
            "    print('FlexiCubes eksik - indiriliyor...')\n",
            "    os.system(f'git clone https://github.com/MaxtirError/FlexiCubes.git {flexicubes_dir}')\n",
            "    os.system(f'rm -rf {flexicubes_dir}/.git')\n",
            "    with open(f'{flexicubes_dir}/__init__.py', 'w') as init_f:\n",
            "        init_f.write('from .flexicubes import FlexiCubes\\\\n__all__ = [\"FlexiCubes\"]\\\\n')\n",
            "    print('FlexiCubes hazir')\n",
            "else:\n",
            "    print('FlexiCubes zaten mevcut')\n",
            "\n",
            "for path in [PROJECT_DIR, f'{PROJECT_DIR}/trellis_lib']:\n",
            "    if path not in sys.path:\n",
            "        sys.path.insert(0, path)\n",
            "\n",
            "os.chdir(PROJECT_DIR)\n",
            "print(f'Calisma dizini: {os.getcwd()}')\n",
            "\n",
            "import torch\n",
            "assert torch.cuda.is_available(), 'GPU bulunamadi!'\n",
            "print(f'GPU  : {torch.cuda.get_device_name(0)}')\n",
            "print(f'CUDA : {torch.version.cuda}')\n",
        ]
        print(f"Adim 3 duzeltildi (index {i})")
        break

with open('colab_app.ipynb', 'w') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook kaydedildi")

