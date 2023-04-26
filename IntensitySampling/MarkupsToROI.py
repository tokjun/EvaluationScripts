#!/usr/bin/env python3

import slicer
import numpy as np


#
# Generate a label map with ROIs at given points
#
#
#   Usage: On the Slicer's Python Interactor:
#       >>> exec(open("/path/to/MarkupsToROI.py").read())
#       >>> markupsToROI(markup_name, volume_name, label_name, roi_size=10, slice_dir=2)
#
#   Arguments:
#     markup_name
#         Name of the markups node
#     volume_name
#         Name of the volume node
#     label_name
#         Name of the label map node
#     roi_size=10
#         Size of the ROI in pixels. ROI is a square of size 2*roi_size+1
#     slice_dir
#         Direction of the slices where the ROIs will be placed
#


def markupsToROI(markups_node_name, volume_node_name, label_node_name, roi_size, slice_dir=2):

    # Get the markups node
    markups_node = slicer.util.getNode(markups_node_name)

    # Get the volume node
    volume_node = slicer.util.getNode(volume_node_name)

    # Get numpy array of volume
    volume_array = slicer.util.arrayFromVolume(volume_node)

    # Create a new numpy array for the label map
    label_array = np.zeros(volume_array.shape)

    N = markups_node.GetNumberOfControlPoints()

    ijkMat = vtk.vtkMatrix4x4()
    volume_node.GetRASToIJKMatrix(ijkMat)

    # Convert slice_dir to Numpy array index
    #
    slice_dir = 2-slice_dir

    for i in range(N):
        p = list(markups_node.GetNthControlPointPosition(i))
        p.append(1.0)
        p_ijk = list(ijkMat.MultiplyPoint(p))
        p_ijk = np.round(p_ijk)
        p_ijk = p_ijk.astype(int)

        n_slices = label_array.shape[slice_dir]
        for sl in range(n_slices):
            label = sl*N+i+1
            if slice_dir == 0:
                label_array[sl,
                             p_ijk[1]-roi_size:p_ijk[1]+roi_size,
                             p_ijk[0]-roi_size:p_ijk[0]+roi_size] = label
            elif slice_dir == 1:
                label_array[p_ijk[2]-roi_size:p_ijk[2]+roi_size,
                             sl,
                             p_ijk[0]-roi_size:p_ijk[0]+roi_size] = label
            else:
                label_array[p_ijk[2]-roi_size:p_ijk[2]+roi_size,
                             p_ijk[1]-roi_size:p_ijk[1]+roi_size,
                             sl] = label

    # create volume node from numpy array
    label_node = addVolumeFromArray(label_array, ijkToRAS=None, name=label_node_name, nodeClassName='vtkMRMLLabelMapVolumeNode')
    #label_node = slicer.util.arrayToVolume(label_array, label_node_name, start_with_zero=True)

    label_node.SetSpacing(volume_node.GetSpacing())
    label_node.SetOrigin(volume_node.GetOrigin())
    matrix = vtk.vtkMatrix4x4()
    volume_node.GetIJKToRASMatrix(matrix)
    label_node.SetIJKToRASMatrix(matrix)
