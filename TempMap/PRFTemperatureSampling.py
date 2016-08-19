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
import csv

import PRFThermometry


lowerThreshold = -1000000.0
upperThreshold =  1000000.0

### Setup modules
alpha=-0.01
gamma=42.576
B0=3.0
TE=0.01
BT=21

PRFThermometryLogic = PRFThermometry.PRFThermometryLogic()

def SampleIntensities(imageDir, imageName, ROIName):
    imageFile = imageName+'.nrrd'
    ROIFile = ROIName+'.nrrd'

    if os.path.isfile(imageDir+'/'+imageFile) and os.path.isfile(imageDir+'/'+ROIFile):
        (r, imageNode) = slicer.util.loadVolume(imageDir+'/'+imageFile, {}, True)
        (r, ROINode) = slicer.util.loadVolume(imageDir+'/'+ROIFile, {}, True)
        
        image = sitk.Cast(sitkUtils.PullFromSlicer(imageNode.GetID()), sitk.sitkFloat32)
        ROI   = sitk.Cast(sitkUtils.PullFromSlicer(ROINode.GetID()), sitk.sitkUInt8)

        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(image, ROI)

        n = stats.GetNumberOfLabels()
        intensityMean = []
        intensitySD = []
        for i in range(0, n):
            intensityMean.append(stats.GetMean(i))
            intensitySD.append(stats.GetSigma(i))

        slicer.mrmlScene.RemoveNode(imageNode)
        slicer.mrmlScene.RemoveNode(ROINode)
            
        return (intensityMean, intensitySD)

    else:
        print "ERROR: Files did not exist."
        return ([], [])

        
def CalcTemp(imageDir, baselineName, referenceName, tempName):

    baselineFile = baselineName+'.nrrd'
    referenceFile = referenceName+'.nrrd'
    print 'reading %s' % baselineFile

    if os.path.isfile(imageDir+'/'+baselineFile) and os.path.isfile(imageDir+'/'+referenceFile):
        (r, baselineNode) = slicer.util.loadVolume(imageDir+'/'+baselineFile, {}, True)
        (r, referenceNode) = slicer.util.loadVolume(imageDir+'/'+referenceFile, {}, True)

        tempVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(tempVolumeNode)
        tempVolumeNode.SetName(tempName)

        PRFThermometryLogic.run(True,
                                baselineNode, referenceNode, tempVolumeNode,
                                alpha, gamma, B0, TE, BT, upperThreshold, lowerThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        tempVolumeNode = slicer.util.getNode(tempName)
        
        slicer.util.saveNode(tempVolumeNode, imageDir+'/'+tempVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(tempVolumeNode)
        slicer.mrmlScene.RemoveNode(baselineNode)
        slicer.mrmlScene.RemoveNode(referenceNode)

        
def LoadImageList(imageListCSV):

    imageList = [[],[]]
    with open(imageListCSV,'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            #imageList.append([int(csvreader[0]), float(csvreader[1])])
            if row != [] and row[0] != 'Se':
                imageList[0].append(int(row[0]))
                imageList[1].append(float(row[1]))
    return imageList


def GenerateTempImages(imageDir, imageIndices, baselineIndex, prefix='T-MAP-'):

    baselineName = '%s%03d' % (prefix, baselineIndex)

    for idx in imageIndices:

        print 'processing %s/%s%03d.nrrd ...' % (imageDir, prefix, idx)

        referenceName = '%s%03d' % (prefix, idx)
        if not os.path.isfile(imageDir+'/'+referenceName+'.nrrd'):
            print 'Error: Could not open file: %s' % referenceName
        else:

            tempImageName = 'Temp-%03d' % idx
            CalcTemp(imageDir, baselineName, referenceName, tempImageName)
            
    return True


def SampleTempPerROI(imageDir, imageList, outputFile, ROIName='roi-label', prefixTemp='Temp-'):

    imageIndices = imageList[0]
    imageTime = imageList[1]
    result = []
    i = 0
    
    for idx in imageIndices:
        print 'processing %s/%s%03d.nrrd ...' % (imageDir, prefixTemp, idx)

        fileTemp = '%s%03d' % (prefixTemp, idx)
        stat = SampleIntensities(imageDir, fileTemp, ROIName)
        row = stat[0]
        row[0] = imageTime[i]     # Replace intensity for index 0 with because it will not be used.
        result.append(stat[0])  # Record only mean
        i = i + 1
    
    with open(outputFile,'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        header = ['Time']
        for i in range(1,len(result[0])):
            header.append('%d' % i)
        csvwriter.writerows([header])
        csvwriter.writerows(result)
        
    return result



