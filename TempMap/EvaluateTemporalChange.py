import os
import os.path
import unittest
import random
import math
import tempfile
import time
import numpy
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import SimpleITK as sitk
import sitkUtils

import LabelStatistics
import PRFThermometry


labelNode = None
baselineNode = None
referenceNode = None

workDir = '/Users/junichi/Experiments/TemperatureMap/TempMap-2016-07-14/Scene'
refIndex = 392
logFileName = 'tempmaplog.txt'

## Open Log File

logFile = open(workDir+'/'+logFileName, 'a')

labelPath = '%s/Reference-label.nrrd' % (workDir)
baselinePath =  '%s/%02d TempMap MultiSlice.1.3.12.2.1107.5.2.36.40481.nrrd' % (workDir, refIndex)

if os.path.isfile(labelPath):
    (r, labelNode) = slicer.util.loadVolume(labelPath, {}, True)

if os.path.isfile(baselinePath):
    (r, baselineNode) = slicer.util.loadVolume(baselinePath, {}, True)

logic = PRFThermometry.PRFThermometryLogic()

for index in range(394,591):
#for index in range(394,430):

    if index % 2 == 1: # Odd index is for magnitude image -- skip
        continue
    
    referencePath = '%s/%02d TempMap MultiSlice.1.3.12.2.1107.5.2.36.40481.nrrd' % (workDir, index)
    print 'processing %s ...' % referencePath

    if os.path.isfile(referencePath):
        (r, referenceNode) = slicer.util.loadVolume(referencePath, {}, True)

    tempmapNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
    slicer.mrmlScene.AddNode(tempmapNode)
    tempmapName = 'TempMap-%03d' % (index)
    tempmapNode.SetName(tempmapName)

    alpha = -0.01
    gamma = 42.576
    B0 = 3.0
    TE = 0.01
    BT = 0.0
    upperThreshold = 1000.0
    lowerThreshold = -1000.0
    logic.run(True, baselineNode, referenceNode, labelNode, tempmapNode,
              alpha, gamma, B0, TE, BT, upperThreshold, lowerThreshold)

    tempmapPath = '%s/TempMap-%03d.nrrd' % (workDir, index)

    newTempmapNode = slicer.util.getNode(tempmapName)
    slicer.util.saveNode(newTempmapNode, tempmapPath)
    slicer.mrmlScene.RemoveNode(newTempmapNode)
    slicer.mrmlScene.RemoveNode(referenceNode)

    if logic.phaseDrift != None:
        logFile.write('%d, %f\n' % (index, logic.phaseDrift))

slicer.mrmlScene.RemoveNode(baselineNode)
slicer.mrmlScene.RemoveNode(labelNode)
logFile.close()
