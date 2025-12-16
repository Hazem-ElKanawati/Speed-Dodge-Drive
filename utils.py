import pygame
from OpenGL.GL import *
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

path ="C:/Users/abdel/Documents/GitHub/Speed-Dodge-Drive/assests/sky.jpg"
def load_texture(path):
    surf = pygame.image.load(path).convert_alpha()
    image = pygame.image.tostring(surf, "RGBA", True)
    w, h = surf.get_size()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA,
        w, h, 0,
        GL_RGBA, GL_UNSIGNED_BYTE, image
    )

    glBindTexture(GL_TEXTURE_2D, 0)
    return tex_id
