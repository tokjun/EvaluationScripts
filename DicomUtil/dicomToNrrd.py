# import argparse, sys, shutil, os, logging
# import argparse, sys, os
import argparse
import sys
import os
import numpy as np
import sqlite3
import pydicom
import nrrd
import json


#  Usage:
#
#  $ python splitSeriesByTag.py  [-h] [-r] TAG [TAG ...] SRC_DIR DST_DIR
#
#  Aarguments:
#         TAG:       DICOM Tag (see below)
#         SRC_DIR:   Source directory that contains DICOM files.
#         DST_DIR:   Destination directory to save NRRD files.
#
#  Dependencies:
#  This script requires 'pydicom' and 'pynrrd.'
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
# A list of DICOM tags exlucded from the json file.
#

dicomGroupsExcluded = [
    '0010'      # patient personal informatoin
]

dicomTagsExcluded = [
    '00080080',  # (0008, 0080) Institution Name
    '00080081',  # (0008, 0081) Institution Address
    '00080090',  # (0008, 0090) Referring Physician's Name
    '00081010',  # (0008, 1010) Station Name
    '00081040',  # (0008, 1040) Institutional Department Name
    '00081048',  # (0008, 1048) Physician(s) of Record
    '00081050',  # (0008, 1050) Performing Physician's Name
    '00081070',  # (0008, 1070) Operators' Name
    '00080100',  # (0008, 0100) Code Value                          SH: 'AMIGO.RAD.MR'
    '00080102',  # (0008, 0102) Coding Scheme Designator            SH: 'L'
    '00080104',  # (0008, 0104) Code Meaning                        LO: 'AMIGO MRI (RAD-LED)'
    '00081140',  # (0008, 1140)  Referenced Image Sequence  3 item(s) ----
    '00081150',  # (0008, 1150) Referenced SOP Class UID            UI: MR Image Storage
    '00081155',  # (0008, 1155) Referenced SOP Instance UID         UI: 1.3.12.2.1107.5.2.36.162041.2022120809082924650415540
    '00081150',  # (0008, 1150) Referenced SOP Class UID            UI: MR Image Storage
    '00081155',  # (0008, 1155) Referenced SOP Instance UID         UI: 1.3.12.2.1107.5.2.36.162041.2022120808180867522809923
    '00081150',  # (0008, 1150) Referenced SOP Class UID            UI: MR Image Storage
    '00081155',  # (0008, 1155) Referenced SOP Instance UID         UI: 1.3.12.2.1107.5.2.36.162041.2022120809033775878915112
    '00191012',  # (0019, 1012) [TablePositionOrigin]
    '00191013',  # (0019, 1013) [ImaAbsTablePosition]
    '00191014',  # (0019, 1014) [ImaRelTablePosition]
    '00191015',  # (0019, 1015) [SlicePosition_PCS]
    '00200032',  # (0020, 0032) Image Position (Patient)
    '00200037',  # (0020, 0037) Image Orientation (Patient)
    '00200052',  # (0020, 0052) Frame of Reference UID
    '00201040',  # (0020, 1040) Position Reference Indicator
    '00201041',  # (0020, 1041) Slice Location
    '00200013',  # (0020, 0013) InstanceNumber -- image number
    '00321032',  # (0032, 1032) Requesting Physician                PN: 'TUNCALI^KEMAL^^^MD'
    '00321060',  # (0032, 1060) Requested Procedure Description     LO: 'AMIGO MRI (RAD-LED)'
    '00321064',  # (0032, 1064)  Requested Procedure Code Sequence  1 item(s) ----
    '00080100',  # (0008, 0100) Code Value                          SH: 'AMIGO.RAD.MR'
    '00080102',  # (0008, 0102) Coding Scheme Designator            SH: 'L'
    '00080104',  # (0008, 0104) Code Meaning                        LO: 'AMIGO MRI (RAD-LED)'
    '00380050',  # (0038, 0050) Special Needs                       LO: 'None [1]'
    '00400244',  # (0040, 0244) Performed Procedure Step Start Date DA: '20221208'
    '00400245',  # (0040, 0245) Performed Procedure Step Start Time TM: '072012.359000'
    '00400253',  # (0040, 0253) Performed Procedure Step ID         SH: 'E8781250'
    '00400254',  # (0040, 0254) Performed Procedure Step Descriptio LO: 'AMIGO MRI (RAD-LED)'
    '00400275',  # (0040, 0275)  Request Attributes Sequence  1 item(s) ----
    '00400007',  # (0040, 0007) Scheduled Procedure Step Descriptio LO: 'AMIGO MRI (RAD-LED)'
    '00400008',  # (0040, 0008)  Scheduled Protocol Code Sequence  1 item(s) ----
    '00400009',  # (0040, 0009) Scheduled Procedure Step ID         SH: 'E8781250'
    '00401001',  # (0040, 1001) Requested Procedure ID              SH: '1075085858'
    '00400280',  # (0040, 0280) Comments on the Performed Procedure ST: ''
    '7fe00010'   # (7fe0, 0010) Pixel Data
    ]

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
        value = ''
        if key in dataset:
            element = dataset[key]
            value = element.value

        if insertStr == '':
            insertStr = "'" + str(value) + "'"
        else:
            insertStr = insertStr + ',' + "'" + str(value) + "'"
    return insertStr;


