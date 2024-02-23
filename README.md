# pyaDBS_ReTuneC04
pythons-based aDBS framework for ReTune C04 projects

### Goal:
Transform Matlab-based C04-aDBS setup to Python to use py-functionality of
timeflux, py-newronika interface, and py-TMSi interface.

### Requirements:
- Advised env to create:
  `conda create --name aDBS python=3.9 jupyter pandas scipy numpy matplotlib h5py pytables bottleneck`
- Packages to install:
  - `pip install pylsl==1.16.2`
  - `pip install timeflux`
  - `pip install serial`
  - `pip install ipympl`

- timeflux plugins installed
  - timeflux_example
  - timeflux_ui
  - timeflux_dsp

- for TMSi functions:
  - Download or clone <a href="https://gitlab.com/tmsi/tmsi-python-interface">TMSi Python Interface from GitLab</a>
    in `REPO\packages\`
  - Navigate to `REPO\packages\` and call 'pip install -r .\requirements39_Windows.txt'
  - `pip install EDFlib`
  - TMSi Saga interface lets the sampling function sleep for ~60ms per data chunk retrieval. This slows down real-time processing. To overcome, change the following lines in `REPO\packages\tmsi-python-interface\TMSiSDK\devices\saga\saga_device.py`:
    1024: time.sleep(0.050) -> time.sleep(0.001)
    1130: time.sleep(0.010) -> time.sleep(0.001)

- for AlphaOmega:
  - succesfully install matlabengine before installing neuroomega_matlab (!), see next heading
  - `conda install flit-core` (not 100% sure)
  - `neuroomega_matlab` folder in `REPO\packages` (including pyproject.toml and src)
  - ensure that correct env is activated! Execute without charite proxies (!)
  - `cd REPO\packages\neuroomega_matlab`, `pip install -e .`  (pip install the package editable)
  - required default scripts: AO_DefaultStopStimulation, and edited version of AO_DefaultStimulation

- for matlabengine
  - for MATLAB version R2021b: pip install matlabengine==9.11.21
  
- for session setup:
  - `pip install mne-bids`


### Important Notes

- don't use camelBack typing for Classnames, rather capitals at first letter
- stick with normal python classes to avoid problematic inheritance from normal classes into dataclasses
- always include time index in output (update()) to print in monitor
- in case of windows 10 pip install issues: https://stackoverflow.com/questions/52815784/python-pip-raising-newconnectionerror-while-installing-libraries 
 
### Contributors:
- <a href="https://github.com/jgvhabets">Jeroen Habets</a> 
- <a href="https://github.com/jlbusch">Johannes Busch</a> 
