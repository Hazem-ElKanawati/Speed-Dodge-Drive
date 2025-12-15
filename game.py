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

# Config
WIN_W, WIN_H = 900, 900
FPS = 60
LANE_COUNT = 3
LANE_SPACING = 3.0
LANE_X = [-(LANE_SPACING) + i * LANE_SPACING for i in range(LANE_COUNT)]
CAMERA_POS = (0.0, 3.2, 12.0)
CAMERA_LOOK_AT = (0.0, 0.2, 0.0)
PLAYER_Z = 2.0
OBSTACLE_START_Z = -80.0
OBSTACLE_SPEED = 20.0
SPAWN_INTERVAL = 0.8
COIN_SPAWN_CHANCE = 0.28

# Lateral move scaling defaults (tie lateral duration to forward speed)
BASE_FORWARD_SPEED = OBSTACLE_SPEED
BASE_MOVE_DURATION = 0.06   # how long lane-change takes at base speed
MIN_MOVE_DURATION = 0.02    # fastest allowed lateral move
MAX_MOVE_DURATION = 0.18    # slowest allowed lateral move

def draw_ground():
    glColor3f(0.10, 0.10, 0.12)
    glBegin(GL_QUADS)
    glVertex3f(-40.0, -2.4, -300.0); glVertex3f(40.0, -2.4, -300.0)
    glVertex3f(40.0, -2.4, 80.0); glVertex3f(-40.0, -2.4, 80.0)
    glEnd()
    for i in range(LANE_COUNT + 1):
        x = -LANE_SPACING + i * LANE_SPACING
        glColor3f(0.15, 0.15, 0.18)
        glBegin(GL_QUADS)
        glVertex3f(x - 0.06, -2.35, -300.0); glVertex3f(x + 0.06, -2.35, -300.0)
        glVertex3f(x + 0.06, -2.35, 80.0); glVertex3f(x - 0.06, -2.35, 80.0)
        glEnd()

