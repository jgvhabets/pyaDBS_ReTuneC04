# pyaDBS_ReTuneC04
pythons-based aDBS framework for ReTune C04 projects

### Goal:
Transform Matlab-based C04-aDBS setup to Python to use py-functionality of
timeflux, py-newronika interface, and py-TMSi interface.

### Requirements:
- Advised env to create:
  `conda create --name aDBS python=3.9 jupyter pandas scipy numpy matplotlib h5py pytables bottleneck`
- Packages to install:
  - `pip install timeflux`
  - `pip install serial`

- timeflux plugins installed
  - timeflux_example
  - timeflux_ui
  - timeflux_dsp

- for TMSi functions:
  - `pip install pyserial`
  - `pip install PySide2`
  - `pip install pyqtgraph`
  - `pip install pyxdf`
  - `pip install EDFlib`
  - Download or clone <a href="https://gitlab.com/tmsi/tmsi-python-interface">TMSi Python Interface from GitLab</a>
    in `REPO\packages\`


- for AlphaOmega:
  - succesfully install matlabengine before installing neuroomega_matlab (!), see next heading
  - `conda install flit-core` (not 100% sure)
  - `neuroomega_matlab` folder in `REPO\packages` (including pyproject.toml and src)
  - ensure that correct env is activated! Execute without charite proxies (!)
  - `cd REPO\packages\neuroomega_matlab`, `pip install -e .`  (pip install the package editable)
  - required default scripts: AO_DefaultStopStimulation, and edited version of AO_DefaultStimulation

- for matlabengine
  - for MATLAB version R2021b: pip install matlabengine==9.11.21
  


### Important Notes

- don't use camelBack typing for Classnames, rather capitals at first letter
- stick with normal python classes to avoid problematic inheritance from normal classes into dataclasses
- always include time index in output (update()) to print in monitor
- in case of windows 10 pip install issues: https://stackoverflow.com/questions/52815784/python-pip-raising-newconnectionerror-while-installing-libraries 
 
### Contributors:
- <a href="https://github.com/jgvhabets">Jeroen Habets</a> 
- <a href="https://github.com/jlbusch">Johannes Busch</a> 
