# Sharkoon SKILLER SGK30 – Linux Control (Ubuntu 24)

This collection of Python scripts enables control of the RGB lighting of the **Sharkoon SKILLER SGK30** on Ubuntu 24 – without Windows software and without PCAP replay.

Supported features:

* Activating onboard profiles (animation continues running independently)
* Setting static (per-key) lighting patterns from JSON
* Setting a solid color
* Debug display of the target state in the terminal

---

# ⚙️ Requirements

* Ubuntu 24
* Python 3
* Root privileges for access to `/dev/hidraw*`

The scripts usually need to be executed with `sudo`.

---

# 📁 Project Structure

## Main Script

### `sgk30_profile_activate.py`

Central control program for:

* Activating saved profiles
* Setting static custom patterns or animated ones
* Setting a solid color

---

# 🚀 Usage

## 1️⃣ Activate Onboard Profile (recommended for animations)

The animation continues running without software after activation.

```bash
sudo python3 sgk30_profile_activate.py --json "Profile 2.json" --activate
```

Or:

```bash
sudo python3 sgk30_profile_activate.py --json "Profile 4.json" --activate
```

---

## 2️⃣ Set Static Custom Lighting Pattern

Uses frame 0 from `CustomLightMode`:

```bash
sudo python3 sgk30_profile_activate.py --json "Liçtmuster.json" --custom-static
```

If it becomes unstable or a `BrokenPipeError` appears:

```bash
sudo python3 sgk30_profile_activate.py --json "Liçtmuster.json" --custom-static --custom-sleep 0.02
```

`--custom-sleep` slows down the sending of per-key reports.

---

## 3️⃣ Set Solid Color

```bash
sudo python3 sgk30_profile_activate.py --json "Profile 2.json" --solid 255,0,0
```

Format: `R,G,B`

Examples:

* `255,0,0` → Red
* `0,255,0` → Green
* `0,0,255` → Blue

---

# 🛠 Troubleshooting

## BrokenPipeError

Occurs when reports are sent too quickly.

Solution:

```bash
--custom-sleep 0.02
```

Increase the value if necessary (0.03, 0.04 ...).

---

## Nothing happens

Possibly the wrong `hidraw` interface.

Optionally specify it explicitly:

```bash
sudo python3 sgk30_profile_activate.py --dev /dev/hidraw2 --json "Profile 2.json" --activate
```

---

# 🧠 Technical Note

Control is performed via HID reports directly to the keyboard’s RGB interface.

Animations are stored or activated onboard, so no background software is required.

---

# ⚠️ Disclaimer

Use at your own risk. Direct HID communication may cause instability if used incorrectly.

---

Have fun reverse engineering and tinkering 🚀
