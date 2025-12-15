# game.py
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import time
import random

from utils import load_high_score, save_high_score, aabb
from player import Player
from spawner import Spawner
from ui import Overlay
from utils import load_texture
from spawner import Spawner, Building


# Config
WIN_W, WIN_H = 900, 900
FPS = 60
LANE_COUNT = 3
LANE_SPACING = 3.0
LANE_X = [-(LANE_SPACING) + i * LANE_SPACING for i in range(LANE_COUNT)]
CAMERA_POS = (0.0, 3.2, 12.0)
CAMERA_LOOK_AT = (0.0, -0.2, 0.0)
PLAYER_Z = 2.0
OBSTACLE_START_Z = -80.0
OBSTACLE_SPEED = 20.0
SPAWN_INTERVAL = 0.8
COIN_SPAWN_CHANCE = 0.28
road_half_width = (LANE_SPACING * (LANE_COUNT - 1)) / 2.0
side_offset = road_half_width + 12
BLOCK_LENGTH = 15.0
BUILDING_SPAWN_BLOCKS = 10
BUILDING_SPAWN_AHEAD = BLOCK_LENGTH * BUILDING_SPAWN_BLOCKS  # = 30.0


# Lateral move scaling defaults (tie lateral duration to forward speed)
BASE_FORWARD_SPEED = OBSTACLE_SPEED
BASE_MOVE_DURATION = 0.06   # how long lane-change takes at base speed
MIN_MOVE_DURATION = 0.02    # fastest allowed lateral move
MAX_MOVE_DURATION = 0.18    # slowest allowed lateral move

def draw_ground():
    glColor3f(0.35, 0.35, 0.35)
    glBegin(GL_QUADS)
    glVertex3f(-40.0, -2.4, -300.0); glVertex3f(40.0, -2.4, -300.0)
    glVertex3f(40.0, -2.4, 80.0); glVertex3f(-40.0, -2.4, 80.0)
    glEnd()
    # lane separator lines (BETWEEN lanes)
    for i in range(LANE_COUNT - 1):
        x = -LANE_SPACING / 2 + i * LANE_SPACING

        glColor3f(0.15, 0.15, 0.18)
        glBegin(GL_QUADS)
        glVertex3f(x - 0.06, -2.35, -300.0)
        glVertex3f(x + 0.06, -2.35, -300.0)
        glVertex3f(x + 0.06, -2.35, 80.0)
        glVertex3f(x - 0.06, -2.35, 80.0)
        glEnd()

