import json, os

def get_history_path(persistent):
    return "chat_history.json" if persistent else None

def load_history(agent_name, path):
    if not path or not os.path.exists(path): return []
    with open(path) as f:
        history = json.load(f)
    return history.get(agent_name, [])

def save_history(agent_name, history, path):
    if not path: return
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data[agent_name] = history
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
