# spawner.py
import random
from OpenGL.GL import *
from player import draw_cube
from utils import aabb

# Visual colors
COL_WALL = (0.9, 0.9, 0.9)
COL_COIN = (1.0, 0.85, 0.25)

class Obstacle:
    def __init__(self, lane_idx, x, z, width=1.6, height=1.6):
        self.lane = lane_idx
        self.x = x
        self.y = -2.4
        self.z = z
        self.w = width
        self.h = height
        self.d = 1.6
        
        # --- SOLID COLORS BASED ON TYPE ---
        if self.w > 2.0:
            # Wide Barrier -> Solid Red
            self.color = (0.9, 0.1, 0.1)
        elif self.h > 2.0:
            # Tall Tower -> Solid Dark Blue/Grey
            self.color = (0.2, 0.2, 0.35)
        else:
            # Spike -> Solid Orange
            self.color = (1.0, 0.5, 0.0)

    def update(self, dz):
        self.z += dz

    def draw(self):
        glDisable(GL_TEXTURE_2D)
        
        # 1. SPIKE (Pyramid Shape)
        # Small obstacles are drawn as sharp pyramids
        if self.w < 2.0 and self.h < 2.5:
            glPushMatrix()
            glTranslatef(self.x, self.y, self.z)
            glColor3f(*self.color)
            
            w, h, d = self.w / 2.0, self.h, self.d / 2.0
            
            glBegin(GL_TRIANGLES)
            # Four sides of the pyramid
            glVertex3f(0, h, 0); glVertex3f(-w, 0, d); glVertex3f(w, 0, d)
            glVertex3f(0, h, 0); glVertex3f(w, 0, d); glVertex3f(w, 0, -d)
            glVertex3f(0, h, 0); glVertex3f(w, 0, -d); glVertex3f(-w, 0, -d)
            glVertex3f(0, h, 0); glVertex3f(-w, 0, -d); glVertex3f(-w, 0, d)
            glEnd()
            
            # Base (bottom)
            glBegin(GL_QUADS)
            glVertex3f(-w, 0, d); glVertex3f(w, 0, d); glVertex3f(w, 0, -d); glVertex3f(-w, 0, -d)
            glEnd()
            glPopMatrix()

        # 2. WIDE BARRIER & TALL TOWER (Block Shape)
        # Drawn as simple solid cubes without stripes or details
        else:
            draw_cube(
                (self.x, self.y + self.h/2, self.z), 
                (self.w, self.h, self.d), 
                self.color
            )

    def rect(self):
        # AABB Collision box
        hx, hy, hz = self.w / 2, self.h / 2, self.d / 2
        
        # Make hitbox slightly forgiving for spikes
        if self.h < 2.5 and self.w < 2.0:
            scale = 0.7
            return (self.x - hx*scale, self.y, self.z - hz*scale), \
                   (self.x + hx*scale, self.y + self.h*scale, self.z + hz*scale)
            
        return (self.x - hx, self.y, self.z - hz), \
               (self.x + hx, self.y + self.h, self.z + hz)
