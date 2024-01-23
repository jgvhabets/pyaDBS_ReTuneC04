import json


def get_config_settings(
    json_filename: str = 'config.json',
):
    # load configuration 
    with open(json_filename, 'r') as file:
        cfg = json.load(file)

    return cfg

