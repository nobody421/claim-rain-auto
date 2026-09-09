# CLAIM RAIN Auto

Auto-clicker for the big orange **CLAIM RAIN** button on DonutSurge + dual MiniCPM brain (text + vision).

## Models

```bash
ollama pull openbmb/minicpm5          # text reasoning (~0.7 GB)
ollama pull openbmb/minicpm-v4.6      # vision (~1.6 GB)
```

## Install

```bash
pip install ollama pyautogui pillow numpy PyQt5 requests opencv-python
```

## Scripts

| File | What it does |
|------|--------------|
| `claimer_template.py` | Fast OpenCV template match (needs `claim_rain.png`) |
| `claimer_vision.py` | Uses MiniCPM-V to decide if CLAIM RAIN is visible |
| `dual_chat.py` | Talk to both brains (text + vision + screen) |

## Quick start (template version)

1. Crop the big orange CLAIM RAIN button → save as `claim_rain.png`
2. `python claimer_template.py`
3. Hit **ON**

## Quick start (vision version)

```bash
python claimer_vision.py
```

## Dual chat

```bash
python dual_chat.py
```

Made by discord.gg/nullstate :)
