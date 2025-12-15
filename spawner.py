# spawner.py
import random
from OpenGL.GL import *
from player import draw_cube
from utils import aabb

# Visual colors
COL_WALL = (0.9, 0.9, 0.9)
COL_COIN = (1.0, 0.85, 0.25)

class Obstacle:
    def __init__(self, lane, x, z, width=1.6, height=1.6, depth=1.6):
        self.lane = lane
        self.x = x
        self.y = -1.0
        self.z = z
        self.w = width
        self.h = height
        self.d = depth

    def rect(self):
        hx, hy, hz = self.w / 2.0, self.h / 2.0, self.d / 2.0
        return ((self.x - hx, self.y - hy, self.z - hz), (self.x + hx, self.y + hy, self.z + hz))

    def update(self, dz):
        self.z += dz

    def draw(self):
        # render as wall-like block (height may vary)
        draw_cube((self.x, self.y + self.h/2.0, self.z), (self.w, self.h, self.d), COL_WALL)
class Building:
    def __init__(self, x, z, width=6.0, depth=6.0, height=10.0):
        self.x = x
        self.y = -1.0
        self.z = z
        self.w = width
        self.h = height
        self.d = depth
        
        # --- MIX OF DARK AND BRIGHT COLORS (For the building walls) ---
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
            
        # Pre-calculate a random "Neon" color for some windows
        self.window_tint = (
            random.uniform(0.5, 1.0),
            random.uniform(0.5, 1.0),
            random.uniform(0.5, 1.0)
        )

   
    def update(self, dz):
        self.z += dz

    def draw(self):
        draw_cube(
            (self.x, self.y + self.h / 2.0, self.z),
            (self.w, self.h, self.d),
            self.color
        )

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