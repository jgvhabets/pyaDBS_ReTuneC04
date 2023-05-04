# add TMSi repo
from os import getcwd, listdir
from os.path import join, dirname
import sys

def add_tmsi_repo():
        
    tmsi_repo_name = 'tmsi-python-interface-main'
    dir = getcwd()
    print(dir)
    while tmsi_repo_name not in listdir(dir):
        dir = dirname(dir)
        # built in security to prevent eternal loop
        if len(dir) < 5:
            raise FileNotFoundError(
                f'{tmsi_repo_name} not found in add_tmsi_repo()'
            )

    sys.path.append(join(dir, tmsi_repo_name))

    return f'added PATH: {join(dir, tmsi_repo_name)}'