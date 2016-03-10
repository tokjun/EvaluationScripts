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

import LabelStatistics
import ComputeT2Star
import ComputeTemp

lowerThreshold = -1000000.0
upperThreshold =  1000000.0

slicer.util.selectModule('LabelStatistics')

### Setup modules
#slicer.util.selectModule('ComputeT2Star')
T2StarLogic = ComputeT2Star.ComputeT2StarLogic()

#slicer.util.selectModule('ComputeTemp')
TempLogic = ComputeTemp.ComputeTempLogic()

def CalcNoise(imageDir, image1Name, image2Name, ROIName):
    
    image1File = image1Name+'.nrrd'
    image2File = image2Name+'.nrrd'
    ROIFile = ROIName+'.nrrd'
    
    if os.path.isfile(imageDir+'/'+image1File) and os.path.isfile(imageDir+'/'+image2File):
        (r, image1Node) = slicer.util.loadVolume(imageDir+'/'+image1File, {}, True)
        (r, image2Node) = slicer.util.loadVolume(imageDir+'/'+image2File, {}, True)
        (r, ROINode) = slicer.util.loadVolume(imageDir+'/'+ROIFile, {}, True)

        image1 = sitk.Cast(sitkUtils.PullFromSlicer(image1Node.GetID()), sitk.sitkFloat32)
        image2 = sitk.Cast(sitkUtils.PullFromSlicer(image2Node.GetID()), sitk.sitkFloat32)
        subImage = sitk.Subtract(image1, image2)
        absImage = sitk.Abs(subImage)
        
        absVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(absVolumeNode)
        absVolumeNode.SetName('abs')
        sitkUtils.PushToSlicer(absImage, absVolumeNode.GetName(), 0, True)

        absVolumeNode = slicer.util.getNode('abs')
        lslogic = LabelStatistics.LabelStatisticsLogic(absVolumeNode, ROINode)
        meanAbsDiff = lslogic.labelStats[1,"Mean"]

        slicer.mrmlScene.RemoveNode(image1Node)
        slicer.mrmlScene.RemoveNode(image2Node)
        slicer.mrmlScene.RemoveNode(ROINode)
        slicer.mrmlScene.RemoveNode(absVolumeNode)
        
        return (meanAbsDiff/math.sqrt(math.pi/2.0))
    else:
        print "ERROR: Could not calculate noise level"
        return -1.0


