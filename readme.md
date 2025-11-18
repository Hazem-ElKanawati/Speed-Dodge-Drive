# Lane3D Runner
A 3D endless‑runner built using **Pygame + PyOpenGL** only. The player controls a car that moves between 3 lanes, avoids obstacles, collects coins, and tries to beat the highscore.

This project demonstrates:
- Basic 3D rendering using OpenGL
- Player movement & lane interpolation
- Swept‑AABB collision detection
- Dynamic difficulty scaling
- HUD overlay drawn with glDrawPixels
- Highscore persistence
- Clean modular architecture for teamwork

---

## 🚀 How to Run
1. Install Python 3.10+ (3.12 works).
2. Install dependencies:
   ```bash
   pip install pygame PyOpenGL PyOpenGL_accelerate
   ```
3. Run the game:
   ```bash
   python main.py
   ```

---

## 🎮 Controls
| Key | Action |
|-----|--------|
| **SPACE** | Start game from menu |
| **LEFT / RIGHT** | Change lanes |
| **F** | Toggle fullscreen |
| **R** | Restart after Game Over |
| **ESC** | Quit game |

---

## 📂 Project Structure
```
project/
│
├── main.py            # Entry point – starts Game()
├── game.py            # Game loop, updating, drawing, overlay, difficulty
├── player.py          # Player class, car model, movement logic, swept motion
├── spawner.py         # Obstacle & coin classes + spawn patterns
├── ui.py              # Overlay (menu, HUD) rendered via glDrawPixels
├── utils.py           # Highscore saving/loading, AABB collision helper
├── lane3d_highscore.txt   # Automatically created highscore file
```

---

## 🧩 Division of Work (3‑Person Team)
### **Person A – Player & Collisions**
- `player.py` movement, interpolation, queue system
- Swept‑AABB integration in `game.py`
- Player hit/collect effects

### **Person B – Spawner & Obstacles**
- `spawner.py` spawn logic, patterns, difficulty tuning
- Add new obstacle types or lane variations
- Adjust heights, widths, randomness

### **Person C – UI, Menu, Overlay, Glue**
- `ui.py` overlay & text rendering
- `game.py` HUD building, state transitions
- Highscore file handling (utils)
- Optional: sounds, polish, fullscreen behavior

---

## 🧠 How the Game Works (Simplified)
### 1. **Rendering**
- Ground, car, obstacles, coins rendered with raw OpenGL primitives.
- Camera fixed behind the player.

### 2. **Movement System**
- Player presses LEFT/RIGHT → lane change is queued.
- Movement uses smooth interpolation between lane centers.
- Movement speed scales with forward speed for consistent feel.

### 3. **Collision Detection**
We use **swept‑AABB**:
- Track previous X (`prev_x`).
- During a slide, the collision box covers the full swept path.
- Prevents “ghost hits” or unfair misses.

### 4. **Difficulty Scaling**
- Forward speed increases over time.
- Spawn interval decreases gradually.
- Lateral movement duration auto‑scales.

### 5. **Overlay System**
- Render menu / score text onto a transparent pygame surface.
- Draw to screen via `glWindowPos2i` + `glDrawPixels`.
- Avoids texture‑mode bugs on some GPUs.

---

## 🔧 Tuning (Where to Adjust)
### In `game.py`:
- `OBSTACLE_SPEED` – starting speed
- `SPAWN_INTERVAL` – base spawn rate
- `COIN_SPAWN_CHANCE`
- Lateral movement scaling constants

### In `player.py`:
- Player size
- Movement duration curve
- Queue behaviour

### In `spawner.py`:
- Obstacle sizes & types
- Coin spacing

---

## 🧪 Testing Checklist
- [ ] Menu appears and is readable
- [ ] Press SPACE → game starts
- [ ] Score & highscore visible during gameplay
- [ ] Lane change works every time without delay
- [ ] Fair collisions during sliding (swept‑AABB)
- [ ] Coins collected even when sliding
- [ ] Game Over triggers correctly
- [ ] Highscore saved to file on restart
- [ ] Fullscreen toggle works

---

## ❓ Troubleshooting
### Overlay not visible
- Ensure `ui.py` uses `glWindowPos2i(0, 0)`.
- Ensure the surface is RGBA with alpha.

### Movement feels unresponsive
- Check `player.move_duration` scaling.
- Ensure no obstacle‑blocking logic is left in `request_move`.

### Highscore not saving
- Make sure project folder is writable.
- The file auto‑creates when the score updates.

---

## ✔️ Final Notes
- The entire game follows the assignment constraints: **OpenGL + Pygame only**, no engines.
- Code is modular to make teamwork easy.
- Swept‑AABB and move‑scaling make the gameplay feel professional.

Good luck with your submission! If you need a CONTRIBUTING.md or presentation script, ask any time.

