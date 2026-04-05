import json

with open('colab_app.ipynb') as f:
    nb = json.load(f)

for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])
    if "from huggingface_hub import login" in src and "HF_TOKEN" in src:
        c['source'] = [
            "from huggingface_hub import login\n",
            "\n",
            "# Token giris (direkt yaz veya Secrets kullan)\n",
            "HF_TOKEN = ''  # 'hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n",
            "\n",
            "# Colab Secrets kullaniyorsaniz (Sol panel > Secrets > HF_TOKEN):\n",
            "try:\n",
            "    from google.colab import userdata\n",
            "    if not HF_TOKEN:\n",
            "        HF_TOKEN = userdata.get('HF_TOKEN')\n",
            "        print('HF_TOKEN Secrets tan okundu')\n",
            "except Exception:\n",
            "    pass\n",
            "\n",
            "if not HF_TOKEN or not HF_TOKEN.startswith('hf_'):\n",
            "    raise ValueError(\n",
            "        'HF_TOKEN girilmedi!\\\\n'\n",
            "        '1. https://huggingface.co/microsoft/TRELLIS-image-large -> Agree tikla\\\\n'\n",
            "        '2. https://huggingface.co/settings/tokens -> token al\\\\n'\n",
            "        '3. HF_TOKEN = \\'hf_xxx...\\' yapistir VEYA Secrets kullan'\n",
            "    )\n",
            "\n",
            "login(token=HF_TOKEN, add_to_git_credential=False)\n",
            "print('HuggingFace girisi basarili!')\n",
            "print(f'Token: {HF_TOKEN[:8]}...{HF_TOKEN[-8:]}')\n",
        ]
        print(f"Token hucresi duzeltildi (index {i})")
        break

with open('colab_app.ipynb', 'w') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook kaydedildi")

