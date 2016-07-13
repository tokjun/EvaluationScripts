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
import ComputeT2Star
import ComputeTempRelativeR2s
import ComputeTemp


### Parameters
#workingDir = '/Users/junichi/Experiments/UTE/UTE-Clinical/ISMRM2015/'

workingDir = '/home/develop/Projects/ISMRM2015/'
vimageDir = ''

TE1 = 0.00007  ## s
TE2 = 0.002    ## s
lowerThreshold = -1000000.0
upperThreshold =  1000000.0

TE1Array = {
    2 : 0.00007,
    5 : 0.00007,
    7 : 0.00007,
    8 : 0.00007,
    9 : 0.00007,
    10: 0.00007,
    11: 0.00008,
    12: 0.00008,
    15: 0.00007,
    16: 0.00007,
}


# Assume the unit for R2* data is s^-1
# Temp = A * R2Star + B
#paramA = -0.12820000
#paramBAbs = 56.667 # for absolute
#paramB = 34.231  # for relative R2*

##y = -7.56058 x + 456.872   #probeROIs <- c(2, 7, 14, 20)
#paramA = -0.13226
#paramBAbs = 60.428168 # for absolute
#paramB = 32.6525  # for relative R2*

#y = -11.1775 x + 347.195   #probeROIs <- c(2, 7, 13, 19)
paramA = -0.089465444
paramBAbs = 31.06195482 # for absolute
paramB = 12.2742  # for relative R2*

scaleFactor = 1.0  ## will be updated

scaleCalibrationR2s = 129.565 ## (s^-1) based on an ex-vivo 

#imageIndeces = [2, 5, 7, 8, 9, 10, 11, 12, 15, 16]
imageIndeces = [16]

#slicer.util.selectModule('LabelStatistics')

### Setup modules
#slicer.util.selectModule('ComputeT2Star')
T2StarLogic = ComputeT2Star.ComputeT2StarLogic()

#slicer.util.selectModule('ComputeTempRelativeR2s')
TempLogicRel = ComputeTempRelativeR2s.ComputeTempRelativeR2sLogic()
TempLogicAbs = ComputeTemp.ComputeTempLogic()


#LabelStatisticsLogic = slicer.modules.labelstatistics.logic()

resampleCLI = slicer.modules.brainsresample

def CalcNoise(image1Name, image2Name, ROIName):
    
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



