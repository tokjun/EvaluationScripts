#! /bin/bash

#
# This script depends on the following modules:
#
#   RegistrationMetrics module 
#     http://svn.na-mic.org/NAMICSandBox/trunk/IGTLoadableModules/RegistrationMetrics
#
#
#


Cases=(1 5 6 7 8 9 10 11 13 16 17 18 19 20 21 22 23 24 25 26)
#Cases=()

ModuleDir="lib/Slicer-4.3/cli-modules/"
SlicerPath="/Users/junichi/igtdev/slicer4/Slicer-SuperBuild-Debug/Slicer-build/"$ModuleDir
SlicerModulePath="/Users/junichi/igtdev/slicer4/Dev/"


#
# DilateAndEvaluate <outputPath> <tumorVolumeResampled> <ablationVolumeResampled> <radius>
#
function DilateAndEvaluate {

    #Dilate distance (mm)
    outputPath=$1
    tumorVolumeResampled=$2
    ablationVolumeResampled=$3
    dilateRadius=$4

    dilateFileName=`printf "tumorVolumeDilated%02d.nrrd" $dilateRadius`
    tumorVolumeDilated=$outputPath"/"$dilateFileName

    overlapFileName=`printf "overlapVolume%02d.nrrd" $dilateRadius`
    overlapVolume=$outputPath"/"$overlapFileName

    logText=$outputPath"/metricLog"$dilateRadius".txt"
    metricReturnFile=$outputPath"/metricFile"$dilateRadius".params"

    ## Dilate the tumor volume with the given margin.
    $SlicerModulePath"ErodeDilateLabel-build/"$ModuleDir"DilateLabel" --label 1 --radius $dilateRadius $tumorVolumeResampled $tumorVolumeDilated

    ## Calculate the olverlap area between the ablation volume and the dilated tumor volume (target volume)
    $SlicerPath/MaskScalarVolume --label 1 --replace 0 $ablationVolumeResampled $tumorVolumeDilated $overlapVolume

    ## Calculate metrics
    #$SlicerModulePath"RegistrationMetrics-build/"$ModuleDir"RegistrationMetrics" --returnparameterfile $metricReturnFile $tumorVolumeDilated $ablationVolumeResampled &> $logText
    $SlicerModulePath"RegistrationMetrics-build/"$ModuleDir"RegistrationMetrics" --returnparameterfile $metricReturnFile $tumorVolumeDilated $overlapVolume &> $logText
}


#
# ExtractResults <margin>
#
function ExtractResults {

    margin=$1

    inputfile=`printf "Segmentation/metricLog%d.txt" $margin`

    # Number of pixels in (dilated) tumor volume
    outputfile=`printf "output/volumeTumor%d.csv" $margin`
    echo "tumor"$margin > $outputfile
    ls |xargs -I{} grep "in Image 1" {}/$inputfile |sed -n 's/.*: //p' >> $outputfile
    
    # Number of pixels in overlapping volume
    outputfile=`printf "output/volumeOverlap%d.csv" $margin`
    echo "overlap"$margin > $outputfile
    ls |xargs -I{} grep "in Image 2" {}/$inputfile |sed -n 's/.*: //p' >> $outputfile
    
    # DSC
    outputfile=`printf "output/DSC%d.csv" $margin`
    echo "DSC"$margin > $outputfile
    ls |xargs -I{} grep "DSC" {}/$inputfile |sed -n 's/.*: //p' >> $outputfile
    
    #HD
    outputfile=`printf "output/HD%d.csv" $margin`
    echo "HD"$margin > $outputfile
    ls |xargs -I{} grep "Hausdorff" {}/$inputfile |sed -n 's/.*: //p' |sed -n 's/ mm//p' >> $outputfile
    
}


for c in ${Cases[@]}
do
    inputPath=`printf "RetrospectiveAblationMargin/Case%03d/Segmentation" $c`
    outputPath=`printf "RetrospectiveAblationMargin/Case%03d/Segmentation" $c`

    mkdir $inputPath

    tumorVolume=$inputPath"/../Output/tumor-label.nrrd"
    ablationVolume=$inputPath"/../Output/ablation-label.nrrd"

    tumorVolumeResampled=$outputPath"/tumorResampled.nrrd"
    tumorVolumeResampledTemp=$outputPath"/tumorResampled-temp.nrrd"

    ablationVolumeResampled=$outputPath"/ablationResampled.nrrd"
    ablationVolumeResampledTemp=$outputPath"/ablationResampled-temp.nrrd"

    ## log file for tumor (not dilated)
    metricReturnFileTumor=$outputPath"/metricFileTumor.params"
    logTextTumor=$outputPath"/metricLog0.txt"

    overlapFileName="overlapVolume0.nrrd"
    overlapVolume=$outputPath"/"$overlapFileName

    ## Resample the image to make the pixel size 1 mm x 1 mm x 1 mm.
    $SlicerPath/ResampleScalarVolume --spacing 1,1,1 --interpolation nearestNeighbor $tumorVolume $tumorVolumeResampledTemp
    $SlicerPath/LabelMapSmoothing --labelToSmooth -1 --numberOfIterations 50 --maxRMSError 0.1 --gaussianSigma 1.5 $tumorVolumeResampledTemp $tumorVolumeResampled

    $SlicerPath/ResampleScalarVolume --spacing 1,1,1 --interpolation nearestNeighbor $ablationVolume $ablationVolumeResampledTemp
    $SlicerPath/LabelMapSmoothing --labelToSmooth -1 --numberOfIterations 50 --maxRMSError 0.1 --gaussianSigma 1.5 $ablationVolumeResampledTemp $ablationVolumeResampled

    ## Calculate the olverlap area between the ablation volume and the dilated tumor volume (target volume)
    $SlicerPath/MaskScalarVolume --label 1 --replace 0 $ablationVolumeResampled $tumorVolumeResampled $overlapVolume
    
    ## Without margin
    $SlicerModulePath"RegistrationMetrics-build/"$ModuleDir"RegistrationMetrics" --returnparameterfile $metricReturnFileTumor $tumorVolumeResampled $overlapVolume &> $logTextTumor

    #for m in {1..10}
    #do
    #	## $m mm margin
    #	DilateAndEvaluate $outputPath $tumorVolumeResampled $ablationVolumeResampled $m
    #done

done


cd RetrospectiveAblationMargin
mkdir output

# Number of pixels in ablation volume
echo "ablation" > output/volumeAblation.csv
ls |xargs -I{} grep "in Image 2" {}/Segmentation/metricLog0.txt |sed -n 's/.*: //p' >> output/volumeAblation.csv

# Extract results from the output files
for m in {0..10}
do
    ## $m mm margin
    ExtractResults $m
done

cd ..

