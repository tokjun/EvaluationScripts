library(ggplot2)
library(reshape2)

loadTempData <- function(path, startTime) {
    
    tempData <- read.csv(path)
    str <- lapply(tempData$Date.Time, as.character)
    #startTime <- strptime(str[[1]], "%d/%m/%Y %I:%M:%OS %p")
    
    n <- length(str)
    t <- c()
    for (i in 1:n) {
        currentTime <- strptime(str[[i]], "%d/%m/%Y %I:%M:%OS %p")
        diffTime <- difftime(currentTime, startTime, units="secs")
        t <- append(t, diffTime[[1]])
    }
    
    tempData$Time <- t
    columns <- c("Time", "CHANNEL0", "CHANNEL1", "CHANNEL2", "CHANNEL3", "CHANNEL4")
    tempData <- tempData[,columns]
    
    return(tempData)
}


loadImageValueData <- function(path, firstImageIndex) {
    
    imageValue <- read.csv(path)
    lastImageIndex <- length(imageValue$Time)
    imageTimeOffset <- imageValue$Time[firstImageIndex]
    imageValue$Time <- imageValue$Time - imageTimeOffset
    
    return (imageValue)
}


loadTempAndImageValue <- function(dir, imageValueFile, tempFile, firstImageIndex, startTempTime, probeROIs) {
    
    imageValuePath <- sprintf("%s/%s", dir, imageValueFile)
    tempPath <- sprintf("%s/%s", dir, tempFile)
    
    imageValue <- loadImageValueData(imageValuePath, firstImageIndex) 
    tempData <- loadTempData(tempPath, startTempTime)

    ## The imaging start at series 14
    tlist <- imageValue$Time
    
    Probe1ImageValue <- c()
    Probe2ImageValue <- c()
    Probe3ImageValue <- c()
    Probe4ImageValue <- c()

    Probe1Temp <- c()
    Probe2Temp <- c()
    Probe3Temp <- c()
    Probe4Temp <- c()
    Probe5Temp <- c()
    
    Time <- c()
    
    for (idx in 1:length(tlist)) {
        t <- tlist[idx]
        mask <- (abs(tempData$Time - t) < 0.25)
        if ((t > 0.0) && (length(tlist[mask]) == 1)) {
            Time <- append(Time, t)
            Probe1Temp <- append(Probe1Temp, tempData$CHANNEL0[mask])
            Probe2Temp <- append(Probe2Temp, tempData$CHANNEL1[mask])
            Probe3Temp <- append(Probe3Temp, tempData$CHANNEL2[mask])
            Probe4Temp <- append(Probe4Temp, tempData$CHANNEL3[mask])
            Probe5Temp <- append(Probe5Temp, tempData$CHANNEL4[mask])
            col <- sprintf("X%d", probeROIs[1])
            Probe1ImageValue <- append(Probe1ImageValue, imageValue[idx, col])
            col <- sprintf("X%d", probeROIs[2])
            Probe2ImageValue <- append(Probe2ImageValue, imageValue[idx, col])
            col <- sprintf("X%d", probeROIs[3])
            Probe3ImageValue <- append(Probe3ImageValue, imageValue[idx, col])
            col <- sprintf("X%d", probeROIs[4])
            Probe4ImageValue <- append(Probe4ImageValue, imageValue[idx, col])
        }
    }
    result <- data.frame(Time, Probe1ImageValue, Probe2ImageValue, Probe3ImageValue, Probe4ImageValue, Probe1Temp, Probe2Temp, Probe3Temp, Probe4Temp, Probe5Temp)

    return(result)
}

meltImageValue <- function(TempImageValue) {
    
    ImageValue <- data.frame(TempImageValue["Time"],
                             TempImageValue["Probe1ImageValue"],
                             TempImageValue["Probe2ImageValue"],
                             TempImageValue["Probe3ImageValue"],
                             TempImageValue["Probe4ImageValue"])
    meltedImageValue <- melt(ImageValue, id.vars="Time")
    
    return(meltedImageValue)
}

meltTemp <- function(TempImageValue) {
    
    Temp <- data.frame(TempImageValue["Time"],
                       TempImageValue["Probe1Temp"],
                       TempImageValue["Probe2Temp"],
                       TempImageValue["Probe3Temp"],
                       TempImageValue["Probe4Temp"])
    meltedTemp <- melt(Temp, id.vars="Time")
    
    return(meltedTemp)
}

nlm_eqn <- function(df, f) {
    m <- nlm(f, df)
    eq <- substitute(italic(y) == b %.% italic(x)+a*","~~italic(r)^2~"="~r2, 
                     list(a = format(coef(m)[1], digits = 2), 
                          b = format(coef(m)[2], digits = 2), 
                          r2 = format(summary(m)$r.squared, digits = 3)))
    as.character(as.expression(eq))
}

lm_eqn <- function(df, f) {
    m <- lm(f, df)
    eq <- substitute(italic(y) == b %.% italic(x)+a*","~~italic(r)^2~"="~r2, 
                     list(a = format(coef(m)[1], digits = 2), 
                          b = format(coef(m)[2], digits = 2), 
                          r2 = format(summary(m)$r.squared, digits = 3)))
    as.character(as.expression(eq))
    
}

