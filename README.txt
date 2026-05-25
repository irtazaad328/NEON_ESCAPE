# 🟦 Neon Escape

<p align="center">
  <img src="https://shields.io" alt="Python Version">
  <img src="https://shields.io" alt="Pygame">
  <img src="https://shields.io" alt="MIT License">
</p>

---

### 🚀 Cyberpunk Arcade Survival — Built with Pure Code

A fast-paced, neon-drenched arcade survival game. Pilot your ship through three escalating phases of absolute chaos. No external image sprites, no audio files, no heavy asset downloads—everything is rendered dynamically at runtime using pure mathematics and code.

---

## 🎮 The Gauntlet: 3 Phases of Chaos

> [!NOTE]
> Each phase introduces entirely new mechanics. Survival requires split-second adaptation.

* **Phase 1: Speed Survival**  
  ⚡ *The Warmup.* Projectiles start slow but aggressively ramp up in speed over time.
* **Phase 2: Constriction**  
  🧱 *The Squeeze.* The boundary walls actively close in on you. Survive the claustrophobic pressure.
* **Phase 3: Final Assault**  
  🔥 *The Payback.* The shields are down. Arm your weapons, shoot back, and blast your way to freedom.

---

## 🕹️ Cockpit Controls


| Target | Input Key | System Action |
| :--- | :--- | :--- |
| **Movement** | `Up Arrow` / `Space` | Fire jet boosters upward *(Release to fall)* |
| **Weapons** | `Z` | Fire lasers *(Phase 3 Only)* |
| **System** | `P` | Pause / Resume Game |
| **Navigation** | `Up` / `Down` | Browse Menu Items |
| **Selection** | `Enter` / `Mouse` | Confirm Selection / Click UI Buttons |
| **Settings** | `Left` / `Right` | Adjust Difficulty Level *(Main Menu)* |
| **Aborts** | `M` / `R` / `ESC` | Main Menu / Retry / Emergency Quit |

---

## 📊 Tactical Data & Scoring

### ⚙️ Combat Difficulty
Choose your fate: **Easy**, **Medium**, or **Hard**. Higher difficulties dynamically scale:
* Enemy projectile velocities & spawn frequencies
* Wall constriction acceleration rates
* Damage scaling parameters & Final Boss aggression

### 🏆 Score Multipliers
* **Standard Dodge:** `+1 Point`
* **Near-Miss Bonus:** `+2 Points` *(Awarded for cutting it closer than 60px)*
* **Combo Streak:** `+N Points` *(Calculated as: Current Combo − 2)*

🎯 **Milestone Rewards Displayed At:** `10` / `25` / `50` / `100` / `200` / `500`

---

## 💻 Quickstart Installation

Ready to fly? Copy and paste these commands into your terminal:

```bash
# 1. Clone the repository
git clone https://github.com
cd neon-escape

# 2. Install core modules
pip install pygame numpy

# 3. Launch the matrix
python neon_escape.py
```

---

## 📜 Legal Matrix
This project is operating under the **MIT License**. You are completely free to fork, modify, destroy, or commercially distribute this code as long as the original copyright remains intact. See the [LICENSE](LICENSE) file for the full legal text.
