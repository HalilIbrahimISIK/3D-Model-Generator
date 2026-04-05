try:
    from .cube2mesh import SparseFeatures2Mesh, MeshExtractResult
except ImportError as e:
    # kaolin not available - mesh extraction won't work but TRELLIS can still run
    import warnings
    warnings.warn(
        f"Mesh module import failed (kaolin not installed): {e}\n"
        "Mesh (STL) export disabled. Gaussian Splatting still available.",
        ImportWarning
    )
    SparseFeatures2Mesh = None
    MeshExtractResult = None
