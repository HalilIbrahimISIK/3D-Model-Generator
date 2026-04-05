from .radiance_field import Strivec
from .octree import DfsOctree as Octree
from .gaussian import Gaussian

try:
    from .mesh import MeshExtractResult
except ImportError:
    # Mesh module failed (kaolin not installed) - continue without it
    MeshExtractResult = None
