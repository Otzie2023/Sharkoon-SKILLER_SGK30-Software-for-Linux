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
| `--frame` | Index of the frame to send (0-based) |
| `--slow` | Enable slow per-key sending for non-uniform frames (test mode) |
| `--loop` | Continuously loop through all frames |
| `--fps` | Playback speed in frames per second (used with `--loop`) |
| `--dev` | Manually specify the `/dev/hidrawX` device path |
| `--sleep` | Delay in seconds between per-key HID reports (used with `--slow`) |
| `--no-init` | Skip sending device initialization reports |

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
