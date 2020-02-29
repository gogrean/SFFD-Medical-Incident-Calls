import yaml

def get_secret_key(key_name, key_fp="../credentials/keys.yml"):
    """Read a key from a YAML file."""

    with open(key_fp, 'r') as f:
        credentials = yaml.load(f, Loader=yaml.FullLoader)

    return(credentials[key_name])
