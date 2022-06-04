#
# Script to sample intensity values in ROIs defined by a label map
# 
# Usage: On the Slicer's Python interactor, 
#
#   >>> execfile('/path/to/script/ClosePackingSphere.py')
# or, if execfile() is not available,
#   >>> exec(open('/path/to/script/ClosePackingSphere.py').read())
# then
#   >>> PackEqualSpheres()
#      
# Arguements:

import math
import numpy as np
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import SimpleITK as sitk
import sitkUtils

def placeSphericalModels(modelNode, posArray, radius, thRes=10, phRes=10):

  apd = vtk.vtkAppendPolyData()
    
  for pos in posArray:
    
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius)
    sphere.SetCenter(pos)
    sphere.SetThetaResolution(thRes)
    sphere.SetPhiResolution(phRes)
    sphere.Update()
    apd.AddInputConnection(sphere.GetOutputPort())
        
  apd.Update()
  modelNode.SetAndObservePolyData(apd.GetOutput())


def generateSimpleHCPLattice(origin, radius, size):

    posArray = []

    for i in range(0,size[0]):
      for j in range(0,size[1]):
        for k in range(0,size[2]):
          pos = [0.0]*3
          pos[0] = origin[0] + (2.0*i + float((j + k) % 2)) * radius
          pos[1] = origin[1] + (np.sqrt(3) * (j + (k % 2)/3.0)) * radius
          pos[2] = origin[2] + (2.0 * np.sqrt(6) * k / 3.0) * radius
          posArray.append(pos)

    return posArray
    

def packEqualSpheres(origin, distance, radius, size, thRes=10, phRes=10):

  #origin = [0.0, 0.0, 0.0]
  #distance = 5.0
  #radius = 4.0
  #size = [10, 10, 10]
  posArray = generateSimpleHCPLattice(origin, distance, size)
  
  modelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
  modelNode.SetName('ClosePackedSpheres')
  
  placeSphericalModels(modelNode, posArray, radius, thRes, phRes)
  


