import json

def save_added_users(added_users):
    with open('added_users.json', 'w') as file:
        json.dump(added_users, file)

def load_added_users():
    try:
        with open('added_users.json', 'r') as file:
            content = file.read()
            if not content:
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}
