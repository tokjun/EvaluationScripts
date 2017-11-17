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

### Parameters
workingDir = '/Users/junichi/Dropbox/Experiments/UTE/UTE-2015-10-16/'
imageDir = '%s/Scene/' % (workingDir)
outputFileName = 'R2Star.csv'
labelImageFile = 'sampling-label.nrrd'

TE1 = 0.00007  ## s
TE2 = 0.002    ## s
lowerThreshold = -100000.0
upperThreshold = 100000.0

imageIndeces = [25, 28, 33, 37, 41, 45, 49, 53, 57, 61, 65, 69, 74, 78, 82, 86, 90, 94]

### Setup modules
slicer.util.selectModule('ComputeT2Star')
T2StarLogic = ComputeT2StarLogic()

slicer.util.selectModule('LabelStatistics')
#LabelStatisticsLogic = slicer.modules.labelstatistics.logic()

### Open output file
outputFile = open(workingDir+'/'+outputFileName, 'w')
outputFile.write("Image,Type,Index,Count,Volume mm^3,Volume cc,Min,Max,Mean,StdDev\n")

### Load label data
(r, labelNode) = slicer.util.loadVolume(imageDir+'/'+labelImageFile, {}, True)

for idx in imageIndeces:

    firstEchoFile = '%d Kidney2-echoPETRA.nrrd' % idx
    secondEchoFile = '%d Kidney2-echoPETRA.nrrd' % (idx+1)
    print 'reading %s' % firstEchoFile

    if os.path.isfile(imageDir+'/'+firstEchoFile) and os.path.isfile(imageDir+'/'+secondEchoFile):
        (r, firstEchoNode) = slicer.util.loadVolume(imageDir+'/'+firstEchoFile, {}, True)
        (r, secondEchoNode) = slicer.util.loadVolume(imageDir+'/'+secondEchoFile, {}, True)

        t2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(t2StarVolumeNode)
        t2StarVolumeNode.SetName('t2s-%s' % idx)

        r2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(r2StarVolumeNode)
        r2StarVolumeNode.SetName('r2s-%s' % idx)

        T2StarLogic.run(firstEchoNode, secondEchoNode, t2StarVolumeNode, r2StarVolumeNode,
                        TE1, TE2, upperThreshold, lowerThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        t2StarVolumeNode = slicer.util.getNode('t2s-%s' % idx)
        r2StarVolumeNode = slicer.util.getNode('r2s-%s' % idx)
        
        slicer.util.saveNode(t2StarVolumeNode, imageDir+'/'+t2StarVolumeNode.GetName()+'.nrrd')
        slicer.util.saveNode(r2StarVolumeNode, imageDir+'/'+r2StarVolumeNode.GetName()+'.nrrd')
        
        lslogic = LabelStatisticsLogic(r2StarVolumeNode, labelNode)

        for i in lslogic.labelStats["Labels"]:
            outputFile.write("%f," % idx)
            outputFile.write("R2s,")
            outputFile.write("%f," % lslogic.labelStats[i,"Index"])
            outputFile.write("%f," % lslogic.labelStats[i,"Count"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume mm^3"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume cc"])
            outputFile.write("%f," % lslogic.labelStats[i,"Min"])
            outputFile.write("%f," % lslogic.labelStats[i,"Max"])
            outputFile.write("%f," % lslogic.labelStats[i,"Mean"])
            outputFile.write("%f\n" % lslogic.labelStats[i,"StdDev"])

        lslogic = LabelStatisticsLogic(firstEchoNode, labelNode)
        for i in lslogic.labelStats["Labels"]:
            outputFile.write("%f," % idx)
            outputFile.write("Echo1,")
            outputFile.write("%f," % lslogic.labelStats[i,"Index"])
            outputFile.write("%f," % lslogic.labelStats[i,"Count"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume mm^3"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume cc"])
            outputFile.write("%f," % lslogic.labelStats[i,"Min"])
            outputFile.write("%f," % lslogic.labelStats[i,"Max"])
            outputFile.write("%f," % lslogic.labelStats[i,"Mean"])
            outputFile.write("%f\n" % lslogic.labelStats[i,"StdDev"])

        lslogic = LabelStatisticsLogic(secondEchoNode, labelNode)
        for i in lslogic.labelStats["Labels"]:
            outputFile.write("%f," % idx)
            outputFile.write("Echo2,")
            outputFile.write("%f," % lslogic.labelStats[i,"Index"])
            outputFile.write("%f," % lslogic.labelStats[i,"Count"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume mm^3"])
            outputFile.write("%f," % lslogic.labelStats[i,"Volume cc"])
            outputFile.write("%f," % lslogic.labelStats[i,"Min"])
            outputFile.write("%f," % lslogic.labelStats[i,"Max"])
            outputFile.write("%f," % lslogic.labelStats[i,"Mean"])
            outputFile.write("%f\n" % lslogic.labelStats[i,"StdDev"])

        slicer.mrmlScene.RemoveNode(t2StarVolumeNode)
        slicer.mrmlScene.RemoveNode(r2StarVolumeNode)
        slicer.mrmlScene.RemoveNode(firstEchoNode)
        slicer.mrmlScene.RemoveNode(secondEchoNode)

outputFile.close()
