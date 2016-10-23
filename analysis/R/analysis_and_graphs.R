# ----------------------------------------------------------------------- #
# Science Funding Analysis                       
# ----------------------------------------------------------------------- #

# Import Modules
library('ez')
library('lme4')
library('ggvis')
library('cowplot')
library('ggplot2')
library('reshape2')
source("data_sources.R")
options(scipen=5)


# ------------------------------------------------ #

resid_analysis <- function(data_frame, model){
    # Note: can be tempermental if lmerTest loaded.
    model_resids <- data_frame
    model_resids <- data.frame(Researcher = model_resids[,c("Researcher")])
    model_resids$resids <- Reduce(c, residuals(model))
    
    # Make Residuals Positive
    counter = 0
    while (-1 %in% sign(model_resids$resids)) {
        model_resids$resids <- model_resids$resids + 1
        counter <- counter + 1
    }
    print(paste("A value of", counter, "was added to the residuals"))
    
    # Base R Plot Settings
    par(mfrow = c(1,3))
    
    # 1. qq-Plot
    qqp(residuals(model), "norm")
    
    # 2. Boxcox
    bc  <- with(model_resids, boxcox(resids ~ id)) 
    bcl <- bc$x[bc$y == max(bc$y)]
    print(paste("lambda = ", round(bcl,4)))
    
    # 3. Hist
    hist(model_resids$resids, breaks = 40)
    par(mfrow = c(1,1))
}

# ------------------------------------------------ #

# Import
setwd(paste0(MAIN_FOLDER(), "R"))

# Read in Data
df <- read.csv("funding_data.csv", na.strings=c("","NA", "NAN", 'nan', 'NaN'))

# Strange
df <- df[df$Grant > 0, ]

# Conversions
df['Grant'] <- as.numeric(df$Grant)
df['Endowment'] <- as.numeric(df$Endowment)

# DataFrame For Model Building
df_m <- df[!(is.na(df$InstitutionType)) & !(is.na(df$OrganizationBlock)) & !(is.na(df$Endowment)), ]

# Convert to Factor
df_m$InstitutionType <- as.factor(df_m$InstitutionType)
df_m$OrganizationBlock <- as.factor(df_m$OrganizationBlock)

# ------------------------------------------------ #
# Linear Mixed Effects Model of Grants
# ------------------------------------------------ #

# Summary
agg = data.frame(aggregate(round(Grant, 2) ~ GrantYear, data = df, FUN = 'sum'))
colnames(agg) <- c('Year', 'Grant')

# Construct a General Model 
m <- lmer(Grant ~ GrantYear + OrganizationBlock + InstitutionType + (1|Researcher),
           data = df_m,
           REML = FALSE)

# Execute a drop1() on the Model.
# Precondition prior to computing this model: AIC will be used to guide model selection.
drop1(m, test = "Chisq")

# Plot Residuals
hist(residuals(m), breaks=10)

# Get Summary
AIC(m)
summary(m)

# --------------------------------------------------------
# Plots
# --------------------------------------------------------

# Grant Density

ggplot(df[!(is.na(df$Grant)),], aes(Grant)) +
    geom_density(aes(fill = OrganizationBlock, color = OrganizationBlock), alpha = 0.25, na.rm=TRUE) +
    scale_x_continuous(limits=c(0, 750000), breaks = seq(0, 750000, 150000), expand = c(0, 0)) +
    scale_y_continuous(limits=c(0, 0.00005), expand = c(0, 0)) +
    ylab("Density") +
    xlab("Grants in Real USD (2015)") +
    labs(color = "Funding Block", fill = "Funding Block") + 
    theme_bw() +
    theme(
          axis.line = element_line(colour = "black"),
          panel.grid.major = element_blank(),
          panel.border = element_blank(),
          axis.ticks=element_blank(),
          panel.background = element_blank()
    ) 

#






























































