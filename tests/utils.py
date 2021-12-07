import sys

import pytest

needs_py39 = pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9+")