class Game:
    def __init__(self):
        pygame.init()
        flags = DOUBLEBUF | OPENGL
        self.screen = pygame.display.set_mode((WIN_W, WIN_H), flags)
        pygame.display.set_caption("Lane3D Runner - Modular")
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glClearColor(0.05, 0.05, 0.06, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, WIN_W / WIN_H, 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)

        self.clock = pygame.time.Clock()
        self.player = Player(LANE_X, start_lane=1, y=-1.0, z=PLAYER_Z)
        self.obstacles = []
        self.coins = []
        self.spawner = Spawner(LANE_X, OBSTACLE_START_Z, coin_chance=COIN_SPAWN_CHANCE)
        self.spawn_timer = 0.0
        self.spawn_interval = SPAWN_INTERVAL
        self.speed = OBSTACLE_SPEED
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.combo_timeout = 3.0  # seconds to get next coin
        self.max_combo = 0  # track best combo this run
        self.highscore = load_high_score()
        print("[DEBUG] loaded highscore:", self.highscore)  # confirm load on startup
        self.state = "menu"  # menu / playing / gameover
        self.running = True
        

        self.overlay = Overlay(WIN_W, WIN_H)
        self.font = pygame.font.SysFont("Arial", 26)
        self.large_font = pygame.font.SysFont("Arial", 44)
        self.particles = []

    def spawn(self):
        self.spawner.spawn_pattern(self.obstacles, self.coins)

    def reset(self):
        self.player = Player(LANE_X, start_lane=1, y=-1.0, z=PLAYER_Z)
        self.obstacles = []
        self.coins = []
        self.spawn_timer = 0.0
        self.spawn_interval = SPAWN_INTERVAL
        self.speed = OBSTACLE_SPEED
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.max_combo = 0
        self.state = "playing"
        self.particles = []

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
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive()]
        if self.state != "playing":
            return

        # accelerate forward speed slightly every frame
        self.speed += dt * 0.9

        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                # Combo expired! Show it briefly then reset
                self.combo = 0
                self.combo_timer = 0.0

        # scale lateral move duration with forward speed so feel stays consistent
        # higher forward speed -> shorter lateral duration (snappier)
        scaled = BASE_MOVE_DURATION * (BASE_FORWARD_SPEED / max(1e-6, self.speed))
        self.player.move_duration = max(MIN_MOVE_DURATION, min(MAX_MOVE_DURATION, scaled))

        # spawning logic
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self.spawn()
            self.spawn_interval = max(0.4, self.spawn_interval * 0.995)

        dz = self.speed * dt
        for o in self.obstacles:
            o.update(dz)
        for c in self.coins:
            c.update(dz)

        # remove objects that passed camera
        self.obstacles = [o for o in self.obstacles if o.z < CAMERA_POS[2] + 8.0]
        self.coins = [c for c in self.coins if c.z < CAMERA_POS[2] + 8.0]

        # update player (this sets prev_x then interpolates to x)
        self.player.update(dt, self.obstacles)

        # Build swept AABB for the player covering lateral movement this frame
        px = self.player.x
        prev_px = getattr(self.player, "prev_x", px)
        hx = self.player.w / 2.0
        hy = self.player.h / 2.0
        hz = self.player.d / 2.0

        swept_min_x = min(prev_px, px) - hx
        swept_max_x = max(prev_px, px) + hx
        pmin_swept = (swept_min_x, self.player.y - hy, self.player.z - hz)
        pmax_swept = (swept_max_x, self.player.y + hy, self.player.z + hz)

        # coin collection using swept AABB (so coins collected mid-slide)
        for c in list(self.coins):
            cmin, cmax = c.rect()
            if aabb(pmin_swept, pmax_swept, cmin, cmax):
                try:
                    self.coins.remove(c)
                except ValueError:
                    pass
                
                # COMBO SYSTEM:
                self.combo += 1
                self.combo_timer = self.combo_timeout  # reset timer
                self.max_combo = max(self.max_combo, self.combo)
                
                # Score multiplier based on combo
                points = 10 * self.combo  # 10, 20, 30, 40...
                self.score += points
                
                self.player.color = (0.48, 1.0, 0.6)
                self.player.flash = 0.25
                
                # MORE PARTICLES for higher combos!
                base_particles = 8
                bonus_particles = min(self.combo * 2, 20)  # up to +20 extra
                num_particles = random.randint(base_particles, base_particles + bonus_particles)
                for _ in range(num_particles):
                    self.particles.append(Particle(c.x, c.y, c.z))
                
                # Console feedback for debugging
                print(f"[COMBO x{self.combo}] +{points} points!")


        # obstacle collision using swept AABB so collisions during slide are fair
        for o in list(self.obstacles):
            omin, omax = o.rect()
            if aabb(pmin_swept, pmax_swept, omin, omax):
                self.player.color = (1.0, 0.26, 0.26)
                self.state = "gameover"
                self.highscore = max(self.highscore, self.score)
                save_high_score(self.highscore)
                
                # Show final combo stats
                print(f"[GAME OVER] Max combo: {self.max_combo}x")
                
                break

    def look_at_camera(self):
        glLoadIdentity()
        gluLookAt(CAMERA_POS[0], CAMERA_POS[1], CAMERA_POS[2],
                  CAMERA_LOOK_AT[0], CAMERA_LOOK_AT[1], CAMERA_LOOK_AT[2],
                  0.0, 1.0, 0.0)

    def draw_scene(self):
        draw_ground()
        for c in self.coins: c.draw()
        for o in self.obstacles: o.draw()
        self.player.draw()
        # Draw particles with blending for fade effect
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for p in self.particles:
            p.draw()
        glDisable(GL_BLEND)

    def build_overlay(self):
        """
        Render overlay surface text and panel.
        - Menu/gameover: full center panel for readability.
        - Playing: only draw a small opaque top bar for score & highscore.
        """
        surf = self.overlay.surface

        if self.state == "playing":
            surf.fill((0, 0, 0, 0))
            bar_h = 44
            pygame.draw.rect(surf, (12, 12, 14, 220), (0, 0, WIN_W, bar_h))
            
            # Score (left)
            score_surf = self.font.render(f"Score: {self.score}", True, (255,255,220))
            surf.blit(score_surf, (12, 8))
            
            # Highscore (right)
            hs_surf = self.font.render(f"High: {self.highscore}", True, (255,255,220))
            surf.blit(hs_surf, (WIN_W - hs_surf.get_width() - 12, 8))
            
            # COMBO DISPLAY (center)
            if self.combo > 1:  # only show if combo is 2+
                # Color changes with combo level
                if self.combo < 5:
                    combo_color = (255, 255, 100)  # yellow
                elif self.combo < 10:
                    combo_color = (255, 180, 50)   # orange
                else:
                    combo_color = (255, 80, 80)    # red (on fire!)
                
                combo_text = f"COMBO x{self.combo}"
                combo_surf = self.large_font.render(combo_text, True, combo_color)
                combo_x = WIN_W // 2 - combo_surf.get_width() // 2
                combo_y = 50
                
                # Add pulsing effect for high combos
                if self.combo >= 5:
                    import math
                    pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 10
                    combo_y = int(50 + pulse)
                
                surf.blit(combo_surf, (combo_x, combo_y))
                
                # Timer bar showing time left
                if self.combo_timer > 0:
                    bar_width = 200
                    bar_height = 8
                    bar_x = WIN_W // 2 - bar_width // 2
                    bar_y = combo_y + combo_surf.get_height() + 5
                    
                    # Background bar (dark)
                    pygame.draw.rect(surf, (40, 40, 40, 200), 
                                   (bar_x, bar_y, bar_width, bar_height))
                    
                    # Progress bar (colored by time remaining)
                    progress = self.combo_timer / self.combo_timeout
                    progress_width = int(bar_width * progress)
                    
                    if progress > 0.5:
                        bar_color = (80, 255, 80)   # green
                    elif progress > 0.25:
                        bar_color = (255, 255, 80)  # yellow
                    else:
                        bar_color = (255, 80, 80)   # red (almost out!)
                    
                    pygame.draw.rect(surf, bar_color, 
                                   (bar_x, bar_y, progress_width, bar_height))

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
                surf.blit(t, (WIN_W//2 - t.get_width()//2, WIN_H//2 - 100))
                
                # Final score
                t2 = self.font.render(f"Final Score: {self.score}", True, (240,240,240))
                surf.blit(t2, (WIN_W//2 - t2.get_width()//2, WIN_H//2 - 40))
                
                # Max combo achieved
                combo_text = f"Max Combo: {self.max_combo}x"
                combo_color = (255, 200, 80) if self.max_combo >= 5 else (200, 200, 200)
                t3 = self.font.render(combo_text, True, combo_color)
                surf.blit(t3, (WIN_W//2 - t3.get_width()//2, WIN_H//2 - 5))
                
                # Restart instruction
                t4 = self.font.render("Press R to restart", True, (180, 180, 180))
                surf.blit(t4, (WIN_W//2 - t4.get_width()//2, WIN_H//2 + 30))

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
            self.look_at_camera()
            self.draw_scene()
            # build overlay and draw
            self.build_overlay()
            self.overlay.draw_fullscreen()
            pygame.display.flip()
        pygame.quit()

class Particle:
    """A single particle that flies outward and fades away"""
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        # Random velocity in X and Y (outward burst effect)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(1, 4)  # mostly upward
        self.vz = random.uniform(-1, 1)  # slight forward/back
        # Lifetime in seconds
        self.life = random.uniform(0.3, 0.6)
        self.max_life = self.life
        # Size shrinks over time
        self.size = random.uniform(0.2, 0.4)
        
    def update(self, dt):
        """Move particle and decrease lifetime"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        # Gravity effect
        self.vy -= 5.0 * dt  # pulls particles down
        self.life -= dt
        
    def is_alive(self):
        return self.life > 0
        
    def draw(self):
        """Draw particle with fade-out effect"""
        if self.life > 0:
            # Fade alpha based on remaining life
            alpha = self.life / self.max_life
            # Color: golden yellow
            glColor4f(1.0, 0.85, 0.25, alpha)
            
            # Draw as small cube
            from player import draw_cube
            draw_cube((self.x, self.y, self.z), 
                     (self.size, self.size, self.size), 
                     (1.0, 0.85, 0.25))