"""SHIVANK AI desktop companion. Executes only allow-listed browser/media actions."""
import argparse, json, os, platform, time, urllib.request
from urllib.parse import urlparse

ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "music.youtube.com", "open.spotify.com", "github.com", "www.google.com", "mail.google.com"}

def send_json(url, token, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"X-Device-Token": token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode())

def media_key(action):
    system = platform.system().lower()
    if system == "windows":
        import ctypes
        keys = {"play_pause": 0xB3, "next": 0xB0, "previous": 0xB1, "volume_up": 0xAF, "volume_down": 0xAE, "mute": 0xAD}
        key = keys.get(action)
        if not key: raise ValueError("Unsupported media action")
        ctypes.windll.user32.keybd_event(key, 0, 0, 0)
        ctypes.windll.user32.keybd_event(key, 0, 2, 0)
    elif system == "darwin":
        scripts = {"play_pause": 'tell application "Music" to playpause', "next": 'tell application "Music" to next track', "previous": 'tell application "Music" to previous track'}
        if action in scripts:
            import subprocess; subprocess.run(["osascript", "-e", scripts[action]], check=True)
        else:
            raise ValueError("Volume hotkeys on macOS need an additional local permission/setup")
    else:
        commands = {"play_pause": ["playerctl", "play-pause"], "next": ["playerctl", "next"], "previous": ["playerctl", "previous"], "volume_up": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"], "volume_down": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"], "mute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"]}
        import subprocess
        cmd = commands.get(action)
        if not cmd: raise ValueError("Unsupported media action")
        subprocess.run(cmd, check=True)

def execute(payload):
    kind = payload.get("kind")
    if kind == "media":
        media_key(payload.get("action", ""))
        return "Executed media action: " + payload.get("action", "")
    if kind == "open_url":
        url = payload.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError("URL blocked by desktop companion allow-list")
        import webbrowser; webbrowser.open(url)
        return "Opened approved website: " + parsed.hostname
    raise ValueError("Action type is not allow-listed")

def main():
    parser = argparse.ArgumentParser(description="SHIVANK AI desktop companion")
    parser.add_argument("--server", required=True, help="SHIVANK AI server base URL, e.g. https://your-host")
    parser.add_argument("--token", default=os.getenv("DEVICE_AGENT_TOKEN"), help="Pairing token; prefer DEVICE_AGENT_TOKEN env var")
    parser.add_argument("--poll", type=int, default=3)
    args = parser.parse_args()
    if not args.token:
        raise SystemExit("Set DEVICE_AGENT_TOKEN environment variable or pass --token")
    base = args.server.rstrip("/")
    print("SHIVANK AI desktop companion connected. Ctrl+C to stop.")
    while True:
        try:
            response = send_json(base + "/api/device/next", args.token)
            job = response.get("job")
            if job:
                try:
                    result = execute(job["payload"])
                except Exception as exc:
                    result = "Action failed: " + str(exc)[:300]
                send_json(base + f"/api/device/{job['id']}/result", args.token, {"result": result})
                print(result)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print("Connection/action error:", str(exc)[:180])
        time.sleep(max(2, args.poll))

if __name__ == "__main__":
    main()