class Building:
    def __init__(self, x, z, width=6.0, depth=6.0, height=10.0):
        self.x = x
        self.y = -1.0
        self.z = z
        self.w = width
        self.h = height
        self.d = depth
        
        # --- MIX OF DARK AND BRIGHT COLORS ---
        if random.random() < 0.5:
            # Bright Colors
            self.color = (
                random.uniform(0.6, 1.0), 
                random.uniform(0.6, 1.0), 
                random.uniform(0.6, 1.0)
            )
        else:
            # Dark Colors
            base = random.uniform(0.15, 0.3) 
            self.color = (
                base + random.uniform(-0.05, 0.1),
                base + random.uniform(-0.05, 0.1),
                base + random.uniform(-0.05, 0.1),
            )
        
        self.window_tint = (
            random.uniform(0.5, 1.0),
            random.uniform(0.5, 1.0),
            random.uniform(0.5, 1.0)
        )

    def draw_windows(self):
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(-1.0, -1.0)
        
        rows = int(self.h // 1.5)
        cols = int(self.d // 1.5) 

        # Calculate the geometric Left face of the building
        side_face_x = (self.x - self.w / 2.0) - 0.02

        for r in range(rows):
            for c in range(cols):
                if random.random() < 0.3: continue 

                if random.random() < 0.6:
                    glColor3f(1.0, 1.0, 1.0) 
                else:
                    glColor3f(*self.window_tint) 

                wy = self.y + 0.6 + r * 1.5
                wz = (self.z - self.d / 2.0) + 0.6 + c * 1.5

                glBegin(GL_QUADS)
                glVertex3f(side_face_x, wy - 0.35, wz - 0.35)
                glVertex3f(side_face_x, wy - 0.35, wz + 0.35)
                glVertex3f(side_face_x, wy + 0.35, wz + 0.35)
                glVertex3f(side_face_x, wy + 0.35, wz - 0.35)
                glEnd()

        glDisable(GL_POLYGON_OFFSET_FILL)

    def draw_lamp(self):
        """ Draws a street lamp attached to the sidewalk in front of the building """
        glDisable(GL_TEXTURE_2D)

        # 1. Determine direction towards the road
        # If building X is positive, road is to the Left (-1)
        # If building X is negative, road is to the Right (+1)
        dir_to_road = -1 if self.x > 0 else 1

        # 2. Position the pole
        # CHANGED: Reduced offset from 2.0 to 0.75 to move it closer to the building
        pole_x = self.x + (self.w / 2.0 * dir_to_road) + (0.75 * dir_to_road)
        pole_y = -1.0
        pole_z = self.z  
        
        pole_h = 3.5     
        arm_len = 1.5    

        # A. Draw Vertical Pole 
        draw_cube((pole_x, pole_y + pole_h/2, pole_z), (0.3, pole_h, 0.3), (0.15, 0.15, 0.2))

        # B. Draw Horizontal Arm 
        arm_center_x = pole_x + (arm_len/2.0 * dir_to_road)
        arm_height_y = pole_y + pole_h - 0.2
        draw_cube((arm_center_x, arm_height_y, pole_z), (arm_len, 0.25, 0.25), (0.15, 0.15, 0.2))

        # C. Draw The Light Bulb 
        light_x = pole_x + ((arm_len - 0.2) * dir_to_road)
        light_y = arm_height_y - 0.4
        
        # Bright Yellow/White Light
        draw_cube((light_x, light_y, pole_z), (0.5, 0.4, 0.5), (1.0, 1.0, 0.8))

    def update(self, dz):
        self.z += dz

    def draw(self):
        # Draw the main building
        draw_cube(
            (self.x, self.y + self.h / 2.0, self.z),
            (self.w, self.h, self.d),
            self.color
        )
        # Draw the details
        self.draw_lamp()

class Coin:
    def __init__(self, lane, x, z, size=0.8):
        self.lane = lane
        self.x = x
        self.y = -0.8
        self.z = z
        self.w = size
        self.h = size
        self.d = size * 0.5

    def rect(self):
        hx, hy, hz = self.w / 2.0, self.h / 2.0, self.d / 2.0
        return ((self.x - hx, self.y - hy, self.z - hz), (self.x + hx, self.y + hy, self.z + hz))

    def update(self, dz):
        self.z += dz

    def draw(self):
        draw_cube((self.x, self.y, self.z), (self.w, self.h, self.d), COL_COIN)

class Spawner:
    def __init__(self, lane_x_list, start_z, coin_chance=0.28):
        self.lane_x_list = lane_x_list
        self.start_z = start_z
        self.coin_chance = coin_chance

    def spawn_pattern(self, obstacles_list, coins_list):
        # random pattern: normal cube, wide wall, or tall wall
        lane = random.randint(0, len(self.lane_x_list) - 1)
        r = random.random()
        
        # 1. Spawn Obstacles
        if r < 0.6:
            # Normal obstacle (Cube)
            obstacles_list.append(
                Obstacle(lane, self.lane_x_list[lane], self.start_z, width=1.6, height=1.6)
            )
        elif r < 0.85:
            # Wide wall spanning two lanes (if possible)
            if lane == 0:
                left = 0
            elif lane == len(self.lane_x_list) - 1:
                left = len(self.lane_x_list) - 2
            else:
                left = lane - 1
            
            # Calculate center point between the two lanes
            center_x = (self.lane_x_list[left] + self.lane_x_list[left + 1]) / 2.0
            # Width is the distance between lanes * 2, minus a small gap
            width = abs(self.lane_x_list[left + 1] - self.lane_x_list[left]) * 2.0 - 0.3
            
            obj = Obstacle(left, center_x, self.start_z, width=width, height=1.8)
            obstacles_list.append(obj)
        else:
            # Tall wall
            obstacles_list.append(
                Obstacle(lane, self.lane_x_list[lane], self.start_z, width=1.8, height=3.5)
            )

        # 2. Spawn Coins
        if random.random() < self.coin_chance:
            cl = random.randint(0, len(self.lane_x_list) - 1)
            # Spawn coin slightly behind the obstacle (z + 8.0)
            coins_list.append(Coin(cl, self.lane_x_list[cl], self.start_z + 8.0))