import ujson as json

CONFIG_PATH = 'minisoul_config.json'

_DEFAULTS = {
    'name': 'MiniSoul',
    'clock_face': 'digital_bold',
    'updated_at': None,
    'available_clock_faces': [
        'digital_bold',
        'minimal_split',
        'analog',
        'orbit',
    ],
}


def config_exists():
    try:
        with open(CONFIG_PATH, 'r'):
            return True
    except OSError:
        return False


def get_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            data = json.loads(f.read())
        # Fill in any missing keys with defaults
        for k, v in _DEFAULTS.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return dict(_DEFAULTS)


def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        f.write(json.dumps(config))


def get_name():
    return get_config().get('name', _DEFAULTS['name'])


def get_clock_face():
    return get_config().get('clock_face', _DEFAULTS['clock_face'])


def get_available_clock_faces():
    return get_config().get('available_clock_faces', _DEFAULTS['available_clock_faces'])


def get_updated_at():
    return get_config().get('updated_at', _DEFAULTS['updated_at'])
