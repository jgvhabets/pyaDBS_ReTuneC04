# add TMSi repo
from os import getcwd, listdir
from os.path import join, dirname, exists
import sys
from numpy import logical_or

def add_tmsi_repo():
        
    # tmsi_repo_name = 'tmsi-python-interface'
    main_repo_name = 'pyaDBS_ReTuneC04'
    dir = getcwd()
    
    # set repo directory as dir
    for i in range(20):

        if not logical_or('packages' in listdir(dir),
                          dir.endswith(main_repo_name)):
                          
            dir = dirname(dir)
    packages_dir = join(dir, 'packages')

    assert exists(packages_dir), ('packages folder not found, '
                                  'check working directory of execution')

    # packages folder is found
    try:
        tmsi_foldername = [f for f in listdir(packages_dir)
                           if f.startswith('tmsi-python')][0]
    except:
        raise FileNotFoundError('tmsi-python folder not found in "repo/packages/"')
    
    tmsi_path = join(packages_dir, tmsi_foldername)

    assert exists(tmsi_path), f'non-existing tmsi-path: {tmsi_path}'
    
    sys.path.append(tmsi_path)

    print(f'added TMSi-packages PATH: {tmsi_path}')