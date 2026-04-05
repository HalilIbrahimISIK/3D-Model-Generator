from typing import *
import torch
import torch.nn as nn
from .. import models


class Pipeline:
    """
    A base class for pipelines.
    """
    def __init__(
        self,
        models: dict[str, nn.Module] = None,
    ):
        if models is None:
            return
        self.models = models
        for model in self.models.values():
            model.eval()

    @staticmethod
    def from_pretrained(path: str) -> "Pipeline":
        """
        Load a pretrained model.
        """
        import os
        import json
        is_local = os.path.exists(f"{path}/pipeline.json")

        if is_local:
            config_file = f"{path}/pipeline.json"
        else:
            from huggingface_hub import hf_hub_download
            config_file = hf_hub_download(path, "pipeline.json")

        with open(config_file, 'r') as f:
            args = json.load(f)['args']

        _models = {}
        for k, v in args['models'].items():
            full_path = f"{path}/{v}"
            try:
                _models[k] = models.from_pretrained(full_path)
            except Exception as first_err:
                # DEBUG: print actual error to help diagnose
                print(f"⚠️  Model '{k}' ({full_path}) yuklenemedi, fallback deneniyor...")
                print(f"    Hata turu: {type(first_err).__name__}")
                print(f"    Mesaj: {str(first_err)[:200]}")
                
                err_str = str(first_err).lower()
                # Re-raise immediately on auth errors — don't fall back silently
                if any(x in err_str for x in ("401", "403", "authentication", "invalid username", "token", "gated", "access", "repository not found")):
                    raise RuntimeError(
                        f"HuggingFace kimlik dogrulama hatasi: {first_err}\n\n"
                        "Cozum:\n"
                        "  1. https://huggingface.co/microsoft/TRELLIS-image-large adresinde\n"
                        "     'Agree and access repository' tusuna tiklayin (ucretsiz)\n"
                        "  2. https://huggingface.co/settings/tokens adresinden token alin\n"
                        "  3. Google Colab'da su kodu calistirin:\n"
                        "       from huggingface_hub import login\n"
                        "       login(token='YOUR_TOKEN_HERE')\n"
                        "  VEYA terminalde: huggingface-cli login"
                    ) from first_err
                
                # Don't try fallback for relative paths (they won't work as repo IDs)
                # Only fallback if v looks like a complete repo path (e.g., "org/model")
                if '/' in v and not v.startswith('ckpts/'):
                    try:
                        print(f"    Fallback deneniyor: '{v}'")
                        _models[k] = models.from_pretrained(v)
                        print(f"    ✅ Fallback basarili")
                        continue
                    except Exception as second_err:
                        print(f"    ❌ Fallback basarisiz: {type(second_err).__name__}")
                
                # If we get here, both attempts failed or fallback was skipped
                raise RuntimeError(
                    f"Model '{k}' yuklenemedi.\n"
                    f"  Path: '{full_path}'\n"
                    f"  Hata: {first_err}\n\n"
                    "Olasi nedenler:\n"
                    "  - HuggingFace hesabinda model erisim izni yok\n"
                    "  - HuggingFace token hatali veya eksik\n"
                    "  - Internet baglantisi problemi\n\n"
                    "Cozum:\n"
                    "  1. https://huggingface.co/microsoft/TRELLIS-image-large -> 'Agree and access repository'\n"
                    "  2. https://huggingface.co/settings/tokens -> Token al\n"
                    "  3. Colab'da: from huggingface_hub import login; login(token='YOUR_TOKEN')"
                ) from first_err

        new_pipeline = Pipeline(_models)
        new_pipeline._pretrained_args = args
        return new_pipeline

    @property
    def device(self) -> torch.device:
        for model in self.models.values():
            if hasattr(model, 'device'):
                return model.device
        for model in self.models.values():
            if hasattr(model, 'parameters'):
                return next(model.parameters()).device
        raise RuntimeError("No device found.")

    def to(self, device: torch.device) -> None:
        for model in self.models.values():
            model.to(device)

    def cuda(self) -> None:
        self.to(torch.device("cuda"))

    def cpu(self) -> None:
        self.to(torch.device("cpu"))
