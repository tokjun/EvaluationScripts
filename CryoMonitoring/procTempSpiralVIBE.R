library(ggplot2)
library(reshape2)
library(signal)

loadTempData <- function(path, startTimeStr) {
#    
#  Load temperature data and calculate time offset from the start time
#  The format of input temperature data should follow the following example:
#
#  Sample Number,Date/Time,CHANNEL0,CHANNEL1,CHANNEL2,CHANNEL3,CHANNEL4,Events
#  1,08/24/2018 10:28:29.256 AM, 20.2088, 20.1857, 20.5672, 20.0585, 20.3742
#  2,08/24/2018 10:28:29.756 AM, 20.3169, 20.3285, 20.4788, 19.8428, 20.3857
#
#  Ex)
#    tempData <- loadTempData('/Users/junichi/Projects/UTE/UTE-Phantom/IRUTE-Test-2018-08-24/temp-2018-08-24.csv', "8/24/2018  11:38:29 AM")

    tempData <- read.csv(path, sep=",")
    
    startTime <- strptime(startTimeStr, "%m/%d/%Y %I:%M:%OS %p")
    tempData$Time <- as.numeric(strptime(tempData$Date.Time, "%m/%d/%Y %I:%M:%OS %p") - startTime, units="secs")

    columns <- c("Time", "CHANNEL0", "CHANNEL1", "CHANNEL2", "CHANNEL3", "CHANNEL4")
    tempData <- tempData[,columns]
    tempData <- tempData[!is.na(tempData$Time),]

    return(tempData)
}

plotTempData <- function(tempData) {

    tempData <- melt(data=tempData, id.vars="Time", measure.vars=c("CHANNEL0", "CHANNEL1", "CHANNEL2", "CHANNEL3", "CHANNEL4"), value.name="Temperature", variable.name="Channel")
    
    ggplot(data=tempData, aes(x=Time, y=Temperature, group=Channel)) + ggtitle("Temperature") + labs(x="Time (s)", y="Temperature (DegC)") + geom_line() + geom_point(aes(color=factor(Channel))) + scale_color_discrete(name ="Channels",labels=c("Channel 0", "Channel 1", "Channel 2", "Channel 3", "Channel 4"))
}

plotTempDataFiltered <- function(tempData) {

    tempData <- melt(data=tempData, id.vars="Time", measure.vars=c("CHANNEL0", "CHANNEL1", "CHANNEL2", "CHANNEL3", "CHANNEL4", "CHANNEL0F", "CHANNEL1F", "CHANNEL2F", "CHANNEL3F", "CHANNEL4F"), value.name="Temperature", variable.name="Channel")
    
    ggplot(data=tempData, aes(x=Time, y=Temperature, group=Channel)) + ggtitle("Temperature") + labs(x="Time (s)", y="Temperature (DegC)") + geom_line() + geom_point(aes(color=factor(Channel))) + scale_color_discrete(name ="Channels",labels=c("Channel 0", "Channel 1", "Channel 2", "Channel 3", "Channel 4", "Channel 0F", "Channel 1F", "Channel 2F", "Channel 3F", "Channel 4F"))
}


filterTempData <- function(tempData) {

    bf <- butter(2, 0.002, type="low")
    gpd <- grpdelay(bf)
    delay <- gpd$gd[1]   # delay for freq = 0

    print(sprintf("filterTempData(): Applying delay of %f frames.", delay))
    CHANNEL0F <- filter(bf, tempData$CHANNEL0)
    CHANNEL1F <- filter(bf, tempData$CHANNEL1)
    CHANNEL2F <- filter(bf, tempData$CHANNEL2)
    CHANNEL3F <- filter(bf, tempData$CHANNEL3)
    CHANNEL4F <- filter(bf, tempData$CHANNEL4)

    tempData$CHANNEL0F <- c(CHANNEL0F[delay:length(tempData$CHANNEL0)], numeric(delay))
    tempData$CHANNEL1F <- c(CHANNEL1F[delay:length(tempData$CHANNEL1)], numeric(delay))
    tempData$CHANNEL2F <- c(CHANNEL2F[delay:length(tempData$CHANNEL2)], numeric(delay))
    tempData$CHANNEL3F <- c(CHANNEL3F[delay:length(tempData$CHANNEL3)], numeric(delay))
    tempData$CHANNEL4F <- c(CHANNEL4F[delay:length(tempData$CHANNEL4)], numeric(delay))

    #points(x, b, col="black", pch=20)
    #
    #bf <- butter(2, 1/25, type="high")
    #b <- filter(bf, y+noise1)
    #points(x, b, col="black", pch=20)
    return(tempData)
}


loadImageList <- function(path) {
#    
#  Load timestamp extracted from the DICOM headers.
#  The script aggregate the data by series and take the earliest timestamp (= time to start acquisition of the series)
#  as the representative timestamp for the series.
#
#  The format of input image list should follow the following example:
#
#  Study,Series,Description,Timestamp
#  1,1,LOCALIZER,105314.770000
#  1,1,LOCALIZER,105316.775000
#  1,1,LOCALIZER,105318.780000
#  1,1,LOCALIZER,105320.785000
#
    imageData <- read.csv(path)
    imageData <- aggregate(imageData[, c("Timestamp")], imageData[,c("Study", "Series","Description")], min)
    names(imageData) <- c("Study", "Series", "Description", "Timestamp")

    return(imageData)
}

