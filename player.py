# player.py
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from utils import aabb

# Colors
COL_PLAYER = (0.16, 0.65, 1.0)
COL_PLAYER_HIT = (1.0, 0.26, 0.26)
COL_PLAYER_COLLECT = (0.48, 1.0, 0.6)

def draw_cube(center, size, color):
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
    verts = [
        (cx - sx, cy - sy, cz - sz),
        (cx + sx, cy - sy, cz - sz),
        (cx + sx, cy + sy, cz - sz),
        (cx - sx, cy + sy, cz - sz),
        (cx - sx, cy - sy, cz + sz),
        (cx + sx, cy - sy, cz + sz),
        (cx + sx, cy + sy, cz + sz),
        (cx - sx, cy + sy, cz + sz),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 3, 7, 4),
    ]
    glColor3f(*color)
    glBegin(GL_QUADS)
    for f in faces:
        for vi in f:
            glVertex3fv(verts[vi])
    glEnd()

def draw_cylinder(center, radius, height, axis='x', color=(0.0,0.0,0.0)):
    glColor3f(*color)
    quad = gluNewQuadric()
    cx, cy, cz = center
    glPushMatrix()
    if axis == 'x':
        glTranslatef(cx, cy, cz)
        glRotatef(90, 0, 0, 1)
    elif axis == 'z':
        glTranslatef(cx, cy, cz)
        glRotatef(90, 1, 0, 0)
    else:
        glTranslatef(cx, cy, cz)
    glTranslatef(0, -height/2.0, 0)
    gluCylinder(quad, radius, radius, height, 12, 1)
    glPushMatrix(); glRotatef(180, 1,0,0); gluDisk(quad, 0, radius, 12, 1); glPopMatrix()
    glTranslatef(0, height, 0); gluDisk(quad, 0, radius, 12, 1)
    glPopMatrix()
    gluDeleteQuadric(quad)

class CarModel:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.w, self.h, self.d = 1.8, 0.8, 3.0
        self.color = COL_PLAYER

    def draw(self):
        x, y, z = self.x, self.y, self.z

        body_color = self.color
        dark = tuple(c * 0.7 for c in body_color)
        glass = (0.08, 0.12, 0.18)
        trim = (0.75, 0.75, 0.78)
        wheel = (0.12, 0.12, 0.14)
        light = (1.0, 1.0, 0.85)
        tail = (0.9, 0.15, 0.15)

    # ======================
    # MAIN BODY
    # ======================
        draw_cube(
            (x, y + 0.25, z),
            (1.9, 0.5, 3.2),
            body_color
        )

    # ======================
    # ROOF
    # ======================
        draw_cube(
            (x, y + 0.7, z + 0.3),
            (1.3, 0.45, 1.6),
            dark
        )

    # ======================
    # HOOD
    # ======================
        draw_cube(
            (x, y + 0.2, z + 1.9),
            (1.8, 0.35, 0.6),
            dark
        )

    # ======================
    # WINDSHIELD
    # ======================
        glPushMatrix()
        glTranslatef(x, y + 0.7, z + 1.1)
        glRotatef(-20, 1, 0, 0)
        draw_cube((0, 0, 0), (1.2, 0.35, 0.1), glass)
        glPopMatrix()

    # ======================
    # REAR WINDOW
    # ======================
        glPushMatrix()
        glTranslatef(x, y + 0.7, z - 0.7)
        glRotatef(15, 1, 0, 0)
        draw_cube((0, 0, 0), (1.2, 0.35, 0.1), glass)
        glPopMatrix()

    # ======================
    # HEADLIGHTS
    # ======================
        for side in (-1, 1):
            draw_cube(
                (x + side * 0.55, y + 0.15, z + 2.1),
                (0.25, 0.18, 0.12),
                light
            )

    # ======================
    # TAILLIGHTS
    # ======================
        for side in (-1, 1):
            draw_cube(
                (x + side * 0.55, y + 0.2, z - 2.0),
                (0.25, 0.15, 0.12),
                tail
            )

    # ======================
    # BUMPERS
    # ======================
        draw_cube((x, y + 0.05, z + 2.25), (1.9, 0.15, 0.25), trim)
        draw_cube((x, y + 0.05, z - 2.15), (1.9, 0.15, 0.2), trim)

  
        # ======================
        # WHEELS (fixed & clean)
        # ======================
        wheel_y = y - 0.25
        wheel_w = 0.25   # thickness
        wheel_h = 0.35   # height
        wheel_d = 0.6    # diameter

        for side in (-1, 1):
            for dz in (1.25, -1.25):
                draw_cube(
                    (x + side * 1.05, wheel_y, z + dz),
                    (wheel_w, wheel_h, wheel_d),
                    wheel
                )




