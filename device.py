"""Safe, allow-listed device command queue for paired desktop companions."""
import re
from urllib.parse import quote_plus
from .store import enqueue_device_job

MUSIC = re.compile(r"(?:play|chala|bajao|lagao)\s+(?:the\s+)?(.+)", re.I)
URLS = {
    "youtube": "https://www.youtube.com/",
    "youtube music": "https://music.youtube.com/",
    "spotify": "https://open.spotify.com/",
    "google": "https://www.google.com/",
    "github": "https://github.com/",
    "gmail": "https://mail.google.com/",
}

def interpret_command(text: str, target: str = "this_device"):
    raw = text.strip()
    low = raw.lower()
    if any(x in low for x in ("pause music", "music pause", "gaana pause", "gaana rok", "stop music", "gaana band")):
        return {"kind": "media", "action": "play_pause", "target": target, "message": "Media play/pause command prepared."}
    if any(x in low for x in ("next song", "next track", "agla gaana", "next gaana")):
        return {"kind": "media", "action": "next", "target": target, "message": "Next-track command prepared."}
    if any(x in low for x in ("previous song", "previous track", "pichla gaana")):
        return {"kind": "media", "action": "previous", "target": target, "message": "Previous-track command prepared."}
    if "volume" in low or "awaaz" in low:
        if any(x in low for x in ("up", "increase", "badha", "zyada")):
            action = "volume_up"
        elif any(x in low for x in ("down", "decrease", "kam", "ghata")):
            action = "volume_down"
        elif "mute" in low:
            action = "mute"
        else:
            return None
        return {"kind": "media", "action": action, "target": target, "message": "Volume command prepared."}
    for name, url in URLS.items():
        if low in (f"open {name}", f"{name} kholo", f"{name} open karo"):
            return {"kind": "open_url", "url": url, "target": target, "message": f"Opening {name}."}
    match = MUSIC.search(raw)
    if match and not any(w in low for w in ("volume", "awaaz")):
        query = match.group(1).strip()
        if query.lower() in ("music", "gaana", "song"):
            url = "https://music.youtube.com/"
        else:
            url = "https://music.youtube.com/search?q=" + quote_plus(query)
        return {"kind": "open_url", "url": url, "target": target, "message": f"Searching music for: {query}"}
    return None

def dispatch_device_command(command: dict):
    target = command.get("target", "this_device")
    if target in ("pc", "both"):
        job = enqueue_device_job(command)
        return {"queued_for_pc": True, "job_id": job, "message": "Command queued for paired PC. Make sure the SHIVANK desktop companion is running.", "open_url": command.get("url") if target == "both" else None}
    return {"queued_for_pc": False, "message": command.get("message", "Command prepared."), "open_url": command.get("url")}
