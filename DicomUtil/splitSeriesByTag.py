import argparse, sys, shutil, os, logging
#import qt, ctk, slicer
import tempfile
import sqlite3
import pydicom
#import DICOMLib
#from DICOMLib.DICOMUtils import TemporaryDICOMDatabase
#from slicer.ScriptedLoadableModule import *

#  Usage:
#
#  $ /path/to/Slicer  --launch PythonSlicer --no-main-window --no-splash --python-script splitSeriesByTag.py -- -i DSC-DICOM -o DSC-mpReview
#
#  Dependencies:
#  This script calls functions in dicom_separate_by_tag.py. Make sure to include the path
#  to the script in the PYTHONPATH environment variable.
#
# DICOM Tags:
# - General
#  - (0008,103e) : SeriesDescription
#  - (0010,0010) : PatientsName
#  - (0020,0010) : StudyID
#  - (0020,0011) : SeriesNumber
#  - (0020,0037) : ImageOrientationPatient
#  - (0008,0032) : AcquisitionTime
#
# - Siemens MR Header
#  - (0051,100f) : Coil element (Siemens)
#  - (0051,1016) : Real/Imaginal (e.x. "R/DIS2D": real; "P/DIS2D": phase)


#
# Match DICOM attriburtes
#
def getDICOMAttribute(con, path, tags):

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


def concatColNames(tags):

    r = ''
    for tag in tags:
        key = tag.replace(',', '')
        if r == '':
            r = 'x' + key + ' text'
        else:
            r = r + ',' + 'x' + key + ' text'
    return r;
    

def buildFilePathDBByTags(con, srcDir, tags, fRecursive=True):

    # Create a table
    print('CREATE TABLE dicom (' + concatColNames(tags) + 'path text)')    
    con.execute('CREATE TABLE dicom (' + concatColNames(tags) + ',path text)')

    filePathList = []
    postfix = 0
    attrList = []
    
    print("Processing directory: %s..." % srcDir)
    
    for root, dirs, files in os.walk(srcDir):
        for file in files:
            srcFilePath = os.path.join(root, file)
            insertStr = getDICOMAttribute(con, srcFilePath, tags)
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


def loadByGroup(cur, tags, valueListDict, cond=None, filename=None):

    if len(tags) == 0:
        cur.execute('SELECT path FROM dicom WHERE ' + cond)
        paths = cur.fetchall()
        print (paths)
        # 
        # load files
        #
        #loadablesByPlugin, loadEnabled = DICOMLib.getLoadablesFromFileLists(fileLists)
        return

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
        loadByGroup(cur, tags2, valueListDict, cond2, filename2)

    

def convertDicomToNrrdBySubdirectory(srcdir, dstdir, tags):

    #con = sqlite3.connect(':memory:')
    con = sqlite3.connect('TestDB.db')
    cur = con.cursor()
    
    #buildFilePathDBByTags(con, srcdir, tags, True)

    # Generate a list of values for each tag
    valueListDict = {}
    for tag in tags:
        colName = 'x' + tag.replace(',', '')
        cur.execute('SELECT ' + colName + ' FROM dicom GROUP BY ' + colName)
        valueListDict[colName] = cur.fetchall()


    loadByGroup(cur, tags, valueListDict)
    


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
    args = parser.parse_args(argv)

    srcdir = args.src[0]
    dstdir = args.dst[0]

    # Make the destination directory, if it does not exists.
    #os.makedirs(dstdir[0], exist_ok=True)

    # Create a temporary directory
    #tempdir = tempfile.TemporaryDirectory()

    dirDict = {}
    
    #extractDICOMByTag(srcdir[0], tmpdir, args.tags, args.recursive, False, None, args.preserve)
    print(args.tags)
    
    convertDicomToNrrdBySubdirectory(srcdir, dstdir, args.tags)


  except Exception as e:
    print(e)
  sys.exit()

if __name__ == "__main__":
  main(sys.argv[1:])