class Player:
    def __init__(self, lane_x_list, start_lane, y, z):
        # lane_x_list: list of lane center x coordinates
        self.lane_x_list = lane_x_list
        self.lane = start_lane
        self.x = lane_x_list[start_lane]
        self.target_x = self.x
        self.prev_x = self.x           # previous frame X position for swept-AABB
        self.y = y
        self.z = z
        self.w, self.h, self.d = 1.8, 0.8, 3.0
        self.color = COL_PLAYER
        # move_duration controls lateral slide speed. 0.06 = smooth & responsive.
        # Set to 0.0 for instant teleport if preferred.
        self.move_duration = 0.045
        self.t = 1.0
        self.flash = 0.0
        self.queue = []
        self.model = CarModel(self.x, self.y, self.z)

    def rect(self):
        hx, hy, hz = self.w / 2.0, self.h / 2.0, self.d / 2.0
        return ((self.x - hx, self.y - hy, self.z - hz), (self.x + hx, self.y + hy, self.z + hz))

    def request_move(self, dir, obstacles):
        """
        Enqueue a requested lane change. Do NOT block based on obstacles —
        allow the move and let collision detection handle the result.
        """
        # estimate lane after queued moves
        cur_lane_est = self.lane
        for q in self.queue:
            cur_lane_est += q

        # bounds check only
        if cur_lane_est + dir < 0 or cur_lane_est + dir >= len(self.lane_x_list):
            return False

        # enqueue and attempt to start immediately for snappy response
        self.queue.append(dir)
        # try to start right away to reduce perceived input lag
        self.apply_next_move(obstacles)
        return True

    def apply_next_move(self, obstacles):
        """
        Start the next queued move — no obstacle blocking checks.
        Returns True if a move was applied.
        """
        if not self.queue:
            return False

        dir = self.queue.pop(0)
        new_lane = self.lane + dir

        # final bounds safety (shouldn't happen)
        if new_lane < 0 or new_lane >= len(self.lane_x_list):
            return False

        # apply move (interrupt interpolation so it's responsive)
        self.lane = new_lane
        self.target_x = self.lane_x_list[self.lane]
        self.t = 0.0
        return True

    def update(self, dt, obstacles):
        """
        Update interpolation and store prev_x for swept collision tests.
        Call this once per frame before collision detection in game.update().
        """
        # store previous x at start of update for swept-AABB (important)
        self.prev_x = self.x

        # if idle and have queued moves, attempt to start next
        if self.t >= 1.0 and self.queue:
            self.apply_next_move(obstacles)

        # interpolation toward target_x
        if self.t < 1.0:
            # progress param
            if self.move_duration <= 0.0:
                # instant teleport
                self.t = 1.0
                self.x = self.target_x
            else:
                self.t += dt / max(1e-6, self.move_duration)
                s = min(1.0, self.t)
                # smoothstep interpolation
                s = s * s * (3 - 2 * s)
                self.x = (1 - s) * self.prev_x + s * self.target_x
        else:
            self.x = self.target_x

        # update model pos
        self.model.x = self.x

        # flash timer (collect/hit)
        if self.flash > 0:
            self.flash -= dt
            if self.flash <= 0:
                self.color = COL_PLAYER

    def draw(self):
        self.model.color = self.color
        self.model.draw()
