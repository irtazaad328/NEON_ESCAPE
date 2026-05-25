# Neon Escape 🟦
**Cyberpunk Arcade Survival** — built with Python & Pygame

A fast-paced arcade survival game where you pilot a neon ship through three escalating phases of chaos: dodging projectiles, surviving crushing walls, and blasting through a final assault — all rendered with pure code, no external assets needed.

---

## Gameplay

| Phase | Name | Description |
|-------|------|-------------|
| 1 | Speed Survival | Projectiles start slow and ramp up over time |
| 2 | Constriction | Walls close in — survive the squeeze |
| 3 | Final Assault | Shoot back and escape the last wave |

---

## Requirements

- Python 3.8+
- pygame
- numpy

---

## Installation & Run

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/neon-escape.git
cd neon-escape

# 2. Install dependencies
pip install pygame numpy

# 3. Run the game
python neon_escape.py
```

No image sprites or sound files required — everything is generated at runtime.

---

## Controls

| Key | Action |
|-----|--------|
| `Up` / `Space` | Jet boost upward |
| `Space` (hold) | Fall with gravity |
| `Z` | Shoot (Phase 3 only) |
| `P` | Pause / Resume |
| `Left` / `Right` | Change difficulty (menu) |
| `Up` / `Down` | Navigate menu items |
| `Enter` | Confirm selection |
| `Mouse` | Hover and click buttons |
| `M` | Main menu (from pause or game over) |
| `R` | Retry (game over screen) |
| `ESC` | Quit |

---

## Scoring

| Event | Points |
|-------|--------|
| Projectile dodged | +1 |
| Near-miss (within 60px) | +2 |
| Combo bonus | +N (N = combo count − 2) |

Milestones are shown at: **10 / 25 / 50 / 100 / 200 / 500**

---

## Difficulty Levels

Choose from **Easy**, **Medium**, or **Hard** at the main menu. Difficulty affects projectile speed, spawn rate, wall constriction speed, damage values, and boss speed.

---

## License

MIT License — free to use, modify, and distribute.