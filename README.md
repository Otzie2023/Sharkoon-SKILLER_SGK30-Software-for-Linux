# Sharkoon SKILLER SGK30 – Linux Lighting Control

The **Sharkoon SKILLER SGK30** keyboard officially supports **Windows only**.  
This project provides an **unofficial Linux solution** to control the keyboard lighting using custom JSON lighting patterns.

---

## ✨ Features

- Control RGB lighting under Linux
- Load custom lighting patterns from JSON files
- Select animation frames
- Adjustable playback speed

---

## 📦 Requirements

- Linux system
- Python 3
- `sudo` privileges (required for USB device access)

---

## 🚀 Usage

Run the script with the required arguments:

```bash
sudo python3 sgk30_json_to_keyboard.py --json "Liçtmuster.json" --frame 0 --slow
```

### Required Arguments

| Argument | Description |
|----------|------------|
| `--json` | Path to the JSON lighting pattern file |
| `--frame` | Frame index to display |
| `--slow` | Enables slower animation speed |

> ⚠️ Root privileges are required to communicate with the keyboard.

---

## 🎨 Custom Lighting Patterns

Instead of `"Liçtmuster.json"`, you can use any compatible JSON pattern file.

Example:

```bash
sudo python3 sgk30_json_to_keyboard.py --json "rainbow.json" --frame 2 --slow
```

You can create your own lighting effects by modifying or creating new JSON files.

---

## ⚠️ Disclaimer

This is an **unofficial Linux tool** and is not affiliated with Sharkoon.  
Use at your own risk.