adjustImageListTimestampBySeries <- function(imageData, firstStudy, firstSeries) {
    
    # Look up the time stamp for the first image
    firstImage <- imageData[imageData$Study==firstStudy & imageData$Series==firstSeries,]
    baseTimestamp <- firstImage$Timestamp
    imageData$Timestamp <- strptime(imageData$Timestamp, "%H%M%OS") - strptime(baseTimestamp, "%H%M%OS")
    imageData <- imageData[!is.na(imageData$Timestamp),]
    imageData$Timestamp <- as.numeric(imageData$Timestamp, units="secs")

    r <- list("imageData"=imageData, "baseTimestamp"=baseTimestamp)
    return(r)
}

adjustImageListTimestampByTimestamp <- function(imageData, baseTimestamp) {
    
    # Look up the time stamp for the first image
    imageData$Timestamp <- strptime(imageData$Timestamp, "%H%M%OS") - strptime(baseTimestamp, "%H%M%OS")
    imageData <- imageData[!is.na(imageData$Timestamp),]
    imageData$Timestamp <- as.numeric(imageData$Timestamp, units="secs")
    
    return(imageData)
}


calcRefTempPerImage <- function(imageData, tempData, duration) {
    
    # Calculate reference temperature by averaging the probe temperatures during the image acquisition

    Temp0 <- numeric(nrow(imageData))
    Temp1 <- numeric(nrow(imageData))
    Temp2 <- numeric(nrow(imageData))
    Temp3 <- numeric(nrow(imageData))
    Temp4 <- numeric(nrow(imageData))

    for (row in 1:nrow(imageData)) {
        tstart <- imageData[row, "Timestamp"]
        tend <- tstart + duration
        td <- tempData[tempData$Time >= tstart & tempData$Time < tend,]
        ## NOTE: Filtered temperature data are used
        Temp0[row] <- mean(td$CHANNEL0F)
        Temp1[row] <- mean(td$CHANNEL1F)
        Temp2[row] <- mean(td$CHANNEL2F)
        Temp3[row] <- mean(td$CHANNEL3F)
        Temp4[row] <- mean(td$CHANNEL4F)
        
    }

    imageData$Temp0 <- Temp0
    imageData$Temp1 <- Temp1
    imageData$Temp2 <- Temp2
    imageData$Temp3 <- Temp3
    imageData$Temp4 <- Temp4

    return(imageData)
}


reformatImageTempData <- function(data, nChannel=0) {

    # Reformat image-temperature table.
    # In the reformatted table, each line show one temperature from a probe
    # Channel of the probe is 1-N instead of 0-(N-1). This corresponds to the indecies
    # in the label map

    if (nChannel == 0) {
        nChannel <- ncol(data)-4
    }

    cnames <- c()
    for (col in 1:nChannel) {
        name <- sprintf("Temp%d", col-1)
        cnames <- c(cnames, name)
    }
    
    data <- melt(data=data, id.vars=c("Study", "Series", "Description", "Timestamp"), measure.vars=cnames, value.name="Temperature", variable.name="Channel")
    levels(data$Channel) <- 1:nChannel

    data <- data[order(data$Timestamp),]
}
    

mergeTempIntensity <- function(imageTempData, intensityData) {

    # Use the same column names as imageTempData
    colnames(intensityData) <- c("Image",  "Series", "Channel",  "Count",  "Min",    "Max",    "Mean",   "StdDev")
    result <- merge(intensityData, imageTempData)
    result <- result[,c("Study", "Series", "Timestamp", "Channel", "Image", "Min", "Max", "Mean", "StdDev", "Temperature")]
    return (result)
}
    

    
interpTempForLabel <- function(imageTempData, probePosition, labelPosition, posSign=-1.0) {

    for (row in 1:nrow(imageTempData)) {
        temperature <- imageTempData[row, 5:9]
        probeTemp <- data.frame("temperature"=t(temperature)[,], "position"=(posSign * probePosition$position))
        if (! any(is.nan(probeTemp$temperature))) {
            fit <- nls(temperature ~ SSasymp(position, yf, y0, log_alpha), data = probeTemp)    
            newData <- data.frame("position" = labelPosition$position)
            newData$temperature <- predict(fit, newData)
            for (col in 1:length(newData$temperature)) {
                colname <- sprintf("Temp%d", col-1)
                imageTempData[row, colname] <- newData$temperature[col]
            }
        }
    }
    imageTempDataNew <- imageTempData[!is.nan(imageTempData$Temp0), ]
    return(imageTempDataNew)
}


interpTempForLabelLM <- function(imageTempData, probePosition, labelPosition, tempIndex=5:9, posSign=-1.0) {

    for (row in 1:nrow(imageTempData)) {
        temperature <- imageTempData[row, tempIndex]
        probeTemp <- data.frame("temperature"=t(temperature)[,], "position"=(posSign * probePosition$position))
        if (! any(is.nan(probeTemp$temperature))) {
            fit <- lm(temperature ~ position, data = probeTemp)
            #fit <- nls(temperature ~ SSasymp(position, yf, y0, log_alpha), data = probeTemp)    
            newData <- data.frame("position" = labelPosition$position)
            newData$temperature <- predict(fit, newData)
            for (col in 1:length(newData$temperature)) {
                colname <- sprintf("Temp%d", col-1)
                imageTempData[row, colname] <- newData$temperature[col]
            }
        }
    }
    imageTempDataNew <- imageTempData[!is.nan(imageTempData$Temp0), ]
    return(imageTempDataNew)
}
