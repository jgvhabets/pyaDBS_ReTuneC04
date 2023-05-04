"""PyInitFile"""

# add TMSi repo
from os import getcwd, listdir
from os.path import join, dirname
import sys

tmsi_repo_name = 'tmsi-python-interface-main'
dir = getcwd()
print(dir)
while tmsi_repo_name not in listdir(dir):
    dir = dirname(dir)

sys.path_append(join(dir, tmsi_repo_name))
print(f'added PATH: {join(dir, tmsi_repo_name)}')