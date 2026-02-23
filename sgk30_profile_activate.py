#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, json, os, time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

VID = 0x320F
PID = 0x5016

def _read_text(p: Path) -> str:
    try: return p.read_text(encoding="utf-8", errors="ignore")
    except Exception: return ""

def find_hidraw_prefer_1_1() -> Optional[str]:
    sys_hidraw = Path("/sys/class/hidraw")
    matches = []
    for entry in sorted(sys_hidraw.iterdir()):
        if not entry.name.startswith("hidraw"):
            continue
        txt = _read_text(entry / "device" / "uevent")
        hid_id = None
        for line in txt.splitlines():
            if line.startswith("HID_ID="):
                hid_id = line.split("=", 1)[1].strip()
                break
        if not hid_id:
            continue
        try:
            _, v, p = hid_id.split(":")
            v = int(v, 16); p = int(p, 16)
        except Exception:
            continue
        if v != VID or p != PID:
            continue
        devpath = os.path.realpath(str(entry / "device"))
        matches.append((entry.name, devpath))
    if not matches:
        return None
    for name, devpath in matches:
        if ":1.1" in devpath:
            return f"/dev/{name}"
    return f"/dev/{matches[0][0]}"

def hidraw_write(dev: str, data: bytes, retries: int = 3) -> None:
    for i in range(retries):
        fd = None
        try:
            fd = os.open(dev, os.O_WRONLY)
            os.write(fd, data)
            return
        except BrokenPipeError:
            time.sleep(0.05 * (i + 1))
        finally:
            if fd is not None:
                try: os.close(fd)
                except Exception: pass
    raise BrokenPipeError("Broken pipe (Timing zu aggressiv / Device lehnt Sequenz ab).")

def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def get_lightinfo(profile: Dict[str, Any]) -> Tuple[int,int,int,int,int]:
    li = profile["Device"][0].get("LightInfo", {})
    r = int(li.get("Red", 0)) & 0xFF
    g = int(li.get("Green", 0)) & 0xFF
    b = int(li.get("Blue", 0)) & 0xFF
    light = int(li.get("Light", 0)) & 0xFF
    speed = int(li.get("Speed", 0)) & 0xFF
    return r,g,b,light,speed

def get_custom_frames(profile: Dict[str, Any]) -> List[List[Tuple[int,int,int]]]:
    frames = profile["Device"][0]["CustomLightMode"]["LightColorInfo"]
    out: List[List[Tuple[int,int,int]]] = []
    for frame in frames:
        out.append([(int(c.get("Red",0))&0xFF, int(c.get("Green",0))&0xFF, int(c.get("Blue",0))&0xFF) for c in frame])
    return out

# --- Helpers: PCAP-basierte Sequenzen (funktionieren bei dir) ---
def rpt(hexstr: str) -> bytes:
    return bytes.fromhex(hexstr)

INIT1 = rpt("04010001" + "00"*60)
INIT2 = rpt("04020002" + "00"*60)
APPLY = rpt("0425000322" + "00"*59)

SEQ_07 = [
    rpt("043f000738" + "00"*59),
    rpt("047700073838" + "00"*58),
    rpt("04af00073870" + "00"*58),
    rpt("04e7000738a8" + "00"*58),
    rpt("041f010738e0" + "00"*58),
    rpt("04580007381801" + "00"*57),
    rpt("048200072a5001" + "00"*57),
]
SEQ_1B = [
    rpt("0453001b38" + "00"*59),
    rpt("048b001b3838" + "00"*58),
    rpt("0499001b0e70" + "00"*58),
]
SEQ_09 = [
    rpt("04ed040938" + "00"*59),
    rpt("046705093838" + "00"*58),
    rpt("04c705093870" + "00"*58),
    rpt("0446060938a8" + "00"*58),
    rpt("0416070938e0" + "00"*58),
    rpt("04730809381801" + "00"*57),
    rpt("04570a092a5001" + "00"*57),
]

def build_lightinfo_report(r: int, g: int, b: int, light: int) -> bytes:
    rep = bytearray(rpt("04b501061b00000000000401000100fe8f" + "00"*46))
    rep[10] = light & 0xFF
    rep[14] = r & 0xFF
    rep[15] = g & 0xFF
    rep[16] = b & 0xFF
    return bytes(rep)

