# ui.py  (FIXED: uses glWindowPos2i instead of glRasterPos)

import pygame
from OpenGL.GL import *

TEXT_COLOR = (255, 255, 220)

class Overlay:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.surface = pygame.Surface((w, h), pygame.SRCALPHA)
        self.font = pygame.font.SysFont("Arial", 26)
        self.large_font = pygame.font.SysFont("Arial", 44)

    def blit_text(self, text, x, y, size=26, color=TEXT_COLOR):
        font = pygame.font.SysFont("Arial", size)
        surf = font.render(text, True, color)
        self.surface.blit(surf, (x, y))

    def draw_fullscreen(self):
        # Convert pygame surface -> RGBA bytes
        data = pygame.image.tostring(self.surface, "RGBA", True)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        # The FIX: always draw to top-left window position
        glWindowPos2i(0, 0)

        glDrawPixels(self.w, self.h, GL_RGBA, GL_UNSIGNED_BYTE, data)

        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
