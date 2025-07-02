from typing import List, Tuple

import numpy as np


def generate_random_points(n: int) -> List[Tuple[float, float]]:
    """Generate n random coordinate pairs between 0 and 1"""
    if n <= 0:
        return []

    points = np.random.rand(n, 2)
    return [(float(x), float(y)) for x, y in points]
