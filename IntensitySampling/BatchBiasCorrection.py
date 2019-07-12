#
# Script to apply bias correction to the images on the list
# 
# Usage: On the Slicer's Python interactor, 
#
#   >>> execfile('/path/to/script/BatchBiasCorrection.py')
#   >>> BatchBiasCorrection(imageListFile, biasFieldImage, sourceDir, outputFile)
#      
# Arguements:
#
#   'imageListFile'
#      The path to a file that contains the list of input image files.
#      The bias image file is an output from N4ITK MRI Bias correction module.
#      (Specified as the "Output bias field image" parameter.)
#
#   'sourceDir'
#      The path to the folder that contains the image files.
#
#   'outputFile'
#      The path to the output file.
#

import os
import os.path
import unittest
import random
import math
import tempfile
import time
import numpy
import re
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import SimpleITK as sitk
import sitkUtils

def BatchBiasCorrectionPerImage(imageListFile, srcDir, destDir):
    
    ### Load the image file list
    try :
        inputFile = open(imageListFile, 'r')
    except IOError:
        print "Could not load the image list file.\n"
        return

    ### Load the bias field map
    (r, bfNode) = slicer.util.loadVolume(biasFieldImageFile, {'singleFile' : True}, True)
    
    if r == False:
        print "Could not load the bias field image.\n"
        return

    bfImage = sitk.Cast(sitkUtils.PullFromSlicer(bfNode.GetID()), sitk.sitkFloat32)

    for imageFile in inputFile:
        
        ### Load image data
        print "Processing "+srcDir+'/'+imageFile.rstrip()+"..."
        (r, imageNode) = slicer.util.loadVolume(srcDir+'/'+imageFile.rstrip(), {'singleFile' : True}, True)
            
        if r == False:
            print "Could not load the image.\n"
            continue

        outputName = imageFile.rstrip()
            
        image    = sitk.Cast(sitkUtils.PullFromSlicer(imageNode.GetID()), sitk.sitkFloat32)
        divideFilter = sitk.DivideRealImageFilter()
        correctedImage = divideFilter.Execute(image, bfImage)

        correctedImageNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(correctedImageNode)
        correctedImageNode.SetName(outputName)
        sitkUtils.PushToSlicer(correctedImage, correctedImageNode.GetName(), 0, True)
        correctedImageNode = slicer.util.getNode(outputName)
        slicer.util.saveNode(correctedImageNode, destDir+'/'+correctedImageNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(imageNode)
        slicer.mrmlScene.RemoveNode(correctedImageNode)
        
    slicer.mrmlScene.RemoveNode(bfNode)
    

def BatchBiasCorrection(imageListFile, biasFieldImageFile, srcDir, destDir):
    
    ### Load the image file list
    try :
        inputFile = open(imageListFile, 'r')
    except IOError:
        print "Could not load the image list file.\n"
        return

    ### Load the bias field map
    (r, bfNode) = slicer.util.loadVolume(biasFieldImageFile, {'singleFile' : True}, True)
    
    if r == False:
        print "Could not load the bias field image.\n"
        return

    bfImage = sitk.Cast(sitkUtils.PullFromSlicer(bfNode.GetID()), sitk.sitkFloat32)

    for imageFile in inputFile:
        
        ### Load image data
        print "Processing "+srcDir+'/'+imageFile.rstrip()+"..."
        (r, imageNode) = slicer.util.loadVolume(srcDir+'/'+imageFile.rstrip(), {'singleFile' : True}, True)
            
        if r == False:
            print "Could not load the image.\n"
            continue

        outputName = imageFile.rstrip()
            
        image    = sitk.Cast(sitkUtils.PullFromSlicer(imageNode.GetID()), sitk.sitkFloat32)
        divideFilter = sitk.DivideRealImageFilter()
        correctedImage = divideFilter.Execute(image, bfImage)

        correctedImageNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(correctedImageNode)
        correctedImageNode.SetName(outputName)
        sitkUtils.PushToSlicer(correctedImage, correctedImageNode.GetName(), 0, True)
        correctedImageNode = slicer.util.getNode(outputName)
        slicer.util.saveNode(correctedImageNode, destDir+'/'+correctedImageNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(imageNode)
        slicer.mrmlScene.RemoveNode(correctedImageNode)
        
    slicer.mrmlScene.RemoveNode(bfNode)
    