def CorrectNoise(inputName, outputName, noiseLevel):
    
    inputFile = inputName+'.nrrd'
    outputFile = outputName+'.nrrd'
    
    if os.path.isfile(imageDir+'/'+inputFile):
        (r, inputNode) = slicer.util.loadVolume(imageDir+'/'+inputFile, {}, True)
    
        inputImage = sitk.Cast(sitkUtils.PullFromSlicer(inputNode.GetID()), sitk.sitkFloat32)
        squareImage = sitk.Pow(inputImage, 2)
        subImage = sitk.Subtract(squareImage, noiseLevel*noiseLevel)
        correctedImage = sitk.Sqrt(subImage)

        correctedVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(correctedVolumeNode)
        correctedVolumeNode.SetName(outputName)
        sitkUtils.PushToSlicer(correctedImage, correctedVolumeNode.GetName(), 0, True)

        correctedVolumeNode = slicer.util.getNode(outputName)
        slicer.util.saveNode(correctedVolumeNode, imageDir+'/'+correctedVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(inputNode)
        slicer.mrmlScene.RemoveNode(correctedVolumeNode)

    else:
        
        print "ERROR: Could not correct noise."
        
        
def CalcR2Star(imageDir, firstEchoName, secondEchoName, t2StarName, r2StarName, TE1, TE2, scaleFactor):

    firstEchoFile = firstEchoName+'.nrrd'
    secondEchoFile = secondEchoName+'.nrrd'
    print 'reading %s' % firstEchoFile

    if os.path.isfile(imageDir+'/'+firstEchoFile) and os.path.isfile(imageDir+'/'+secondEchoFile):
        (r, firstEchoNode) = slicer.util.loadVolume(imageDir+'/'+firstEchoFile, {}, True)
        (r, secondEchoNode) = slicer.util.loadVolume(imageDir+'/'+secondEchoFile, {}, True)

        t2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(t2StarVolumeNode)
        t2StarVolumeNode.SetName(t2StarName)

        r2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(r2StarVolumeNode)
        r2StarVolumeNode.SetName(r2StarName)

        T2StarLogic.run(firstEchoNode, secondEchoNode, t2StarVolumeNode, r2StarVolumeNode, TE1, TE2, scaleFactor, upperThreshold, lowerThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        t2StarVolumeNode = slicer.util.getNode(t2StarName)
        r2StarVolumeNode = slicer.util.getNode(r2StarName)
        
        slicer.util.saveNode(t2StarVolumeNode, imageDir+'/'+t2StarVolumeNode.GetName()+'.nrrd')
        slicer.util.saveNode(r2StarVolumeNode, imageDir+'/'+r2StarVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(t2StarVolumeNode)
        slicer.mrmlScene.RemoveNode(r2StarVolumeNode)
        slicer.mrmlScene.RemoveNode(firstEchoNode)
        slicer.mrmlScene.RemoveNode(secondEchoNode)

        
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

        
def CalcTemp(imageDir, baselineName, referenceName, tempName, r2StarName, paramA, paramB):

    # Assume the unit for R2* data is s^-1
    # Temp = A * R2Star + B
    paramA = 0.15798
    paramB = -9.92

    baselineFile = baselineName+'.nrrd'
    referenceFile = referenceName+'.nrrd'
    print 'reading %s' % baselineFile

    if os.path.isfile(imageDir+'/'+baselineFile) and os.path.isfile(imageDir+'/'+referenceFile):
        (r, baselineNode) = slicer.util.loadVolume(imageDir+'/'+baselineFile, {}, True)
        (r, referenceNode) = slicer.util.loadVolume(imageDir+'/'+referenceFile, {}, True)

        tempVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(tempVolumeNode)
        tempVolumeNode.SetName(tempName)

        TempLogic.run(baselineR2Star, referenceR2Star, tempVolumeNode, paramA, paramB, upperThreshold, lowerThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        tempVolumeNode = slicer.util.getNode(tempName)
        
        slicer.util.saveNode(tempVolumeNode, imageDir+'/'+tempVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(tempVolumeNode)
        slicer.mrmlScene.RemoveNode(baselineNode)
        slicer.mrmlScene.RemoveNode(referenceNode)

        
def CalcScalingFactor(imageDir, echo1Name, echo2Name, ROIName):

    ## NOTE: We assume the T2* in the ROI is long enough to assume that intensities in image1 and image2 are supposed to be similar.
    image1File = echo1Name+'.nrrd'
    image2File = echo2Name+'.nrrd'
    ROIFile = ROIName+'.nrrd'

    if os.path.isfile(imageDir+'/'+image1File) and os.path.isfile(imageDir+'/'+image2File):
        (r, image1Node) = slicer.util.loadVolume(imageDir+'/'+image1File, {}, True)
        (r, image2Node) = slicer.util.loadVolume(imageDir+'/'+image2File, {}, True)
        (r, ROINode) = slicer.util.loadVolume(imageDir+'/'+ROIFile, {}, True)

        image1 = sitk.Cast(sitkUtils.PullFromSlicer(image1Node.GetID()), sitk.sitkFloat32)
        image2 = sitk.Cast(sitkUtils.PullFromSlicer(image2Node.GetID()), sitk.sitkFloat32)
        ROI = sitk.Cast(sitkUtils.PullFromSlicer(ROINode.GetID()), sitk.sitkUInt8)

        # Compute voxel-wise scaling factor
        scaleImage = sitk.Divide(image1, image2)

        #lslogic1 = LabelStatistics.LabelStatisticsLogic(image1Node, ROINode)
        #mean1 = lslogic1.labelStats[1,"Mean"]
        #
        #lslogic2 = LabelStatistics.LabelStatisticsLogic(image2Node, ROINode)
        #mean2 = lslogic2.labelStats[1,"Mean"]

        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(scaleImage, ROI)
        
        slicer.mrmlScene.RemoveNode(image1Node)
        slicer.mrmlScene.RemoveNode(image2Node)
        slicer.mrmlScene.RemoveNode(ROINode)

        scale = stats.GetMean(1)
        #intensitySD.append(stats.GetSigma(i))
        return scale
    else:
        print "ERROR: scaling factor"
        return -1.0
    

def CalcScalingFactorBatch(imageDir, imageIndices, prefixEcho1, prefixEcho2, ROIName):

    factors = numpy.array([])

    for idx in imageIndices:
        fileEcho1 = '%s%03d' % (prefixEcho1, idx)
        fileEcho2 = '%s%03d' % (prefixEcho2, idx)
        factor = CalcScalingFactor(imageDir, fileEcho1, fileEcho2, ROIName)
        print 'Scaling factor for %s%03d.nrrd: %f' % (prefixEcho1, idx, factor)
        if factor > 0.0:
            factors = numpy.append(factors, factor)
    print 'factor = %f +/- %f' % (numpy.mean(factors), numpy.std(factors))


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


def GenerateR2StarMaps(imageDir, imageIndices, prefixEcho1='echo1-', prefixEcho2='echo2-', TE1=0.00007, TE2=0.002, prefixT2Star='t2s-', prefixR2Star='r2s-', scaleFactor=0.7899):

    for idx in imageIndices:

        print 'processing %s/%s%03d.nrrd ...' % (imageDir, prefixEcho1, idx)

        fileEcho1 = '%s%03d' % (prefixEcho1, idx)
        fileEcho2 = '%s%03d' % (prefixEcho2, idx)
        fileR2Star = '%s%03d' % (prefixR2Star, idx)
        fileT2Star = '%s%03d' % (prefixT2Star, idx)

        ### Skip noise correction for now...
        #
        #echo1Noise = CalcNoise(imageDir, 'baseline-petra-echo1', 'fz1-max-petra-echo1', 'noise-roi-label')
        #if echo1Noise < 0:
        #    echo1Noise = CalcNoise(imageDir, 'baseline-petra-echo1', 'fz2-max-petra-echo1', 'noise-roi-label')
        #
        #echo2Noise = CalcNoise(imageDir, 'baseline-petra-echo2', 'fz1-max-petra-echo2', 'noise-roi-label')
        #if echo2Noise < 0:
        #    echo2Noise = CalcNoise(imageDir, 'baseline-petra-echo2', 'fz2-max-petra-echo2', 'noise-roi-label')
        #
        #CorrectNoise('baseline-petra-echo1', 'baseline-petra-echo1-nc', echo1Noise)
        #CorrectNoise('baseline-petra-echo2', 'baseline-petra-echo2-nc', echo2Noise)
        #CorrectNoise('fz1-max-petra-echo1', 'fz1-max-petra-echo1-nc', echo1Noise)
        #CorrectNoise('fz1-max-petra-echo2', 'fz1-max-petra-echo2-nc', echo2Noise)
        #CorrectNoise('fz2-max-petra-echo1', 'fz2-max-petra-echo1-nc', echo1Noise)
        #CorrectNoise('fz2-max-petra-echo2', 'fz2-max-petra-echo2-nc', echo2Noise)

        ## Intensity clibration for echoes 1 and 2
        CalcR2Star(imageDir, fileEcho1, fileEcho2, fileT2Star, fileR2Star, TE1, TE2, scaleFactor)


def SampleR2StarPerROI(imageDir, imageList, outputFile, ROIName='roi-label', prefixR2Star='r2s-'):

    imageIndices = imageList[0]
    imageTime = imageList[1]
    result = []
    i = 0
    
    for idx in imageIndices:
        print 'processing %s/%s%03d.nrrd ...' % (imageDir, prefixR2Star, idx)

        fileR2Star = '%s%03d' % (prefixR2Star, idx)
        stat = SampleIntensities(imageDir, fileR2Star, ROIName)
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


def GenerateNormalizedImage(imageDir, imageIndices, baselineIndex, prefixEcho1='echo1-'):

    baselineFile = '%s%03d.nrrd' % (prefixEcho1, baselineIndex)

    if not os.path.isfile(imageDir+'/'+baselineFile):
        print 'Error: Could not open file: %s' % baselineFile
        return False


    (r, baselineNode) = slicer.util.loadVolume(imageDir+'/'+baselineFile, {}, True)
    baselineImage = sitk.Cast(sitkUtils.PullFromSlicer(baselineNode.GetID()), sitk.sitkFloat32)

    for idx in imageIndices:

        print 'processing %s/%s%03d.nrrd ...' % (imageDir, prefixEcho1, idx)

        fileEcho1 = '%s%03d.nrrd' % (prefixEcho1, idx)
        if not os.path.isfile(imageDir+'/'+fileEcho1):
            print 'Error: Could not open file: %s' % fileEcho1
        else:
            (r, echo1Node) = slicer.util.loadVolume(imageDir+'/'+fileEcho1, {}, True)
            echo1Image = sitk.Cast(sitkUtils.PullFromSlicer(echo1Node.GetID()), sitk.sitkFloat32)
            normImage = sitk.Divide(echo1Image,baselineImage)
            
            normImageName = 'norm-%03d' % idx
            normVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
            slicer.mrmlScene.AddNode(normVolumeNode)
            normVolumeNode.SetName(normImageName)
            sitkUtils.PushToSlicer(normImage, normImageName, 0, True)

            normVolumeNode = slicer.util.getNode(normImageName)
            slicer.util.saveNode(normVolumeNode, imageDir+'/'+normImageName+'.nrrd') 
            slicer.mrmlScene.RemoveNode(normVolumeNode)

    return True
            

def SampleNormalizedIntensityPerROI(imageDir, imageList, outputFile, ROIName='roi-label', prefixNormImage='norm-'):

    imageIndices = imageList[0]
    imageTime = imageList[1]
    result = []
    i = 0
    
    for idx in imageIndices:
        print 'processing %s/%s%03d.nrrd ...' % (imageDir, prefixNormImage, idx)

        fileNormImage = '%s%03d' % (prefixNormImage, idx)
        stat = SampleIntensities(imageDir, fileNormImage, ROIName)
        row = stat[0]
        row[0] = imageTime[i]   # Replace intensity for index 0 with because it will not be used.
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

