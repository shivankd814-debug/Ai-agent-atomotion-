from app.device import interpret_command

def test_music_search():
    out = interpret_command("play Arijit Singh songs", "this_device")
    assert out["kind"] == "open_url"
    assert "music.youtube.com/search" in out["url"]

def test_media_key_routes_to_pc():
    out = interpret_command("pause music", "pc")
    assert out["kind"] == "media"
    assert out["action"] == "play_pause"

def test_volume_command():
    out = interpret_command("volume up", "pc")
    assert out["action"] == "volume_up"

def test_unknown_command_is_not_device_action():
    assert interpret_command("send my friend a WhatsApp", "pc") is None