def activate_profile_like_windows(dev: str, r: int, g: int, b: int, light: int):
    def send(x: bytes, d=0.01):
        hidraw_write(dev, x)
        time.sleep(d)

    send(INIT1)
    send(APPLY)
    for p in SEQ_07: send(p, 0.002)
    for p in SEQ_1B: send(p, 0.002)
    send(INIT2)

    send(INIT1)
    send(build_lightinfo_report(r,g,b,light))
    send(INIT2)

    send(APPLY)
    send(APPLY)

    send(INIT1)
    for p in SEQ_09: send(p, 0.003)
    send(INIT2)

def solid_color_report(r: int, g: int, b: int) -> bytes:
    rep = bytearray(64)
    rep[0]=0x04
    rep[1]=0x2B; rep[2]=0x03
    rep[3]=0x06; rep[4]=0x1B
    rep[9]=0x05; rep[10]=0x04; rep[11]=0x03
    rep[14]=r&0xFF; rep[15]=g&0xFF; rep[16]=b&0xFF
    return bytes(rep)

def send_custom_frame_best_effort(dev: str, frame: List[Tuple[int,int,int]], sleep_s: float):
    """
    Stehendes Muster: wir senden Frame 0 genau einmal per-key (langsam).
    """
    base = bytearray(64)
    base[0]=0x04
    base[1]=0x2E; base[2]=0x01
    base[3]=0x06; base[4]=0x1B
    base[9]=0x05; base[10]=0x04; base[11]=0x03

    for idx,(r,g,b) in enumerate(frame):
        rep = bytearray(base)
        rep[13]=idx & 0xFF
        rep[14]=r&0xFF; rep[15]=g&0xFF; rep[16]=b&0xFF
        hidraw_write(dev, bytes(rep))
        time.sleep(sleep_s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="Profil JSON (z.B. Profil 2.json / Liçtmuster.json)")
    ap.add_argument("--dev", default=None, help="Optional: /dev/hidraw2 erzwingen")
    ap.add_argument("--activate", action="store_true", help="Profil wie Windows aktivieren (Animation onboard auswählen)")
    ap.add_argument("--custom-static", action="store_true", help="Stehendes CustomLightMode Frame0 einmal auf Tastatur setzen")
    ap.add_argument("--custom-sleep", type=float, default=0.02, help="Delay zwischen Keys beim custom-static")
    ap.add_argument("--solid", default=None, help="Setze Vollfarbe R,G,B (z.B. 255,100,0)")
    args = ap.parse_args()

    dev = args.dev or find_hidraw_prefer_1_1()
    if not dev:
        raise SystemExit("Kein SGK30 HIDRAW gefunden (VID/PID).")
    print("Nutze Device:", dev)

    prof = load_json(Path(args.json))

    if args.solid:
        r,g,b = (int(x.strip()) for x in args.solid.split(","))
        hidraw_write(dev, INIT1); time.sleep(0.01)
        hidraw_write(dev, solid_color_report(r,g,b))
        hidraw_write(dev, INIT2)
        print(f"Solid gesetzt: ({r},{g},{b})")
        return

    if args.activate:
        r,g,b,light,speed = get_lightinfo(prof)
        print(f"LightInfo: Light={light} Speed={speed} RGB=({r},{g},{b})")
        activate_profile_like_windows(dev, r,g,b,light)
        print("Aktiviert (onboard Effekt wird ausgewählt).")
        return

    if args.custom_static:
        frames = get_custom_frames(prof)
        if not frames:
            raise SystemExit("Keine CustomLightMode.LightColorInfo Frames gefunden.")
        frame0 = frames[0]
        print(f"Custom-static: sende Frame0 ({len(frame0)} LEDs) einmal...")
        hidraw_write(dev, INIT1); time.sleep(0.01)
        send_custom_frame_best_effort(dev, frame0, args.custom_sleep)
        # kleiner Abschluss/Apply – schadet nicht
        hidraw_write(dev, APPLY); time.sleep(0.01)
        hidraw_write(dev, INIT2)
        print("Done. (Stehendes Muster gesetzt)")
        return

    raise SystemExit("Nutze: --activate oder --custom-static oder --solid R,G,B")

if __name__ == "__main__":
    main()
