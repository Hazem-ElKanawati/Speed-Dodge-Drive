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
        # random pattern: normal cube, wide wall, or tall wall + possible coin
        lane = random.randint(0, len(self.lane_x_list) - 1)
        r = random.random()
        if r < 0.6:
            # normal obstacle in its lane
            obstacles_list.append(Obstacle(lane, self.lane_x_list[lane], self.start_z, width=1.6, height=1.6))
        elif r < 0.85:
            # wide wall spanning two lanes when possible
            # choose a pair of lanes: ensure we can center between them
            if lane == 0:
                left = 0
            elif lane == len(self.lane_x_list) - 1:
                left = len(self.lane_x_list) - 2
            else:
                left = lane - 1
            # width equals distance between centers of two lanes minus small gap
            center_x = (self.lane_x_list[left] + self.lane_x_list[left + 1]) / 2.0
            width = abs(self.lane_x_list[left + 1] - self.lane_x_list[left]) * 2.0 - 0.3
            obj = Obstacle(left, center_x, self.start_z, width=width, height=1.8)
            # set lane to left to approximate blocking logic (works for lane-block checks)
            obj.lane = left
            obstacles_list.append(obj)
        else:
            # tall wall
            obstacles_list.append(Obstacle(lane, self.lane_x_list[lane], self.start_z, width=1.8, height=2.4))

        # coin spawn
        if random.random() < self.coin_chance:
            cl = random.randint(0, len(self.lane_x_list) - 1)
            coins_list.append(Coin(cl, self.lane_x_list[cl], self.start_z + 8.0))
