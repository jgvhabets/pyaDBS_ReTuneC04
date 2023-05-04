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
  - `pip install py-serial`

- timeflux plugins installed
  - timeflux_example
  - timeflux_ui
  - timeflux_dsp

  
- Download or clone <a href="https://gitlab.com/tmsi/tmsi-python-interface">TMSi Python Interface from GitLab</a>.   


### Important Notes

- don't use camelBack typing for Classnames, rather capitals at first letter
- stick with normal python classes to avoid problematic inheritance from normal classes into dataclasses
- always include time index in output (update()) to print in monitor
 
### Contributors:
- <a href="https://github.com/jgvhabets">Jeroen Habets</a> 
- <a href="https://github.com/jlbusch">Johannes Busch</a> 
