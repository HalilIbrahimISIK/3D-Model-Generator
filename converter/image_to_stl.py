"""
Image to STL Converter using TripoSR.
TripoSR: https://github.com/VAST-AI-Research/TripoSR
Model: stabilityai/TripoSR (HuggingFace)
"""

import os
import sys
import tempfile
from typing import Optional, Callable
from utils.config_manager import load_config

# Add bundled TripoSR library to Python path
_TRIPOSR_LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "triposr_lib")
if os.path.isdir(_TRIPOSR_LIB) and _TRIPOSR_LIB not in sys.path:
    sys.path.insert(0, _TRIPOSR_LIB)


class ImageToSTLConverter:
    """
    Converts a single 2D image to a 3D STL mesh using TripoSR.

    Requirements:
        pip install git+https://github.com/VAST-AI-Research/TripoSR.git
        or
        pip install tsr

    The HuggingFace model (stabilityai/TripoSR) is automatically downloaded
    on first use (~1.5 GB).
    """

    def __init__(self):
        self.model = None
        self._model_loaded = False
        self._triposr_available = False
        self.device = "cpu"
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if TripoSR and required packages are available."""
        try:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            self.device = "cpu"

        try:
            from tsr.system import TSR  # noqa
            self._triposr_available = True
        except ImportError:
            self._triposr_available = False

    def is_available(self) -> bool:
        """Return True if TripoSR is installed."""
        return self._triposr_available

    def get_install_instructions(self) -> str:
        """Return installation instructions for TripoSR."""
        return (
            "TripoSR kurulu değil. Kurmak için:\n\n"
            "pip install git+https://github.com/VAST-AI-Research/TripoSR.git\n\n"
            "veya setup.sh scriptini çalıştırın."
        )

    def _load_model(self, progress_cb: Optional[Callable] = None):
        """Load TripoSR model from HuggingFace (downloads on first run)."""
        if self._model_loaded and self.model is not None:
            return

        if not self._triposr_available:
            raise RuntimeError("TripoSR kurulu değil. " + self.get_install_instructions())

        try:
            import torch
            from tsr.system import TSR

            if progress_cb:
                progress_cb(5, "TripoSR modeli yükleniyor (ilk kullanımda ~1.5 GB indirilir)...")

            self.model = TSR.from_pretrained(
                "stabilityai/TripoSR",
                config_name="config.yaml",
                weight_name="model.ckpt",
            )

            # Optimize chunk size for memory
            if hasattr(self.model, "renderer") and hasattr(self.model.renderer, "set_chunk_size"):
                self.model.renderer.set_chunk_size(8192)

            self.model = self.model.to(self.device)
            self.model.eval()
            self._model_loaded = True

            if progress_cb:
                progress_cb(25, "Model başarıyla yüklendi.")

        except Exception as e:
            self._model_loaded = False
            self.model = None
            raise RuntimeError(f"Model yüklenirken hata: {e}")

    def convert(
        self,
        image_path: str,
        output_path: str,
        progress_cb: Optional[Callable] = None,
    ) -> str:
        """
        Convert an image file to STL.

        Args:
            image_path:   Path to input image (PNG, JPG, etc.)
            output_path:  Desired output .stl path
            progress_cb:  Optional callback(percent: int, message: str)

        Returns:
            Path to the generated STL file.
        """
        if not self._triposr_available:
            raise RuntimeError(self.get_install_instructions())

        import torch
        from PIL import Image

        # ---- 1. Load model ----
        self._load_model(progress_cb)

        # ---- 2. Load & preprocess image ----
        if progress_cb:
            progress_cb(30, "Görsel işleniyor...")

        image = Image.open(image_path).convert("RGBA")

        # ---- 3. Background removal ----
        try:
            from rembg import remove as rembg_remove, new_session
            if progress_cb:
                progress_cb(40, "Arka plan kaldırılıyor...")
            session = new_session("u2net")
            image = rembg_remove(image, session=session)
        except Exception as e:
            print(f"[Converter] rembg not available or failed ({e}), skipping background removal.")

        # Convert to RGB for TripoSR
        image = image.convert("RGB")

        # ---- 4. Resize/center foreground ----
        try:
            from tsr.utils import resize_foreground
            image = resize_foreground(image, 0.85)
        except Exception:
            # Fallback: just resize to 512x512
            image = image.resize((512, 512), Image.LANCZOS)

        # ---- 5. Run 3D reconstruction ----
        if progress_cb:
            progress_cb(55, "3D yeniden yapılandırma çalışıyor...")

        with torch.no_grad():
            scene_codes = self.model([image], device=self.device)

        # ---- 6. Extract mesh ----
        config = load_config()
        resolution = config.get("mesh_resolution", 256)

        if progress_cb:
            progress_cb(80, f"Mesh çıkarılıyor (çözünürlük: {resolution})...")

        meshes = self.model.extract_mesh(scene_codes, has_vertex_color=False, resolution=resolution)
        mesh = meshes[0]

        # ---- 7. Export STL ----
        if progress_cb:
            progress_cb(95, "STL dosyası dışa aktarılıyor...")

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Ensure .stl extension
        if not output_path.lower().endswith(".stl"):
            output_path += ".stl"

        mesh.export(output_path)

        if progress_cb:
            progress_cb(100, "✅ STL dosyası başarıyla oluşturuldu!")

        return output_path

    def unload_model(self):
        """Release model from memory."""
        if self.model is not None:
            try:
                import torch
                del self.model
                if self.device == "cuda":
                    torch.cuda.empty_cache()
            except Exception:
                pass
            finally:
                self.model = None
                self._model_loaded = False


