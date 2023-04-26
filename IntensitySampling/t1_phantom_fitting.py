#!/usr/bin/env python3
import numpy as np
import csv
import matplotlib.pyplot as plt

from scipy.optimize import curve_fit

import json
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

def IntensitySamplingParam(imageParamJSON, labelMapName, paramKey):

    with open(imageParamJSON, 'r') as json_file:
        paramList = json.load(json_file)

    ### Load the label map
    label_node = slicer.util.getNode(labelMapName)
    label_image = sitk.Cast(sitkUtils.PullVolumeFromSlicer(label_node.GetID()), sitk.sitkInt16)

    outputDict = {}


    ### Load the image file list
    for key, param in paramList.items():
        volume_node = slicer.util.getNode(key)
        p = param[paramKey]

        image    = sitk.Cast(sitkUtils.PullVolumeFromSlicer(volume_node.GetID()), sitk.sitkFloat32)
        labelStatistics = sitk.LabelStatisticsImageFilter()
        labelStatistics.Execute(image, label_image)

        n = labelStatistics.GetNumberOfLabels()

        dictLabel = {}

        for i in range(1,n): # Exclude '0' (background)
            stat = {}
            stat['Count'] = labelStatistics.GetCount(i)
            stat['Min'] = labelStatistics.GetMinimum(i)
            stat['Max'] = labelStatistics.GetMaximum(i)
            stat['Mean'] = labelStatistics.GetMean(i)
            stat['StdDev'] = labelStatistics.GetSigma(i)
            dictLabel[i] = stat

        if p in outputDict:
            print('WARNING: Duplicate parameter value found, possibly a repeated experiment. : ' + p)
        outputDict[p] = dictLabel


    return outputDict


def func(x, T1, Iinf, p):

    return Iinf * np.abs(1.0-p*np.exp(-x/T1))


def T1fitting(title, x, y):

    popt, pcov = curve_fit(func, x, y, bounds=([0.0, 0.0, 1.5], [5000, 1500, 2.5]))
    #popt, pcov = curve_fit(func, x, y, bounds=([0.0, 0.0, 1.79], [5000, 1500, 1.8]))
    print(title + ': T1 = %f ms, Iinf=%f, p=%f' % tuple(popt))
    return popt


def processROI(imageParamJSON, labelMapName, paramKey):

    dataDict = IntensitySamplingParam(imageParamJSON, labelMapName, paramKey)

    x_array = []
    y_array_dict = {}
    sd_array_dict = {}
    for key in dataDict.keys():
        x_array.append(float(key))
        dictLabel = dataDict[key]
        for l, v in dictLabel.items():
            if l in y_array_dict:
                y_array_dict[l].append(v['Mean'])
                sd_array_dict[l].append(v['StdDev'])
            else:
                y_array_dict[l] = [v['Mean']]
                sd_array_dict[l] = [v['StdDev']]

    t1_list = {}
    sd_list = {}
    for l in y_array_dict.keys():
        popt = T1fitting('ROI ' + str(int(l)), x_array, y_array_dict[l])
        t1_list[l] = popt[0]
        sd_list[l] = numpy.mean(sd_array_dict[l])

    return (t1_list, sd_list)
    # plt.plot(xx, func(xx, *popt), 'r-', label='T1=%f ms' % popt[0])
    # plt.plot(x_array, y_array_dict[l], 'x')
    # plt.xlabel('TI (ms)')
    # plt.ylabel('Intensity')
    # plt.legend()
    # plt.show()


def exportCSV(t1_list, csv_file, n_samples):

    outputFile = open(csv_file, 'w')


    # Sort the T1 list by sample #
    t1_by_sample = {}
    for l in t1_list.keys():
        sample = l % n_samples + 1
        sl = int(l / n_samples)
        if sl == 0:
            sl = 12
        if sample not in t1_by_sample:
            t1_by_sample[sample] = {}
        t1_by_sample[sample][sl] = t1_list[l]

    samples = sorted(t1_by_sample.keys())
    outputFile.write("Slice")
    for sample in samples:
        outputFile.write(",%d" % sample)
    outputFile.write("\n")

    slices = sorted(t1_by_sample[1].keys())
    for sl in slices:
        outputFile.write("%s" % sl)
        for sample in samples:
            outputFile.write(",%s" % t1_by_sample[sample][sl])
        outputFile.write("\n")

    outputFile.close()