#
# Convert attribute to folder name (Remove special characters that cannot be
# included in a path name)
#
def removeSpecialCharacter(v):

    input = str(v)  # Make sure that the input parameter is a 'str' type.
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
    return r


#
# Build a file path database based on the DICOM tags
#
def buildFilePathDBByTags(con, srcDir, tags, fRecursive=True):

    # Create a table
    con.execute('CREATE TABLE dicom (' + concatColNames(tags) + ',path text)')

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

        if fRecursive is False:
            break

    con.commit()


def exportNrrd(filelist, dst=None, filename=None):
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

        try:
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
        except KeyError:
            print('KeyError: Missing geometric information. Skipping.')
            return None

        if rescaleIntercept >= 0:
            sl['pixelArray'] = dataset.pixel_array*rescaleSlope + rescaleIntercept
        else:
            sl['pixelArray'] = (dataset.pixel_array*rescaleSlope + rescaleIntercept).astype('int16')

        slices.append(sl)

    # Sort the slices
    def keyfunc(e):
        return e['sliceLocation']

    slices.sort(key=keyfunc)
    if int(slices[0]['instanceNumber']) >  int(slices[-1]['instanceNumber']):
        slices.sort(reverse=True, key=keyfunc)

    # Generate a 3D matrix
    data = np.array([])

    data = np.atleast_3d(np.transpose(slices[0]['pixelArray']))
    for sl in slices[1:]:
        data = np.append(data, np.atleast_3d(np.transpose(sl['pixelArray'])), axis=2)
        print(str(sl['sliceLocation']) + ' ' + str(sl['instanceNumber']))

    # data = data.reshape((slices[0]['columns'], slices[0]['rows'], len(slices)))

    seriesNumber = dataset['00200011'].value  # (0020,0011) : SeriesNumber

    sliceSpacing = sl['sliceThickness']  # for a single slice image
    if len(slices) > 1:                  # for a multi-slice image
        sliceSpacing = slices[1]['sliceLocation'] - slices[0]['sliceLocation']

    spacing = slices[0]['spacing']
    spacing = np.append(spacing, sliceSpacing)

    norm = slices[0]['orientation'].reshape((2,3))
    norm = np.append(norm, np.cross(norm[1],norm[0]).reshape((1,3)), axis=0)
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
    header['space']    = 'left-posterior-superior'
    header['kinds']    = ['domain', 'domain', 'domain']
    header['encoding'] = 'raw'

    seriesDescription       = dataset['0008103e'].value  # (0008,103e) : SeriesDescription
    patientsName            = dataset['00100010'].value  # (0010,0010) : PatientsName
    studyID                 = dataset['00200010'].value  # (0020,0010) : StudyID
    seriesNumber            = dataset['00200011'].value  # (0020,0011) : SeriesNumber
    imageOrientationPatient = dataset['00200037'].value  # (0020,0037) : ImageOrientationPatient
    acquisitionTime         = dataset['00080032'].value  # (0008,0032) : AcquisitionTime
    #print('%s: %s\t%s\t%s\t%d\n' % (seriesNumber, seriesDescription, imageOrientationPatient, acquisitionTime, nSlices))
    #print('%s: %s\t%s\n' % (seriesNumber, pos[0], ori[0]))

    if filename == None:
        filename = 'output' + str(seriesNumber)
    if dst:
        nrrd.write('%s/%s.nrrd' % (dst, filename), data, header)
    else:
        nrrd.write('%s.nrrd' % (filename), data, header)

    return filename


