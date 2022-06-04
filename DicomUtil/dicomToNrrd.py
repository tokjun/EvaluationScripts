import argparse, sys, shutil, os, logging
import numpy as np
import sqlite3
import pydicom
import nrrd


#  Usage:
#
#  $ /path/to/Slicer  --no-main-window --no-splash --python-script splitSeriesByTag.py  \\
#         [-h] [-r] TAG [TAG ...] SRC_DIR DST_DIR
#
#  Aarguments:
#         TAG:       DICOM Tag (see below)
#         SRC_DIR:   Source directory that contains DICOM files.
#         DST_DIR:   Destination directory to save NRRD files.
#
#  Dependencies:
#  This script calls functions in dicom_separate_by_tag.py. Make sure to include the path
#  to the script in the PYTHONPATH environment variable.
#
#  Examples of DICOM Tags:
#   - General
#    - (0008,103e) : SeriesDescription
#    - (0010,0010) : PatientsName
#    - (0020,0010) : StudyID
#    - (0020,0011) : SeriesNumber
#    - (0020,0037) : ImageOrientationPatient
#    - (0008,0032) : AcquisitionTime
#   
#   - Siemens MR Header
#    - (0051,100f) : Coil element (Siemens)
#    - (0051,1016) : Real/Imaginal (e.x. "R/DIS2D": real; "P/DIS2D": phase)


#
# Match DICOM attriburtes
#
def getDICOMAttribute(path, tags):

    dataset = None
    try:
        dataset = pydicom.dcmread(path, specific_tags=None)
    except pydicom.errors.InvalidDicomError:
        print("Error: Invalid DICOM file: " + path)
        return None

    insertStr = ''
    for tag in tags:
        key = tag.replace(',', '')
        if key in dataset:
            element = dataset[key]
            if insertStr == '':
                insertStr = "'" + str(element.value) + "'"
            else:
                insertStr = insertStr + ',' + "'" + str(element.value) + "'"
                
    return insertStr;


#
# Convert attribute to folder name (Remove special characters that cannot be
# included in a path name)
#
def removeSpecialCharacter(v):

    input = str(v) # Make sure that the input parameter is a 'str' type.
    removed = input.translate ({ord(c): "-" for c in "!@#$%^&*()[]{};:/<>?\|`="})

    return removed


#
# Concatenate column names
#
def concatColNames(tags):

    r = ''
    for tag in tags:
        key = tag.replace(',', '')
        if r == '':
            r = 'x' + key + ' text'
        else:
            r = r + ',' + 'x' + key + ' text'
    return r;
    
#
# Build a file path database based on the DICOM tags
#
def buildFilePathDBByTags(con, srcDir, tags, fRecursive=True):

    # Create a table
    con.execute('CREATE TABLE dicom (' + concatColNames(tags) + ',path text)')

    filePathList = []
    postfix = 0
    attrList = []
    
    print("Processing directory: %s..." % srcDir)
    
    for root, dirs, files in os.walk(srcDir):
        for file in files:
            srcFilePath = os.path.join(root, file)
            insertStr = getDICOMAttribute(srcFilePath, tags)
            if insertStr == None:
                print("Could not obtain attributes for %s" % srcFilePath)
                continue
            else:
                # Add the file path
                insertStr = insertStr + ',' + "'" + srcFilePath + "'"
                con.execute('INSERT INTO dicom VALUES (' + insertStr + ')')
                #print('INSERT INTO dicom VALUES (' + insertStr + ')')
    
        if fRecursive == False:
            break
        
    con.commit()


