"""FlexiCubes module for TRELLIS."""
try:
    from .flexicubes import FlexiCubes
    __all__ = ['FlexiCubes']
except ImportError as e:
    # kaolin not available - FlexiCubes won't work but TRELLIS can still run
    import warnings
    warnings.warn(
        f"FlexiCubes import failed (kaolin not installed): {e}\n"
        "Mesh export won't work, but Gaussian Splatting output is still available.",
        ImportWarning
    )
    FlexiCubes = None
    __all__ = []