def CalcScalingFactor(image1Name, image2Name, ROIName):

    image1File = image1Name+'.nrrd'
    image2File = image2Name+'.nrrd'
    ROIFile = ROIName+'.nrrd'
    
    if os.path.isfile(imageDir+'/'+image1File) and os.path.isfile(imageDir+'/'+image2File):
        (r, image1Node) = slicer.util.loadVolume(imageDir+'/'+image1File, {}, True)
        (r, image2Node) = slicer.util.loadVolume(imageDir+'/'+image2File, {}, True)
        (r, ROINode) = slicer.util.loadVolume(imageDir+'/'+ROIFile, {}, True)

        image1 = sitk.Cast(sitkUtils.PullFromSlicer(image1Node.GetID()), sitk.sitkFloat32)
        image2 = sitk.Cast(sitkUtils.PullFromSlicer(image2Node.GetID()), sitk.sitkFloat32)
        roiImage = sitk.Cast(sitkUtils.PullFromSlicer(ROINode.GetID()), sitk.sitkInt8)

        LabelStatistics = sitk.LabelStatisticsImageFilter()
        LabelStatistics.Execute(image1, roiImage)
        echo1 = LabelStatistics.GetMean(1)
        LabelStatistics.Execute(image2, roiImage)
        echo2 = LabelStatistics.GetMean(1)

        scale = echo1 / (echo2 * numpy.exp(scaleCalibrationR2s*(TE2-TE1)))

        slicer.mrmlScene.RemoveNode(image1Node)
        slicer.mrmlScene.RemoveNode(image2Node)
        slicer.mrmlScene.RemoveNode(ROINode)

        return (scale)

    else:

        print "ERROR: Could not calculate scaling factor"
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
        
        
def CalcR2Star(imageDir, firstEchoName, secondEchoName, t2StarName, r2StarName, echo1InputThreshold, echo2InputThreshold):

    firstEchoFile = firstEchoName+'.nrrd'
    secondEchoFile = secondEchoName+'.nrrd'
    print 'reading %s' % firstEchoFile

    if os.path.isfile(imageDir+'/'+firstEchoFile) and os.path.isfile(imageDir+'/'+secondEchoFile):
        (r, firstEchoNode) = slicer.util.loadVolume(imageDir+'/'+firstEchoFile, {}, True)
        (r, secondEchoNode) = slicer.util.loadVolume(imageDir+'/'+secondEchoFile, {}, True)

        r2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(r2StarVolumeNode)
        r2StarVolumeNode.SetName(r2StarName)

        noiseLevel = None
        outputThreshold = [lowerThreshold, upperThreshold]
        MinT2s = 0.000

        ## Skip inputThreshold because, in case of Delta R2* method, scale factor is not taken into account
        ## (it will be cancelled out), and if the echo 2 is larger than echo 1, R2* can be negative. 
        #inputThreshold = None
        inputThreshold = [echo1InputThreshold, echo2InputThreshold*scaleFactor]
        T2StarLogic.run(firstEchoNode, secondEchoNode, None, r2StarVolumeNode, TE1, TE2, scaleFactor, noiseLevel, outputThreshold, inputThreshold, MinT2s)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        r2StarVolumeNode = slicer.util.getNode(r2StarName)
        
        slicer.util.saveNode(r2StarVolumeNode, imageDir+'/'+r2StarVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(r2StarVolumeNode)

        slicer.mrmlScene.RemoveNode(firstEchoNode)
        slicer.mrmlScene.RemoveNode(secondEchoNode)
    
def CalcTempAbs(imageDir, echo1ImageName, echo2ImageName, tempName, echo1InputThreshold, echo2InputThreshold):

    echo1ImageFile = echo1ImageName+'.nrrd'
    echo2ImageFile = echo2ImageName+'.nrrd'

    if os.path.isfile(imageDir+'/'+echo1ImageFile) and os.path.isfile(imageDir+'/'+echo2ImageFile):
        (r, echo1ImageNode) = slicer.util.loadVolume(imageDir+'/'+echo1ImageFile, {}, True)
        (r, echo2ImageNode) = slicer.util.loadVolume(imageDir+'/'+echo2ImageFile, {}, True)

        tempVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(tempVolumeNode)
        tempVolumeNode.SetName(tempName)

        MinT2s = 0.001250
        noiseLevel = [0.0, 0.0]
        outputThreshold = [lowerThreshold, upperThreshold] 
        inputThreshold = [echo1InputThreshold, echo2InputThreshold*scaleFactor]

        TempLogicAbs.run(echo1ImageNode, echo2ImageNode, tempVolumeNode, TE1, TE2, scaleFactor, paramA, paramBAbs, noiseLevel, outputThreshold, inputThreshold, MinT2s) 

        tempVolumeNode = slicer.util.getNode(tempName)
        
        slicer.util.saveNode(tempVolumeNode, imageDir+'/'+tempVolumeNode.GetName()+'.nrrd')
        slicer.mrmlScene.RemoveNode(tempVolumeNode)
        slicer.mrmlScene.RemoveNode(echo1ImageNode)
        slicer.mrmlScene.RemoveNode(echo2ImageNode)


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

        transformName = ''
        if referenceName == 'fz1-max-r2s':
            transformName = 'T-fz1-max-to-baseline'
        else:
            transformName = 'T-fz2-max-to-baseline'

        if os.path.isfile(imageDir+'/'+transformName+'.h5'):
            print imageDir+'/'+transformName+'.h5'
            (r, transformNode) = slicer.util.loadTransform(imageDir+'/'+transformName+'.h5', True)
            resampleVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
            slicer.mrmlScene.AddNode(resampleVolumeNode)
            resampleVolumeNode.SetName(referenceName+'-REG-baseline')
            resampleParameters = {}
            resampleParameters["inputVolume"] = referenceNode.GetID()
            resampleParameters["outputVolume"] = resampleVolumeNode.GetID()
            resampleParameters["referenceVolume"] = baselineNode.GetID()
            resampleParameters["pixelType"] = "float"
            resampleParameters["warpTransform"] = transformNode.GetID()
            resampleParameters["interpolationMode"] = "Linear"
            resampleParameters["defaultValue"] = 0
            resampleParameters["numberOfThreads"] = -1
            slicer.cli.run(resampleCLI, None, resampleParameters, True)
            slicer.util.saveNode(resampleVolumeNode, imageDir+'/'+resampleVolumeNode.GetName()+'.nrrd')
            slicer.mrmlScene.RemoveNode(referenceNode)
            print referenceName+'-REG-baseline'
            referenceNode = slicer.util.getNode(referenceName+'-REG-baseline')
            slicer.mrmlScene.RemoveNode(transformNode)

        outputThreshold = [lowerThreshold, upperThreshold] 
        #inputThreshold = [800-175, 800-175]
        inputThreshold = [0.0, 1000]
        #inputThreshold = None
        TempLogicRel.run(baselineNode, referenceNode, tempVolumeNode, paramA, paramB, outputThreshold, inputThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        tempVolumeNode = slicer.util.getNode(tempName)
        
        slicer.util.saveNode(tempVolumeNode, imageDir+'/'+tempVolumeNode.GetName()+'.nrrd')
        slicer.mrmlScene.RemoveNode(tempVolumeNode)
        slicer.mrmlScene.RemoveNode(baselineNode)
        slicer.mrmlScene.RemoveNode(referenceNode)

def Resample(imageDir, intraopName, postopName, resampleName, transformName):
        
    intraopFile = intraopName+'.nrrd'
    postopFile = postopName+'.nrrd'
    print 'reading %s' % intraopFile

    r = False
    
    if os.path.isfile(imageDir+'/'+intraopFile)  and os.path.isfile(imageDir+'/'+postopFile):
        (r, intraopNode) = slicer.util.loadVolume(imageDir+'/'+intraopFile, {}, True)
        (r, postopNode) = slicer.util.loadVolume(imageDir+'/'+postopFile, {}, True)

        if os.path.isfile(imageDir+'/'+transformName+'.h5'):
            print imageDir+'/'+transformName+'.h5'
            (r, transformNode) = slicer.util.loadTransform(imageDir+'/'+transformName+'.h5', True)
            resampleVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
            slicer.mrmlScene.AddNode(resampleVolumeNode)
            resampleVolumeNode.SetName(resampleName)
            resampleParameters = {}
            resampleParameters["inputVolume"] = intraopNode.GetID()
            resampleParameters["outputVolume"] = resampleVolumeNode.GetID()
            resampleParameters["referenceVolume"] = postopNode.GetID()
            resampleParameters["pixelType"] = "float"
            resampleParameters["warpTransform"] = transformNode.GetID()
            resampleParameters["interpolationMode"] = "Linear"
            resampleParameters["defaultValue"] = 0
            resampleParameters["numberOfThreads"] = -1
            slicer.cli.run(resampleCLI, None, resampleParameters, True)
            slicer.util.saveNode(resampleVolumeNode, imageDir+'/'+resampleVolumeNode.GetName()+'.nrrd')
            slicer.mrmlScene.RemoveNode(resampleVolumeNode)
            slicer.mrmlScene.RemoveNode(transformNode)
            r = True
            
        slicer.mrmlScene.RemoveNode(intraopNode)
        slicer.mrmlScene.RemoveNode(postopNode)
            
    return r


for idx in imageIndeces:

    imageDir = '%s/cryo-%03d/' % (workingDir, idx)
    print 'processing %s ...' % imageDir

    TE1 = TE1Array[idx]

    print 'TE1 = %f' % TE1

    echo1Noise = CalcNoise('baseline-petra-echo1', 'fz1-max-petra-echo1', 'kidney-roi-label')
    if echo1Noise < 0:
        echo1Noise = CalcNoise('baseline-petra-echo1', 'fz2-max-petra-echo1', 'kidney-roi-label')

    echo2Noise = CalcNoise('baseline-petra-echo2', 'fz1-max-petra-echo2', 'kidney-roi-label')
    if echo2Noise < 0:
        echo2Noise = CalcNoise('baseline-petra-echo2', 'fz2-max-petra-echo2', 'kidney-roi-label')

    print 'Echo 1 noise: %f' % echo1Noise
    print 'Echo 2 noise: %f' % echo2Noise

    CorrectNoise('baseline-petra-echo1', 'baseline-petra-echo1-nc', echo1Noise)
    CorrectNoise('baseline-petra-echo2', 'baseline-petra-echo2-nc', echo2Noise)
    CorrectNoise('fz1-max-petra-echo1', 'fz1-max-petra-echo1-nc', echo1Noise)
    CorrectNoise('fz1-max-petra-echo2', 'fz1-max-petra-echo2-nc', echo2Noise)
    CorrectNoise('fz2-max-petra-echo1', 'fz2-max-petra-echo1-nc', echo1Noise)
    CorrectNoise('fz2-max-petra-echo2', 'fz2-max-petra-echo2-nc', echo2Noise)

    # Recaulcate scaling factor for absolute temperature methods
    scaleFactor = CalcScalingFactor('baseline-petra-echo1-nc', 'baseline-petra-echo2-nc', 'kidney-roi-label')
    print 'Scaling factor for baseline= %f' % scaleFactor
    if scaleFactor < 0.0:
        scaleFactor = CalcScalingFactor('fz1-max-petra-echo1-nc', 'fz1-max-petra-echo2-nc', 'kidney-roi-label')
        print 'Using scaling factor for fz1= %f' % scaleFactor
    if scaleFactor < 0.0:
        scaleFactor = CalcScalingFactor('fz2-max-petra-echo1-nc', 'fz2-max-petra-echo2-nc', 'kidney-roi-label')
        print 'Using scaling factor for fz2= %f' % scaleFactor
    
    CalcR2Star(imageDir, 'baseline-petra-echo1-nc', 'baseline-petra-echo2-nc', 'baseline-t2s', 'baseline-r2s', echo1Noise, echo2Noise)
    CalcR2Star(imageDir, 'fz1-max-petra-echo1-nc', 'fz1-max-petra-echo2-nc', 'fz1-max-t2s', 'fz1-max-r2s',     echo1Noise, echo2Noise)
    CalcR2Star(imageDir, 'fz2-max-petra-echo1-nc', 'fz2-max-petra-echo2-nc', 'fz2-max-t2s', 'fz2-max-r2s',     echo1Noise, echo2Noise)

    #CalcR2Star(imageDir, 'baseline-petra-echo1', 'baseline-petra-echo2', 'baseline-t2s', 'baseline-r2s', echo1Noise, echo2Noise)
    #CalcR2Star(imageDir, 'fz1-max-petra-echo1', 'fz1-max-petra-echo2', 'fz1-max-t2s', 'fz1-max-r2s', echo1Noise, echo2Noise)
    #CalcR2Star(imageDir, 'fz2-max-petra-echo1', 'fz2-max-petra-echo2', 'fz2-max-t2s', 'fz2-max-r2s', echo1Noise, echo2Noise)

    #scaleFactor = CalcScalingFactor('baseline-petra-echo1', 'baseline-petra-echo2', 'kidney-roi-label')
    #print 'Scaling factor for baseline= %f' % scaleFactor
    #if scaleFactor < 0.0:
    #    scaleFactor = CalcScalingFactor('fz1-max-petra-echo1', 'fz1-max-petra-echo2', 'kidney-roi-label')
    #    print 'Using scaling factor for fz1= %f' % scaleFactor
    #if scaleFactor < 0.0:
    #    scaleFactor = CalcScalingFactor('fz2-max-petra-echo1', 'fz2-max-petra-echo2', 'kidney-roi-label')
    #    print 'Using scaling factor for fz2= %f' % scaleFactor

    CalcTemp(imageDir,'baseline-r2s', 'fz1-max-r2s', 'fz1-temp')
    CalcTemp(imageDir,'baseline-r2s', 'fz2-max-r2s', 'fz2-temp')

    #CalcTempAbs(imageDir,'fz1-max-petra-echo1', 'fz1-max-petra-echo2', 'fz1-temp-abs', echo1Noise, echo2Noise)
    #CalcTempAbs(imageDir,'fz2-max-petra-echo1', 'fz2-max-petra-echo2', 'fz2-temp-abs', echo1Noise, echo2Noise)
    CalcTempAbs(imageDir,'fz1-max-petra-echo1-nc', 'fz1-max-petra-echo2', 'fz1-temp-abs', echo1Noise, echo2Noise)
    CalcTempAbs(imageDir,'fz2-max-petra-echo1-nc', 'fz2-max-petra-echo2', 'fz2-temp-abs', echo1Noise, echo2Noise)
    
    Resample(imageDir, 'fz1-temp', 'postop', 'fz1-temp-REG-postop', 'T-baseline-to-postop')
    Resample(imageDir, 'fz2-temp', 'postop', 'fz2-temp-REG-postop', 'T-baseline-to-postop')
    Resample(imageDir, 'fz1-temp-abs', 'postop', 'fz1-temp-abs-REG-postop', 'T-fz1-max-to-postop')
    Resample(imageDir, 'fz2-temp-abs', 'postop', 'fz2-temp-abs-REG-postop', 'T-fz2-max-to-postop')
    
    Resample(imageDir, 'fz1-max-haste', 'postop', 'fz1-max-haste-REG-postop', 'T-fz1-max-to-postop')
    Resample(imageDir, 'fz2-max-haste', 'postop', 'fz2-max-haste-REG-postop', 'T-fz2-max-to-postop')
    Resample(imageDir, 'fz1-max-vibe', 'postop', 'fz1-max-vibe-REG-postop', 'T-fz1-max-to-postop')
    Resample(imageDir, 'fz2-max-vibe', 'postop', 'fz2-max-vibe-REG-postop', 'T-fz2-max-to-postop')


