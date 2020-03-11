import yaml
import os


def _find_credentials_dir():
    """Try to build the path to the '../credentials' directory."""
    file_dir = os.path.dirname(os.path.realpath(__file__))
    key_fp = "/".join(file_dir.split('/')[:-1])
    key_fp += "/credentials/keys.yml"

    return key_fp

def get_secret_key(key_name, key_fp=None):
    """Read a key from a YAML file."""

    # If the filepath for the key file is not given, navigate to
    # the ROOT_DIR/credentials/keys.yml. And cross your fingers...
    if not key_fp:
        key_fp = _find_credentials_dir()

    with open(key_fp, 'r') as f:
        credentials = yaml.load(f, Loader=yaml.FullLoader)

    return(credentials[key_name])