plotImageParameterVsTemperature <- function(path, sampledImageFile, tempFile, timeOffset, probeROIs, paramName="R2*", paramFileStr="R2s", paramUnit="s^-1", fitting="linear") {
    
    TempImageValue <- loadTempAndImageValue(path, sampledImageFile, tempFile, 3, timeOffset, probeROIs)

    meltedImageValue <- meltImageValue(TempImageValue)
    meltedTemp <- meltTemp(TempImageValue)
    meltedData <- data.frame(Time=meltedImageValue$Time, Temp=meltedTemp$value, imageParam=meltedImageValue$value, Probe=meltedTemp$variable)

    ## Plot: Temperature
    ggplot(data=meltedData, aes(x=Time, y=Temp, group=Probe)) + ggtitle("Temperature") + labs(x="Time (s)", y="Temperature (DegC)") + geom_line() + geom_point(aes(color=factor(Probe))) + scale_color_discrete(name ="Probes",labels=c("Probe 1", "Probe 2", "Probe 3", "Probe 4"))
    ggsave(file=sprintf("Plot-Temp-%s.pdf", tempFile))

    meltedData <-data.frame(meltedData, Pos=0.0)
    meltedData$Pos[meltedData$Probe=="Probe1Temp"] = 1.9
    meltedData$Pos[meltedData$Probe=="Probe2Temp"] = 12.8
    meltedData$Pos[meltedData$Probe=="Probe3Temp"] = 31.5
    meltedData$Pos[meltedData$Probe=="Probe4Temp"] = 45.9

    ggplot(data=meltedData, aes(x=Pos, y=Temp, group=Time)) + ggtitle("Position vs Temperature") + labs(x="Position (mm)", y="Temperature (DegC)") + geom_line() + geom_point()
    ggsave(file=sprintf("Plot-POS-vs-Temp-%s.pdf", tempFile))

    ggplot(data=meltedData, aes(x=Pos, y=imageParam, group=Time))+ ggtitle(sprintf("Position vs %s", paramName)) + labs(x="Position (mm)", y=sprintf("%s (%s)", paramName, paramUnit)) + geom_line() + geom_point()
    ggsave(file=sprintf("Plot-POS-vs-%s-%s.pdf", paramFileStr, tempFile))
    
    ## Temperature range
    #meltedData <- meltedData[meltedData$Temp< (-5.0),]
    #fit <- lm(meltedData$Temp ~ meltedData$imageParam)
    
    ## Plot: Temperature vs Image Parameter
    #ggplot(data=meltedData, aes(x=Temp, y=R2s, group=Probe)) + ggtitle("Temperature vs R2*") + labs(x="Temperature (DegC)", y="R2* (sec^-1)") + geom_point(aes(color=factor(Probe))) + scale_color_discrente(name ="Probes",labels=c("Probe 1", "Probe 2", "Probe 3", "Probe 4"))
    p <- ggplot(data=meltedData, aes(x=Temp, y=imageParam))
    p <- p + ggtitle(sprintf("Temperature vs %s", paramName))
    p <- p + labs(x="Temperature (DegC)", y=sprintf("%s (%s)", paramName, paramUnit))
    p <- p + geom_point(aes(shape=factor(Probe)))
    p <- p + scale_shape_discrete(name ="Probes",labels=c("Probe 1", "Probe 2", "Probe 3", "Probe 4"))
    
    if (fitting == "linear") {
        f1 <- y ~ x
        p <- p + geom_smooth(method = "lm", se=FALSE, color="black", formula=f1)
        f2 <- imageParam~Temp
        p <- p + geom_text(x = -30, y = 450, label = lm_eqn(meltedData, f2), parse = TRUE)
    } else if (fitting == "exp") {
        f1 <-y ~ a* exp(b*x) + c
        m <- nls(y ~ a* exp(b*x) + c, start=list(a=1, b=1, c=0))
        print (m)
        #p <- p + geom_smooth(method = "nls", formula=f1, se=FALSE, color="black", start=list(a=1))
        #f2 <- imageParam ~ a * exp(b * Temp)
        #p <- p + geom_text(x = -30, y = 450, label = nlm_eqn(meltedData, f2), parse = TRUE)
    }
    p
    ggsave(file=sprintf("Plot-Temp-vs-%s-%s.pdf", paramFileStr, tempFile))
}


#Series 14 started at 11:43:28.227500 on the scanner -> 11:44:01 on the DAQ
#path <- "/Users/junichi/Dropbox/Experiments/UTE/Cryo-2016-02-12"
path <- "/home/develop/Projects/Dropbox/Experiments/UTE/Cryo-2016-02-12"

timeOffset <- "2016-12-02 11:44:01 EST"
tempFile <- "Temp-freeze.csv"
#tempFile <- "Temp-thaw.csv"

# Probe 1 = ROI 1; Probe 2 = ROI 6; Probe 3 = ROI 14; Probe 4 = ROI 20
#probeROIs <- c(2, 7, 14, 20)
probeROIs <- c(2, 7, 13, 19)

plotImageParameterVsTemperature(path, "roi-r2s.csv", tempFile, timeOffset, probeROIs)
#plotImageParameterVsTemperature(path, "roi-norm-intensity.csv", tempFile, timeOffset, probeROIs, paramName="Normalized Intensity", paramFileStr="NormIntensity", paramUnit="--", fitting="exp")
    



