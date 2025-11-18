# utils.py
import os

HIGH_SCORE_FILE = "lane3d_highscore.txt"

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(int(score)))
    except Exception:
        pass

def aabb(a_min, a_max, b_min, b_max):
    """Axis aligned bounding box intersection test (3D)."""
    return (
        a_min[0] <= b_max[0] and a_max[0] >= b_min[0]
        and a_min[1] <= b_max[1] and a_max[1] >= b_min[1]
        and a_min[2] <= b_max[2] and a_max[2] >= b_min[2]
    )