class Game:
    def __init__(self):
        pygame.init()
        flags = DOUBLEBUF | OPENGL
        self.screen = pygame.display.set_mode((WIN_W, WIN_H), flags)
        pygame.display.set_caption("Lane3D Runner - Modular")
        glEnable(GL_DEPTH_TEST)
        #glEnable(GL_CULL_FACE)
        glClearColor(0.05, 0.05, 0.06, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, WIN_W / WIN_H, 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)
        self.sky_tex = load_texture("assets/sky.jpg")
        print("[DEBUG] sky texture id:", self.sky_tex)

        self.clock = pygame.time.Clock()
        self.player = Player(LANE_X, start_lane=1, y=-1.0, z=PLAYER_Z)
        self.next_building_spawn_z = self.player.z - BUILDING_SPAWN_AHEAD

        print("[DEBUG] Player start lane:", self.player.lane)
        print("[DEBUG] Player start x:", self.player.x)

        self.buildings =[]
        self.obstacles = []
        self.coins = []
        self.spawner = Spawner(LANE_X, OBSTACLE_START_Z, coin_chance=COIN_SPAWN_CHANCE)
        self.spawn_timer = 0.0
        self.spawn_interval = SPAWN_INTERVAL
        self.speed = OBSTACLE_SPEED
        self.score = 0
        self.highscore = load_high_score()
        print("[DEBUG] loaded highscore:", self.highscore)  # confirm load on startup
        self.state = "menu"  # menu / playing / gameover
        self.running = True

        self.overlay = Overlay(WIN_W, WIN_H)
        self.font = pygame.font.SysFont("Arial", 26)
        self.large_font = pygame.font.SysFont("Arial", 44)
       

        

    def spawn(self):
        self.spawner.spawn_pattern(self.obstacles, self.coins)

    def reset(self):
        self.player = Player(LANE_X, start_lane=1, y=-1.0, z=PLAYER_Z)
        self.obstacles = []
        self.coins = []
        self.buildings = []
        
        # Start spawn cursor slightly ahead of camera
        self.next_building_spawn_z = CAMERA_POS[2] + 5.0

        # Pre-fill world
        # CHANGED: range(100) -> range(40). 
        # Since BLOCK_LENGTH is now 15.0, 40 blocks covers 600 units of distance.
        for _ in range(40):
            self.spawn_buildings(self.next_building_spawn_z)
            self.next_building_spawn_z -= BLOCK_LENGTH

        self.spawn_timer = 0.0
        self.spawn_interval = SPAWN_INTERVAL
        self.speed = OBSTACLE_SPEED
        self.score = 0
        self.state = "playing"

    def toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def handle_key(self, key):
        if key == K_f:
            self.toggle_fullscreen()
            return
        if self.state == "menu":
            if key == K_SPACE:
                self.reset()
        elif self.state == "playing":
            if key == K_LEFT:
                _ = self.player.request_move(-1, self.obstacles)
            elif key == K_RIGHT:
                _ = self.player.request_move(1, self.obstacles)
        elif self.state == "gameover":
            if key == K_r:
                self.highscore = max(self.highscore, self.score)
                save_high_score(self.highscore)
                self.reset()

    def update(self, dt):
        PARALLAX = 0.35

        # STOP updating if game is over
        if self.state != "playing":
            return

        # 1. Base Acceleration (gradually gets faster over time naturally)
        self.speed += dt * 0.9

        # 2. Controls Feel (Scale lateral speed)
        scaled = BASE_MOVE_DURATION * (BASE_FORWARD_SPEED / max(1e-6, self.speed))
        self.player.move_duration = max(MIN_MOVE_DURATION, min(MAX_MOVE_DURATION, scaled))

        # 3. Movement Calculations
        dz = self.speed * dt
        
        # Move the invisible "spawn cursor" so it stays with the moving world
        self.next_building_spawn_z += dz * PARALLAX

        # 4. Update Objects (Obstacles & Coins)
        for o in self.obstacles:
            o.update(dz)
        for c in self.coins:
            c.update(dz)

        # Remove objects behind camera
        self.obstacles = [o for o in self.obstacles if o.z < CAMERA_POS[2] + 8.0]
        self.coins = [c for c in self.coins if c.z < CAMERA_POS[2] + 8.0]

        # 5. Update Player
        self.player.update(dt, self.obstacles)

        # 6. Collision Detection
        px = self.player.x
        prev_px = getattr(self.player, "prev_x", px)
        hx = self.player.w / 2.0
        hy = self.player.h / 2.0
        hz = self.player.d / 2.0

        swept_min_x = min(prev_px, px) - hx
        swept_max_x = max(prev_px, px) + hx
        pmin_swept = (swept_min_x, self.player.y - hy, self.player.z - hz)
        pmax_swept = (swept_max_x, self.player.y + hy, self.player.z + hz)

        # --- COIN COLLECTION & SPEED BOOST ---
        for c in list(self.coins):
            cmin, cmax = c.rect()
            if aabb(pmin_swept, pmax_swept, cmin, cmax):
                try: self.coins.remove(c)
                except ValueError: pass
                
                self.score += 10
                self.player.color = (0.48, 1.0, 0.6)
                self.player.flash = 0.25

                # === SPEED BOOST LOGIC ===
                # I used larger numbers (2.0, 4.0) because 0.10 is too small to notice
                if self.score == 100:
                    self.speed += 2.0  # Boost at 100
                    print(f"Speed Up! Level 1 (Speed: {self.speed:.1f})")
                elif self.score == 150:
                    self.speed += 3.0  # Bigger boost at 150
                    print(f"Speed Up! Level 2 (Speed: {self.speed:.1f})")
                elif self.score > 150 and self.score % 50 == 0:
                    self.speed += 1.5  # Continuous boost every 50 points after
                    print(f"Speed Up! (Speed: {self.speed:.1f})")
                # =========================

        # Obstacles
        for o in list(self.obstacles):
            omin, omax = o.rect()
            if aabb(pmin_swept, pmax_swept, omin, omax):
                self.player.color = (1.0, 0.26, 0.26)
                self.state = "gameover"
                self.highscore = max(self.highscore, self.score)
                save_high_score(self.highscore)
                break
        
        # 7. Spawn Pattern for Obstacles
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self.spawn()
            self.spawn_interval = max(0.4, self.spawn_interval * 0.995)
        
        # 8. Infinite Building Generation
        for b in self.buildings:
             b.update(dz * PARALLAX)
        
        self.buildings = [b for b in self.buildings if b.z < CAMERA_POS[2] + 20.0]
        
        spawn_horizon = self.player.z - BUILDING_SPAWN_AHEAD
        while self.next_building_spawn_z >= spawn_horizon:
            self.spawn_buildings(self.next_building_spawn_z) 
            self.next_building_spawn_z -= BLOCK_LENGTH

    def look_at_camera(self):
        glLoadIdentity()
        px= self.player.x
        gluLookAt(
        px, CAMERA_POS[1], CAMERA_POS[2],   # camera follows player X
        px, CAMERA_LOOK_AT[1], CAMERA_LOOK_AT[2],
        0.0, 1.0, 0.0
    )
        
    def draw_sky(self):
    # --- Save state ---
        glDisable(GL_DEPTH_TEST)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(-1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.sky_tex)

    # IMPORTANT: reset color so texture is not darkened
        glColor3f(1.0, 1.0, 1.0)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(-1, -0.6)
        glTexCoord2f(1, 0); glVertex2f( 1, -0.6)
        glTexCoord2f(1, 1); glVertex2f( 1,  1)
        glTexCoord2f(0, 1); glVertex2f(-1,  1)
        glEnd()


        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)


    def draw_scene(self):
        draw_ground()
        for b in self.buildings:
            b.draw()
        for c in self.coins: c.draw()
        for o in self.obstacles: o.draw()
        self.player.draw()

    def build_overlay(self):
        """
        Render overlay surface text and panel.
        - Menu/gameover: full center panel for readability.
        - Playing: only draw a small opaque top bar for score & highscore.
        """
        surf = self.overlay.surface

        if self.state == "playing":
            # Playing: keep most of overlay transparent so 3D is visible.
            surf.fill((0, 0, 0, 0))  # fully transparent
            # Draw small top bar for score/highscore so it's readable
            bar_h = 44
            pygame.draw.rect(surf, (12, 12, 14, 220), (0, 0, WIN_W, bar_h))
            # Score and highscore (bright)
            score_surf = self.font.render(f"Score: {self.score}", True, (255,255,220))
            surf.blit(score_surf, (12, 8))
            hs_surf = self.font.render(f"High: {self.highscore}", True, (255,255,220))
            surf.blit(hs_surf, (WIN_W - hs_surf.get_width() - 12, 8))
        else:
            # Menu or gameover: show a full semi-opaque panel so text is obvious
            surf.fill((10, 10, 12, 220))
            # Score and highscore (bright) at top corners
            score_surf = self.font.render(f"Score: {self.score}", True, (255,255,220))
            surf.blit(score_surf, (12, 8))
            hs_surf = self.font.render(f"High: {self.highscore}", True, (255,255,220))
            surf.blit(hs_surf, (WIN_W - hs_surf.get_width() - 12, 8))

            if self.state == "menu":
                title = self.large_font.render("Lane3D Runner", True, (255, 240, 140))
                instruct = self.font.render("Press SPACE to start  •  F = fullscreen  •  ESC = quit", True, (240,240,240))
                surf.blit(title, (WIN_W//2 - title.get_width()//2, WIN_H//2 - 80))
                surf.blit(instruct, (WIN_W//2 - instruct.get_width()//2, WIN_H//2 - 20))
                start_hint = self.large_font.render("Press SPACE to start", True, (255, 220, 80))
                surf.blit(start_hint, (WIN_W//2 - start_hint.get_width()//2, WIN_H//2 + 30))
            elif self.state == "gameover":
                t = self.large_font.render("GAME OVER", True, (255,255,255))
                t2 = self.font.render(f"Final Score: {self.score}   Press R to restart", True, (240,240,240))
                surf.blit(t, (WIN_W//2 - t.get_width()//2, WIN_H//2 - 80))
                surf.blit(t2, (WIN_W//2 - t2.get_width()//2, WIN_H//2 - 20))

        # Note: ui.draw_fullscreen() will handle converting/drawing the surface via glWindowPos/glDrawPixels

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == QUIT:
                    self.running = False
                elif ev.type == KEYDOWN:
                    if ev.key == K_ESCAPE:
                        self.running = False
                    else:
                        self.handle_key(ev.key)

            self.update(dt)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw_sky()          
            self.look_at_camera()
            self.draw_scene()
            # build overlay and draw
            self.build_overlay()
            self.overlay.draw_fullscreen()
            pygame.display.flip()
        pygame.quit()

    def spawn_buildings(self, z_val):
        # We use the specific Z passed to the function, not the Camera position
        # This ensures they lock to the grid perfectly.
        
        road_half_width = (LANE_SPACING * (LANE_COUNT - 1)) / 2.0
        side_offset = road_half_width + 4.5

        for side in (-1, 1):  # left & right
            x = side * side_offset
            
            # Add slight random offset to Z, but keep it centered on z_val
            z = z_val + random.uniform(-1.0, 1.0)

            if random.random() < 0.7:
                height = random.uniform(4.0, 10.0)
            else:
                height = random.uniform(12.0, 22.0)
            
            width  = random.uniform(2.5, 4.0)
            depth  = random.uniform(8.0, 12.0)

            self.buildings.append(
                Building(x, z, width=width, depth=depth, height=height)
            )



