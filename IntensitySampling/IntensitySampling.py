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
import LabelStatistics

### Parameters
workingDir = '/Users/junichi/Projects/Gyn/greg-2017-07-21-experiment/2017-11-17/Test'
outputFileName = 'Intensities.csv'
labelImageFile = 'sampling-label.nrrd'

imageFileList = [
  '101 T1_p2_fa1_9_18_FLIP1.nrrd',
  '102 T1_p2_fa1_9_18_FLIP2.nrrd',
  '104 T1_p2_fa1_9_18_FLIP1.nrrd',
  '105 T1_p2_fa1_9_18_FLIP2.nrrd',
  '107 T1_p2_fa1_9_18_FLIP1.nrrd',
  '108 T1_p2_fa1_9_18_FLIP2.nrrd',
  '82 T1_p2_fa1_3_12_FLIP1.nrrd',
  '83 T1_p2_fa1_3_12_FLIP2.nrrd',
  '85 T1_p2_fa1_3_12_FLIP1.nrrd',
  '86 T1_p2_fa1_3_12_FLIP2.nrrd',
  '88 T1_p2_fa1_3_12_FLIP1.nrrd',
  '89 T1_p2_fa1_3_12_FLIP2.nrrd',
  '91 T1_p2_fa1_6_15_FLIP1.nrrd',
  '92 T1_p2_fa1_6_15_FLIP2.nrrd',
  '94 T1_p2_fa1_6_15_FLIP1.nrrd',
  '95 T1_p2_fa1_6_15_FLIP2.nrrd',
  '97 T1_p2_fa1_6_15_FLIP1.nrrd',
  '98 T1_p2_fa1_6_15_FLIP2.nrrd',
]
    
### Setup modules

### Open output file
outputFile = open(workingDir+'/'+outputFileName, 'w')
outputFile.write("Image,Index,Count,Volume mm^3,Volume cc,Min,Max,Mean,StdDev\n")

### Load label data
(r, labelNode) = slicer.util.loadVolume(workingDir+'/'+labelImageFile, {}, True)

for imageFile in imageFileList:

    print workingDir+'/'+imageFile
    if os.path.isfile(workingDir+'/'+imageFile):
        (r, imageNode) = slicer.util.loadVolume(workingDir+'/'+imageFile, {}, True)

        lslogic = LabelStatistics.LabelStatisticsLogic(imageNode, labelNode)
        print 'analyzing %s' % imageFile

        for i in lslogic.labelStats["Labels"]:
            outputFile.write("%s," % imageFile)
            outputFile.write("%f," % lslogic.labelStats[i,"Index"])
            outputFile.write("%f," % lslogic.labelStats[i,"Count"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume mm^3"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume cc"])
            outputFile.write("%f," % lslogic.labelStats[i,"Min"])
            outputFile.write("%f," % lslogic.labelStats[i,"Max"])
            outputFile.write("%f," % lslogic.labelStats[i,"Mean"])
            outputFile.write("%f\n" % lslogic.labelStats[i,"StdDev"])

        slicer.mrmlScene.RemoveNode(imageNode)

slicer.mrmlScene.RemoveNode(labelNode)

outputFile.close()
