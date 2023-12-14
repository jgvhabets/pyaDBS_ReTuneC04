# add TMSi repo
from os import getcwd, listdir
from os.path import join, dirname, exists
import sys
from numpy import logical_or

def add_tmsi_repo():
        
    tmsi_repo_name = 'tmsi-python-interface-main'
    main_repo_name = 'pyaDBS_ReTuneC04'
    dir = getcwd()
    
    for i in range(20):

        if not logical_or('packages' in listdir(dir),
                          dir.endswith(main_repo_name)):
                          
            dir = dirname(dir)
    # packages folder is found
    else:
        tmsi_path = join(dir, 'packages', tmsi_repo_name)
        assert exists(tmsi_path), f'non-existing tmsi-path: {tmsi_path}'
        sys.path.append(tmsi_path)

    return f'added PATH: {join(dir, tmsi_repo_name)}'