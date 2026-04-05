"""
Image to STL Converter using TRELLIS.
TRELLIS: https://github.com/microsoft/TRELLIS
Model: microsoft/TRELLIS-image-large (HuggingFace)

Supports single and multi-image 3D reconstruction.
⚠️  TRELLIS requires a CUDA-capable NVIDIA GPU.
"""

import os
import sys
from typing import Optional, Callable, List

from utils.config_manager import load_config

# Env flag: use native spconv algo (no auto-benchmark on first run)
os.environ.setdefault("SPCONV_ALGO", "native")

# Add bundled TRELLIS library to Python path
_TRELLIS_LIB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trellis_lib"
)
if os.path.isdir(_TRELLIS_LIB) and _TRELLIS_LIB not in sys.path:
    sys.path.insert(0, _TRELLIS_LIB)


class ImageToSTLConverter:
    """
    Converts one or more 2D images to a 3D STL mesh using TRELLIS.

    Single image  → pipeline.run(image)
    Multi-image   → pipeline.run_multi_image(images)   (different angles)

    ⚠️  Requires CUDA GPU. CPU-only execution is not supported by TRELLIS.
    """

    def __init__(self):
        self.pipeline = None
        self._model_loaded = False
        self._trellis_available = False
        self.device = "cpu"
        self._check_dependencies()

    # ── Dependency check ────────────────────────────────────

    def _check_dependencies(self):
        """Detect device and check if TRELLIS is importable."""
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        except ImportError:
            self.device = "cpu"

        try:
            from trellis.pipelines import TrellisImageTo3DPipeline  # noqa
            self._trellis_available = True
        except Exception:
            self._trellis_available = False

    def is_available(self) -> bool:
        return self._trellis_available

    def get_device(self) -> str:
        return self.device

    def get_install_instructions(self) -> str:
        return (
            "TRELLIS kurulu değil veya import edilemiyor.\n\n"
            "Kurulum için:\n"
            "  git clone https://github.com/microsoft/TRELLIS.git trellis_lib\n"
            "  pip install spconv-cu118  # CUDA 11.8 için\n"
            "  pip install easydict imageio plyfile jaxtyping\n\n"
            "⚠️  TRELLIS, NVIDIA CUDA GPU gerektirir.\n"
            "    GPU bilgisi: " + self.device
        )

    # ── Model loading ────────────────────────────────────────

    def _load_model(self, progress_cb: Optional[Callable] = None):
        """Load TRELLIS pipeline from HuggingFace (downloads ~2 GB on first run)."""
        if self._model_loaded and self.pipeline is not None:
            return

        if not self._trellis_available:
            raise RuntimeError(self.get_install_instructions())

        if self.device not in ("cuda",):
            raise RuntimeError(
                f"⚠️  TRELLIS yalnızca NVIDIA CUDA GPU ile çalışır.\n"
                f"Mevcut cihaz: {self.device}\n\n"
                "macOS kullanıyorsanız CUDA destekli bir sunucuya veya "
                "Google Colab'a ihtiyacınız var."
            )

        try:
            from trellis.pipelines import TrellisImageTo3DPipeline

            # ── HuggingFace kimlik doğrulama ──────────────────
            config = load_config()
            hf_token = config.get("hf_token", "").strip()
            if hf_token:
                try:
                    from huggingface_hub import login
                    login(token=hf_token, add_to_git_credential=False)
                    if progress_cb:
                        progress_cb(3, "HuggingFace girişi başarılı.")
                except Exception as e:
                    raise RuntimeError(
                        f"HuggingFace token geçersiz: {e}\n"
                        "Ayarlar > HuggingFace Token alanını kontrol edin."
                    )
            else:
                if progress_cb:
                    progress_cb(3, "⚠️  HF token girilmemiş — gated model erişimi başarısız olabilir.")

            if progress_cb:
                progress_cb(5, "TRELLIS modeli yükleniyor (ilk kullanımda ~2 GB indirilir)...")

            self.pipeline = TrellisImageTo3DPipeline.from_pretrained(
                "microsoft/TRELLIS-image-large"
            )
            self.pipeline.cuda()
            self._model_loaded = True

            if progress_cb:
                progress_cb(25, "✅ Model başarıyla yüklendi.")

        except Exception as e:
            self._model_loaded = False
            self.pipeline = None
            raise RuntimeError(f"Model yüklenirken hata: {e}")

    # ── Conversion ───────────────────────────────────────────

    def convert(
        self,
        image_paths: List[str],
        output_path: str,
        progress_cb: Optional[Callable] = None,
    ) -> str:
        """
        Convert one or more images to an STL file.

        Args:
            image_paths:  List of image file paths (1 = single, 2+ = multi-angle).
            output_path:  Desired output .stl path.
            progress_cb:  Optional callback(percent: int, message: str).

        Returns:
            Path to the generated STL file.
        """
        if not self._trellis_available:
            raise RuntimeError(self.get_install_instructions())
        if not image_paths:
            raise ValueError("En az bir görsel gerekli.")

        from PIL import Image
        import trimesh
        import numpy as np

        # ── 1. Load model ──────────────────────────────────
        self._load_model(progress_cb)

        # ── 2. Load images ─────────────────────────────────
        if progress_cb:
            progress_cb(30, f"{len(image_paths)} görsel yükleniyor...")

        images = [Image.open(p).convert("RGB") for p in image_paths]

        # ── 3. Run TRELLIS pipeline ────────────────────────
        config = load_config()
        steps = config.get("trellis_steps", 12)
        cfg = config.get("trellis_cfg_strength", 7.5)

        if progress_cb:
            progress_cb(40, "3D yeniden yapılandırma çalışıyor...")

        if len(images) == 1:
            outputs = self.pipeline.run(
                images[0],
                seed=42,
                preprocess_image=True,
                sparse_structure_sampler_params={"steps": steps, "cfg_strength": cfg},
                slat_sampler_params={"steps": steps, "cfg_strength": 3.0},
            )
        else:
            if progress_cb:
                progress_cb(40, f"{len(images)} açıdan çok görsel analizi yapılıyor...")
            outputs = self.pipeline.run_multi_image(
                images,
                seed=42,
                preprocess_image=True,
                sparse_structure_sampler_params={"steps": steps, "cfg_strength": cfg},
                slat_sampler_params={"steps": steps, "cfg_strength": 3.0},
            )

        # ── 4. Extract mesh ────────────────────────────────
        if progress_cb:
            progress_cb(82, "Mesh çıkarılıyor...")

        mesh_result = outputs["mesh"][0]
        vertices = mesh_result.vertices.cpu().float().numpy()
        faces = mesh_result.faces.cpu().numpy()

        tri_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

        # ── 5. Export STL ──────────────────────────────────
        if progress_cb:
            progress_cb(95, "STL dosyası dışa aktarılıyor...")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if not output_path.lower().endswith(".stl"):
            output_path += ".stl"

        tri_mesh.export(output_path)

        if progress_cb:
            progress_cb(100, "✅ STL dosyası başarıyla oluşturuldu!")

        return output_path

    # ── Cleanup ──────────────────────────────────────────────

    def unload_model(self):
        """Release GPU memory."""
        if self.pipeline is not None:
            try:
                import torch
                del self.pipeline
                if self.device == "cuda":
                    torch.cuda.empty_cache()
            except Exception:
                pass
            finally:
                self.pipeline = None
                self._model_loaded = False