def exportNrrd(filelist):
    # Obtain the image info from the first image

    nSlices = len(filelist)

    # Generate a list of slice positions
    slices = []
    for i in range(nSlices):
        dataset = None
        try:
            dataset = pydicom.dcmread(filelist[i], specific_tags=None)
        except pydicom.errors.InvalidDicomError:
            print("Error: Invalid DICOM file: " + path)
            return None

        try:
            rescaleIntercept = dataset['00281052'].value  # RescaleIntercept (b)
            rescaleSlope     = dataset['00281053'].value  # RescaleSlope     (m)  U = m*SV + b
        except KeyError:
            rescaleIntercept = 0
            rescaleSlope     = 1

        sl = {
            'position'       : np.array(dataset['00200032'].value), # ImagePositionPatient
            'orientation'    : np.array(dataset['00200037'].value), # ImageOrientationPatient
            'spacing'        : np.array(dataset['00280030'].value), # PixelSpacing
            'sliceThickness' : dataset['00180050'].value, # SliceThickness
            'rows'           : dataset['00280010'].value, # Rows
            'columns'        : dataset['00280011'].value, # Columns
            'sliceLocation'  : dataset['00201041'].value, # SliceLocation
            'bitsAllocated'  : dataset['00280100'].value, # BitsAllocated
            'instanceNumber' : dataset['00200013'].value, # InstanceNumber -- image number
            }
        if rescaleIntercept >= 0:
            sl['pixelArray'] = dataset.pixel_array*rescaleSlope + rescaleIntercept
        else:
            sl['pixelArray'] = (dataset.pixel_array*rescaleSlope + rescaleIntercept).astype('int16')
            

        
        slices.append(sl)

    # Sort the slices
    def keyfunc(e):
        return e['sliceLocation']

    slices.sort(key=keyfunc)

    # Generate a 3D matrix
    data = np.array([])

    print(slices[0]['pixelArray'].dtype)
    data = np.atleast_3d(np.transpose(slices[0]['pixelArray']))
    for sl in slices[1:]:
        data = np.append(data, np.atleast_3d(np.transpose(sl['pixelArray'])), axis=2)
        
    
    #data = data.reshape((slices[0]['columns'], slices[0]['rows'], len(slices)))
        
    seriesNumber            = dataset['00200011'].value # (0020,0011) : SeriesNumber
    print(seriesNumber)

    sliceSpacing = slices[1]['sliceLocation'] - slices[0]['sliceLocation']
    spacing = slices[0]['spacing']
    spacing = np.append(spacing, sliceSpacing)
    print(spacing)

    norm = slices[0]['orientation'].reshape((2,3))
    norm = np.append(norm, np.cross(norm[0], norm[1]).reshape((1,3)), axis=0)
    norm = np.transpose(norm)

    header = {}
    header['space directions'] = np.transpose(norm * spacing)
    header['space origin'] = slices[0]['position']

    nbytes = slices[0]['bitsAllocated'] / 8
    nrrdType = ''
    if nbytes == 1:
        nrrdType = 'int8'
    elif nbytes == 2:
        nrrdType = 'short'
    elif nbytes == 4:
        nrrdType = 'int'

    #header['type']      = nrrdType
    #header['dimension'] = 3
    header['space']     = 'left-posterior-superior'
    header['kinds']      = ['domain', 'domain', 'domain']
    header['encoding']  = 'raw'

    seriesDescription       = dataset['0008103e'].value # (0008,103e) : SeriesDescription
    patientsName            = dataset['00100010'].value # (0010,0010) : PatientsName
    studyID                 = dataset['00200010'].value # (0020,0010) : StudyID
    seriesNumber            = dataset['00200011'].value # (0020,0011) : SeriesNumber
    imageOrientationPatient = dataset['00200037'].value # (0020,0037) : ImageOrientationPatient
    acquisitionTime         = dataset['00080032'].value # (0008,0032) : AcquisitionTime
    #print('%s: %s\t%s\t%s\t%d\n' % (seriesNumber, seriesDescription, imageOrientationPatient, acquisitionTime, nSlices))
    #print('%s: %s\t%s\n' % (seriesNumber, pos[0], ori[0]))

    nrrd.write('output%d.nrrd' % seriesNumber, data, header)


    
def groupSeriesAndExport(cur, tags, valueListDict, cond=None, filename=None):

    if len(tags) == 0:
        cur.execute('SELECT path FROM dicom WHERE ' + cond)
        paths = cur.fetchall()
        if len(paths) == 0:
            return
        filelist = []
        for p in paths:
            filelist.append(str(p[0]))
            
        exportNrrd(filelist)

        return

    # Note: We add prefix 'x' to the DICOM tag as the DICOM tags are recognized as intenger
    #       by SQLight
    tag = 'x' + tags[0].replace(',', '')
    values = list(valueListDict[tag])
    tags2 = tags[1:]
    
    for tp in values:
        value = tp[0]
        cond2 = ''
        filename2 = ''
        if cond==None:
            cond2 = tag + ' == ' + "'" + value + "'"
        else:
            cond2 = cond + ' AND ' + tag + ' == ' + "'" + value + "'"
        if filename==None:
            filename2 = 'OUT-' + value
        else:
            filename2 = filename + '-' + value
        groupSeriesAndExport(cur, tags2, valueListDict, cond2, filename2)


def main(argv):
    
    try:
        parser = argparse.ArgumentParser(description="Split DICOM series by Tag.")
        parser.add_argument('tags', metavar='TAG', type=str, nargs='+',
                            help='DICOM tags(e.g. "0020,000E")')
        parser.add_argument('src', metavar='SRC_DIR', type=str, nargs=1,
                            help='source directory')
        #parser.add_argument('dst', metavar='DST_DIR', type=str, nargs=1,
        #                    help='destination directory')
        parser.add_argument('-r', dest='recursive', action='store_const',
                            const=True, default=False,
                            help='search the source directory recursively')
        args = parser.parse_args(argv)

    except Exception as e:
        print(e)

    tags   = args.tags
    srcdir = args.src[0]

    con = sqlite3.connect(':memory:')
    #con = sqlite3.connect('TestDB.db')
    cur = con.cursor()
    
    buildFilePathDBByTags(con, srcdir, tags, True)
     
    # Generate a list of values for each tag
    valueListDict = {}
    for tag in tags:
        colName = 'x' + tag.replace(',', '')
        cur.execute('SELECT ' + colName + ' FROM dicom GROUP BY ' + colName)
        valueListDict[colName] = cur.fetchall()
    
    groupSeriesAndExport(cur, tags, valueListDict, None, None)

    sys.exit()

if __name__ == "__main__":
  main(sys.argv[1:])



