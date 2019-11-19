import json

def get_credential(file_path):
    """
        Read credential json file and return
        username and password
    """
    with open(file_path) as json_file:
        config = json.load(json_file)
    assert "username" in config.keys()
    assert "password" in config.keys()

    return config["username"], config["password"]

def get_driver():
    """
        This function prepare geckodriver
        TODO: Reduce duplicate code
    """
    pass