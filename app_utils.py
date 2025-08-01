import json, os

SOURCE_PATH = "sources.json"
PROFILE_PATH = "profiles.json"

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f, indent=2)
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_sources():
    return load_json(SOURCE_PATH, {"Books":[],"Experts":[],"Styles":[],"Custom":[]})

def save_sources(data):
    save_json(SOURCE_PATH, data)

def load_profiles():
    return load_json(PROFILE_PATH, [])

def save_profiles(data):
    save_json(PROFILE_PATH, data)
