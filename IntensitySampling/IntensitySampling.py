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
#import LabelStatistics

### Parameters
#workingDir = '/Users/junichi/Projects/Gyn/greg-2017-07-21-experiment/2017-11-17/IRTSE'
workingDir = '/Users/junichi/Projects/Gyn/greg-2017-07-21-experiment/2017-11-17/UTE-VFA'
outputFileName = 'Intensities.csv'
labelImageFile = 'sampling-label.nrrd'

imageFileList = [
    '143 UTE_WIP580_1echo FA5.nrrd',
    '144 UTE_WIP580_1echo FA10.nrrd',
    '145 UTE_WIP580_1echo FA15.nrrd',
    '146 UTE_WIP580_1echo FA20.nrrd',
    '147 UTE_WIP580_1echo FA1.nrrd',
    '148 UTE_WIP580_1echo FA2.nrrd',
    '149 UTE_WIP580_1echo FA3.nrrd',
    '150 UTE_WIP580_1echo FA4.nrrd',
    '151 UTE_WIP580_1echo FA6.nrrd'  
#    '163 TSE_T1_map TI198.nrrd',
#    '164 TSE_T1_map TI198.nrrd',
#    '165 TSE_T1_map TI490.nrrd',
#    '166 TSE_T1_map TI490.nrrd',
#    '167 TSE_T1_map TI108.nrrd',
#    '168 TSE_T1_map TI108.nrrd',
#    '169 TSE_T1_map TI896.nrrd',
#    '170 TSE_T1_map TI896.nrrd',
#    '171 TSE_T1_map TI80.nrrd',
#    '172 TSE_T1_map TI80.nrrd',
#    '173 TSE_T1_map TI1640.nrrd',
#    '174 TSE_T1_map TI1640.nrrd',
#    '175 TSE_T1_map TI363.nrrd',
#    '176 TSE_T1_map TI363.nrrd',
#    '177 TSE_T1_map TI146.nrrd',
#    '178 TSE_T1_map TI146.nrrd',
#    '179 TSE_T1_map TI663.nrrd',
#    '180 TSE_T1_map TI663.nrrd',
#    '181 TSE_T1_map TI268.nrrd',
#    '182 TSE_T1_map TI268.nrrd',
#    '183 TSE_T1_map TI24.nrrd',
#    '184 TSE_T1_map TI24.nrrd',
#    '185 TSE_T1_map TI2800.nrrd',
#    '186 TSE_T1_map TI2800.nrrd',
#    '187 TSE_T1_map TI50.nrrd',
#    '188 TSE_T1_map TI50.nrrd',
#    '189 TSE_T1_map TI2200.nrrd',
#    '190 TSE_T1_map TI2200.nrrd',
]
    
### Setup modules

### Open output file
outputFile = open(workingDir+'/'+outputFileName, 'w')
outputFile.write("Image,Index,Count,Min,Max,Mean,StdDev\n")

### Load label data
(r, labelNode) = slicer.util.loadVolume(workingDir+'/'+labelImageFile, {'singleFile' : True}, True)

for imageFile in imageFileList:

    print workingDir+'/'+imageFile
    if os.path.isfile(workingDir+'/'+imageFile):
        (r, imageNode) = slicer.util.loadVolume(workingDir+'/'+imageFile, {'singleFile' : True}, True)

        roiImage = sitk.Cast(sitkUtils.PullFromSlicer(labelNode.GetID()), sitk.sitkInt8)
        image    = sitk.Cast(sitkUtils.PullFromSlicer(imageNode.GetID()), sitk.sitkFloat32)

        labelStatistics = sitk.LabelStatisticsImageFilter()
        labelStatistics.Execute(image, roiImage)
        
        print 'analyzing %s' % imageFile

        #for i in lslogic.labelStats["Labels"]:
        #    outputFile.write("%s," % imageFile)
        #    outputFile.write("%f," % lslogic.labelStats[i,"Index"])
        #    outputFile.write("%f," % lslogic.labelStats[i,"Count"])
        #    outputFile.write("%f," % lslogic.labelStats[i,"Min"])
        #    outputFile.write("%f," % lslogic.labelStats[i,"Max"])
        #    outputFile.write("%f," % lslogic.labelStats[i,"Mean"])
        #    outputFile.write("%f\n" % lslogic.labelStats[i,"StdDev"])

        n = labelStatistics.GetNumberOfLabels()
        for i in range(1,n):
            outputFile.write("%s," % imageFile)  #imageFile
            outputFile.write("%f," % i)                           #Index
            outputFile.write("%f," % labelStatistics.GetCount(i))  #Count
            outputFile.write("%f," % labelStatistics.GetMinimum(i))    #Min
            outputFile.write("%f," % labelStatistics.GetMaximum(i))    #Max
            outputFile.write("%f," % labelStatistics.GetMean(i))   #Mean
            outputFile.write("%f\n"% labelStatistics.GetSigma(i))  #StdDev
            
        slicer.mrmlScene.RemoveNode(imageNode)

slicer.mrmlScene.RemoveNode(labelNode)

outputFile.close()
