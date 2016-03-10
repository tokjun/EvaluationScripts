EvaluationScripts
=================
Python/R/Shell scripts for evaluation 


CryoMonitoring: Experiment Tools for CryoMonitoring Research 
============================================================

Before use, load the script:

  >>> execfile('/path/GenerateR2StarMaps.py')

Second echo scaling factor
--------------------------

First, load the list of images:

  >>> list = LoadImageList('/data path/Cryo-2016-02-12/ImageList.csv')

then, calculate the scaling factor (to calibrate the second echo to the first). Once you create a label map that specifies the region for calibration, calculate the scaling factor by calling the following function:

  >>> CalcScalingFactorBatch('/data path/Cryo-2016-02-12/PETRA-NRRD', list[0], 'echo1-', 'echo2-', 'calib-roi-label')


