#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import time
from pathlib import Path
from typing import List, Tuple, Optional

VID_DEFAULT = 0x320F
PID_DEFAULT = 0x5016

def load_frames(json_path: Path) -> List[List[Tuple[int, int, int]]]:
    j = json.loads(json_path.read_text(encoding="utf-8"))
    frames = j["Device"][0]["CustomLightMode"]["LightColorInfo"]
    out: List[List[Tuple[int, int, int]]] = []
    for frame in frames:
        row = []
        for c in frame:
            row.append((int(c.get("Red",0))&0xFF, int(c.get("Green",0))&0xFF, int(c.get("Blue",0))&0xFF))
        out.append(row)
    if not out:
        raise SystemExit("Keine Frames gefunden.")
    return out

def is_uniform(frame: List[Tuple[int,int,int]]) -> bool:
    return bool(frame) and all(px == frame[0] for px in frame)

def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def find_hidraw(vid: int, pid: int) -> Optional[str]:
    sys_hidraw = Path("/sys/class/hidraw")
    matches = []
    for entry in sorted(sys_hidraw.iterdir()):
        if not entry.name.startswith("hidraw"):
            continue
        txt = _read_text(entry / "device" / "uevent")
        hid_id = None
        for line in txt.splitlines():
            if line.startswith("HID_ID="):
                hid_id = line.split("=",1)[1].strip()
                break
        if not hid_id:
            continue
        try:
            _, v, p = hid_id.split(":")
            v = int(v,16); p = int(p,16)
        except Exception:
            continue
        if v != vid or p != pid:
            continue
        devpath = os.path.realpath(str(entry / "device"))
        matches.append((entry.name, devpath))
    if not matches:
        return None
    # prefer :1.1 (dein RGB-Interface)
    for name, devpath in matches:
        if ":1.1" in devpath:
            return f"/dev/{name}"
    return f"/dev/{matches[0][0]}"

def hidraw_write(dev_path: str, data: bytes, retries: int = 3, backoff_s: float = 0.05) -> None:
    """
    Robust: fängt BrokenPipe (EPIPE) ab und versucht es nochmal.
    """
    for attempt in range(retries):
        fd = None
        try:
            fd = os.open(dev_path, os.O_WRONLY)
            os.write(fd, data)
            return
        except BrokenPipeError:
            # Gerät/Kernel hat die Pipe geschlossen: kurz warten und retry
            time.sleep(backoff_s * (attempt + 1))
            continue
        finally:
            if fd is not None:
                try: os.close(fd)
                except Exception: pass
    raise BrokenPipeError("hidraw_write: Broken pipe nach Retries (zu viele Reports / falsches Protokoll).")

def make_init_reports():
    r1 = bytes([0x04,0x01,0x00,0x01] + [0x00]*60)
    r2 = bytes([0x04,0x02,0x00,0x02] + [0x00]*60)
    return [r1, r2]

def solid_color_report(r,g,b):
    rep = bytearray(64)
    rep[0]=0x04
    rep[1]=0x2B
    rep[2]=0x03
    rep[3]=0x06
    rep[4]=0x1B
    rep[9]=0x05
    rep[10]=0x04
    rep[11]=0x03
    rep[14]=r&0xFF
    rep[15]=g&0xFF
    rep[16]=b&0xFF
    return bytes(rep)

def per_key_reports_best_effort(frame):
    base = bytearray(64)
    base[0]=0x04
    base[1]=0x2E
    base[2]=0x01
    base[3]=0x06
    base[4]=0x1B
    base[9]=0x05
    base[10]=0x04
    base[11]=0x03
    reps=[]
    for idx,(r,g,b) in enumerate(frame):
        rep=bytearray(base)
        rep[13]=idx&0xFF
        rep[14]=r&0xFF
        rep[15]=g&0xFF
        rep[16]=b&0xFF
        reps.append(bytes(rep))
    return reps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--fps", type=float, default=6.0)
    ap.add_argument("--dev", default=None)
    ap.add_argument("--slow", action="store_true", help="Non-uniform sehr langsam senden (Test)")
    ap.add_argument("--sleep", type=float, default=0.01, help="Delay zwischen Per-Key Reports (bei --slow)")
    ap.add_argument("--no-init", action="store_true")
    args = ap.parse_args()

    frames = load_frames(Path(args.json))
    if args.frame < 0 or args.frame >= len(frames):
        raise SystemExit(f"--frame muss 0..{len(frames)-1} sein.")
    dev = args.dev or find_hidraw(VID_DEFAULT, PID_DEFAULT)
    if not dev:
        raise SystemExit("Kein passendes /dev/hidrawX gefunden.")
    print(f"Nutze Device: {dev}")
    print(f"Frames: {len(frames)}, LEDs/Frame: {len(frames[0])}")

    def send_frame(i):
        frame = frames[i]
        if not args.no_init:
            for rep in make_init_reports():
                hidraw_write(dev, rep)
                time.sleep(0.01)

        if is_uniform(frame):
            r,g,b = frame[0]
            hidraw_write(dev, solid_color_report(r,g,b))
            print(f"Frame {i}: uniform -> SolidColor ({r},{g},{b})")
            return

        # non-uniform:
        if not args.slow:
            # sicherer Default: nicht kaputtballern
            print(f"Frame {i}: non-uniform -> NICHT gesendet (verwende --slow zum Testen).")
            return

        reps = per_key_reports_best_effort(frame)
        print(f"Frame {i}: non-uniform -> sende {len(reps)} Reports langsam...")
        for rep in reps:
            hidraw_write(dev, rep)
            time.sleep(args.sleep)
        print("Done (best-effort).")

    if args.loop:
        delay = 1.0 / max(0.1, args.fps)
        k = 0
        while True:
            send_frame(k % len(frames))
            time.sleep(delay)
            k += 1
    else:
        send_frame(args.frame)

if __name__ == "__main__":
    main()