# Remove DICOM tags that are on the exclude list
def removeDicomTags(dataset, tagsExcluded):

    # Check process child sequences
    for tag in dataset.keys():
        if type(dataset[tag].value) is pydicom.sequence.Sequence:
            for ds in dataset[tag].value:
                removeDicomTags(ds, tagsExcluded)

    # Top level
    for etag in tagsExcluded:
        if etag in dataset:
            del dataset[etag]



def addImageToList(imageList, filename, dicomList):
    # Take the first image and obtain the DICOIM tags
    try:
        dataset = pydicom.dcmread(dicomList[0], specific_tags=None)
    except pydicom.errors.InvalidDicomError:
        print("Error: Invalid DICOM file: " + path)
        return None

    # Remove DICOM groups that are on the exclude list
    for g in dicomGroupsExcluded:
        groupInt = int(g, 16)
        subdataset = dataset.group_dataset(groupInt)
        for key in subdataset.keys():
            del dataset[key]

    # Remove DICOM tags that are on the exclude list
    # removeDicomTags processes child sequences recursively
    removeDicomTags(dataset, dicomTagsExcluded)

    newDict = {}
    for key in dataset.keys():
        newDict[dataset[key].keyword] = str(dataset[key].value)

    imageList[filename] = newDict


def groupBySeriesAndExport(cur, tags, valueListDict, cond=None, filename=None, dst=None, prefix=None, imageList=None):

    if len(tags) == 0:
        cur.execute('SELECT path FROM dicom WHERE ' + cond)
        paths = cur.fetchall()
        if len(paths) == 0:
            return
        filelist = []
        for p in paths:
            filelist.append(str(p[0]))

        print('Writing ' + dst + '/' + filename)
        filenameUsed = exportNrrd(filelist, dst, filename)

        if (filenameUsed is not None) and (imageList is not None):
            addImageToList(imageList, filenameUsed, filelist)

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
            filename2 = value.replace('/', '.')
        else:
            filename2 = filename + '-' + value.replace('/', '.')
        groupBySeriesAndExport(cur, tags2, valueListDict, cond2, filename2, dst=dst, imageList=imageList)


def main(argv):

    try:
        parser = argparse.ArgumentParser(description="Split DICOM series by Tag.")
        parser.add_argument('tags', metavar='TAG', type=str, nargs='+',
                            help='DICOM tags(e.g. "0020,000E")')
        parser.add_argument('src', metavar='SRC_DIR', type=str, nargs=1,
                            help='source directory')
        parser.add_argument('dst', metavar='DST_DIR', type=str, nargs=1,
                            help='destination directory')
        parser.add_argument('-r', dest='recursive', action='store_const',
                            const=True, default=False,
                            help='search the source directory recursively')
        parser.add_argument('-l', dest='imagelist', action='store_const',
                            const=True, default=False,
                            help='generate a image list with DICOM parameters.')
        args = parser.parse_args(argv)

    except Exception as e:
        print(e)

    tags   = args.tags
    srcdir = args.src[0]
    dstdir = args.dst[0]

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

    os.makedirs(dstdir, exist_ok=True)

    d = {}
    groupBySeriesAndExport(cur, tags, valueListDict, cond=None, filename=None, dst=dstdir, imageList=d)

    with open(dstdir+'/'+'tags.json', 'w', encoding='utf8') as json_file:
        json.dump(d, json_file, ensure_ascii=False)



if __name__ == "__main__":
    main(sys.argv[1:])
