import argparse, sys, shutil, os, logging
import SimpleITK as sitk

#  Usage:
#
#    $ python3 BiasCorrectionByCoilElement.py \\
#        [-h] [-c NUMBEROFCONTROLPOINTS] [-t CONVERGENCETHRESHOLD]
#        [-b BSPLINEORDER] [-s SHRINKFACTOR] [-i NUMBEROFITERATIONS]
#        SRC_FILE_LIST DST_DIR
##
#  Aarguments:
#        SRC_FILE_LIST : A list of input files.
#        DST_DIR       : destination folder.')
#        -c numberOfControlPoints : Number of control points (default: 4,4,4)
#        -t convergenceThreshold  : Convergence threshold (default: 0.0001)
#        -b bSplineOrder          : B-Spline order (default: 3)
#        -s shrinkFactor          : Shring factor (default: 4)
#        -i numberOfIterations    : Number of iteration for each step (default: 50,40,30)
#
#  Dependencies:
#    This script calls SimpleITK API.
#


#
# Apply bias correction to individual volumes and combine
#
def applyBiasCorrection(loadedImageList, fileList, param):

    correctedImageList = []
    idx = 0

    print('========== Parameters ==========')
    print(param)
    print('================================')
    
    for inputImage in loadedImageList:

        srcFileName = fileList[idx]
        idx = idx + 1
        
        print('Processing image: ' + srcFileName)
        # Shrink factor
        image = sitk.Shrink(inputImage, [param['shrinkFactor']] * inputImage.GetDimension())
        
        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        # Number of control points
        corrector.SetNumberOfControlPoints(param['numberOfControlPoints'])
        corrector.SetMaximumNumberOfIterations(param['numberOfIterations'])
        corrector.SetSplineOrder(param['bsplineOrder'])
        output = corrector.Execute(image)
        log_bias_field = corrector.GetLogBiasFieldAsImage(inputImage)
        output = inputImage / sitk.Exp( log_bias_field )
        
        correctedImageList.append(output)

    return correctedImageList


def combinCorrectedImages(correctedImageList):
    
    sqrImage = None
    n = 0
    for image in correctedImageList:
        if sqrImage:
            sqrImage = sqrImage + sitk.Pow(image, 2)
        else:
            sqrImage = sitk.Pow(image, 2)
        n = n + 1
    rootMeanSqrImage = sitk.Sqrt(sqrImage / float(n))

    return rootMeanSqrImage


def loadImageList(filename):

    ### Load the image file list
    imageList = []

    try :
        inputFile = open(filename, 'r')
    except IOError:
        print("Could not load the image list file.\n")
        return None

    for imageFile in inputFile:
        #print ('list = ' + imageFile)
        imageFile = imageFile.replace('\n','')
        imageList.append(imageFile)

    return imageList


def loadImages(srcFileList):

    loadedImageList = []
    for srcFile in srcFileList:
        image = sitk.ReadImage(srcFile, sitk.sitkFloat32)
        if image == None:
            continue
        loadedImageList.append(image)

    return loadedImageList


def saveImages(imageList, srcFileList, dstDir):

    idx = 0
    for image in imageList:
        srcFilePath = srcFileList[idx]
        dir, srcFileName = os.path.split(srcFilePath)
        path = dstDir + "/" + 'N4_' + srcFileName
        print("Saving file: " + path)
        sitk.WriteImage(image, path)
        idx = idx + 1


def strToFloat(s):
    
    return float(s)

def strToInt(s):
    
    return int(s)

def strToIntArray(s):
    strArray = s.split(',')
    intArray = [int(d) for d in strArray]
    return intArray


def main(argv):

    args = []
    try:
        parser = argparse.ArgumentParser(description="Perform N4ITK Bias Correction for each coil element and combine.")
        parser.add_argument('src', metavar='SRC_FILE_LIST', type=str, nargs=1,
                            help='A list of input files.')
        parser.add_argument('dst', metavar='DST_DIR', type=str, nargs=1,
                            help='destination folder.')
        parser.add_argument('-c', dest='numberOfControlPoints', default='4,4,4',
                            help='Number of control points (default: 4,4,4)')
        parser.add_argument('-t', dest='convergenceThreshold', default='0.0001',
                            help='Convergence threshold (default: 0.0001)')
        parser.add_argument('-b', dest='bSplineOrder', default='3',
                            help='B-Spline order (default: 3)')
        parser.add_argument('-s', dest='shrinkFactor', default='4',
                            help='Shring factor (default: 4)')
        parser.add_argument('-i', dest='numberOfIterations', default='50,40,30',
                            help='Number of iteration for each step (default: 50,40,30)')

        args = parser.parse_args(argv)
        
    except Exception as e:
        print(e)
        sys.exit()

    srcFileListFile = args.src[0]
    dstDir = args.dst[0]
    # Make the destination directory, if it does not exists.
    os.makedirs(dstDir, exist_ok=True)

    numberOfControlPoints = strToIntArray(args.numberOfControlPoints)
    convergenceThreshold = strToFloat(args.convergenceThreshold)
    bSplineOrder = strToInt(args.bSplineOrder)
    shrinkFactor = strToInt(args.shrinkFactor)
    numberOfIterations = strToIntArray(args.numberOfIterations)
    
    param = {
        'numberOfControlPoints': numberOfControlPoints,
        'convergenceThreshold' : convergenceThreshold,
        'bsplineOrder'         : bSplineOrder,
        'shrinkFactor'         : shrinkFactor,
        'numberOfIterations'   : numberOfIterations
    }
    
    srcFileList = loadImageList(srcFileListFile)
    if not srcFileList:
        print("ERROR: Could not load the file list: " + srcFileListFile)
        sys.exit()
    
    loadedImageList = loadImages(srcFileList)
    if not loadedImageList:
        print("ERROR: Could not load the source files")
        sys.exit()
        
    correctedImageList = applyBiasCorrection(loadedImageList, srcFileList, param)
    saveImages(correctedImageList, srcFileList, dstDir)

    combinedImage = combinCorrectedImages(correctedImageList)
    saveImages([combinedImage], ['CombinedImage.nrrd'], dstDir)
    
        
if __name__ == "__main__":
  main(sys.argv[1:])

