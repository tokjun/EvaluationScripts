#
# Script to sample intensity values in ROIs defined by a label map
# 
# Usage: On the Slicer's Python interactor, 
#
#   >>> execfile('/path/to/script/IntensitySampling.py')
#   >>> IntensitySampling(imageListFile, sourceDir, outputFile)
#      
# Arguements:
#
#   'imageListFile'
#      The path to a file that contains the list of input image files.
#      The first line must be the name of the label map, whereas the rest
#      are the names of image files to be sampled. One file per line.
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

def IntensitySampling(imageListFile, sourceDir, outputFile):
    
    ### Open output file
    outputFile = open(outputFile, 'w')
    outputFile.write("Image,Series,Index,Count,Min,Max,Mean,StdDev\n")

    ### Load the image file list
    try :
        inputFile = open(imageListFile, 'r')
    except IOError:
        print("Could not load the image list file.\n")
        return

    ### Load the label map
    lmap = inputFile.readline().rstrip()
    print(lmap)
    (r, labelNode) = slicer.util.loadVolume(sourceDir+'/'+lmap, {'singleFile' : True}, True)
    
    if r == False:
        print("Could not load the label map.\n")
        return

    roiImage = sitk.Cast(sitkUtils.PullFromSlicer(labelNode.GetID()), sitk.sitkInt8)

    for imageFile in inputFile:
        
        ### Load image data
        print("Processing "+sourceDir+'/'+imageFile.rstrip()+"...")
        (r, imageNode) = slicer.util.loadVolume(sourceDir+'/'+imageFile.rstrip(), {'singleFile' : True}, True)
            
        if r == False:
            print("Could not load the image.\n")
            continue
            
        image    = sitk.Cast(sitkUtils.PullFromSlicer(imageNode.GetID()), sitk.sitkFloat32)
        labelStatistics = sitk.LabelStatisticsImageFilter()
        labelStatistics.Execute(image, roiImage)
            
        n = labelStatistics.GetNumberOfLabels()
        
        # Detect series number (assuming that the series number comes at the begining of NRRD file name
        imagename = imageFile.rstrip()
        res = re.split(' ', imagename)
        if res[0].isdigit():
            series = res[0]
        else:
            series = -1
            
        for i in range(1,n):
            outputFile.write("%s," % imagename)  #imageFile
            outputFile.write("%s," % series)  #imageFile
            outputFile.write("%d," % i)                           #Index
            outputFile.write("%f," % labelStatistics.GetCount(i))  #Count
            outputFile.write("%f," % labelStatistics.GetMinimum(i))    #Min
            outputFile.write("%f," % labelStatistics.GetMaximum(i))    #Max
            outputFile.write("%f," % labelStatistics.GetMean(i))   #Mean
            outputFile.write("%f\n"% labelStatistics.GetSigma(i))  #StdDev
                
        slicer.mrmlScene.RemoveNode(imageNode)
        
    slicer.mrmlScene.RemoveNode(labelNode)
    outputFile.close()
    


