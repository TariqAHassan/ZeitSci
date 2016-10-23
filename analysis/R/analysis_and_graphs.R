# ----------------------------------------------------------------------- #
# Science Funding Analysis                       
# ----------------------------------------------------------------------- #

# Import Modules
library('ez')
library('lme4')
library('ggvis')
library('cowplot')
library('ggplot2')
library('scales')
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

# From http://www.cookbook-r.com/Graphs/Plotting_means_and_error_bars_(ggplot2)/
source("r_cookBook_helper_fns.R")

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

# ------------------------------------------------ #
# Linear Mixed Effects Model of Grants
# ------------------------------------------------ #

# DataFrame For Model Building
df_m <- df[!(is.na(df$InstitutionType)) & !(is.na(df$OrganizationBlock)) & !(is.na(df$Endowment)), ]

# Convert to Factor
df_m$InstitutionType <- as.factor(df_m$InstitutionType)
df_m$OrganizationBlock <- as.factor(df_m$OrganizationBlock)


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
# Plots - Exploratory
# --------------------------------------------------------

df_plotting <- df[!(is.na(df$Grant)) & (df$GrantYear < 2016),]

# Grant Density

ggplot(df_plotting, aes(Grant)) +
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

# ---------------------------
# Break on Public Vs. Private
# ---------------------------

# Time Series
agg_inst <- data.frame(aggregate(round(Grant, 2) ~ GrantYear + InstitutionType, data = df, FUN = 'sum'))
colnames(agg_inst) <- c('Year', 'InstitutionType', 'Grant')

ggplot(agg_inst, aes(x = Year, y = Grant, color = InstitutionType)) +
    geom_point(alpha = 0.75, size = 3.5) + 
    scale_x_continuous(limits = c(2000, 2015)) +
    scale_y_continuous(limits=c(0, 8000000000), breaks = seq(0, 8000000000, 2000000000)) 

# ---------------------------
# Break on Block
# ---------------------------

agg_block <- data.frame(aggregate(round(Grant, 2) ~ GrantYear + OrganizationBlock
                                  , data = df[df$GrantYear >= 2010 & df$GrantYear < 2016,]
                                  , FUN = 'sum'))
colnames(agg_block) <- c('Year', 'OrganizationBlock', 'Grant')

# Define Scaling Information
scalar <- 10^(floor(log10(max(agg_block$Grant))) - 1) 
breaks = seq(0, max(agg_block$Grant), length.out = 6)

# see: # http://stackoverflow.com/a/28160040/4898004
formatted_labels <- format(round(breaks / scalar), trim = TRUE) 

ggplot(agg_block, aes(x = factor(Year), y = Grant, fill = OrganizationBlock)) +
    geom_bar(stat = "identity", position = 'dodge', alpha = 0.85) + 
    ylab("Grants (Billions of USD)") +
    labs(fill = "Funding Block") + 
    scale_y_continuous(breaks = breaks, labels = formatted_labels, expand = c(0,0)) +
    scale_x_discrete(expand = c(0,0))

# Mean
agg_block_mean <- data.frame(aggregate(round(Grant, 2) ~ GrantYear + OrganizationBlock
                                  , data = df[df$GrantYear >= 2010 & df$GrantYear < 2016,]
                                  , FUN = 'mean'))
colnames(agg_block_mean) <- c('Year', 'OrganizationBlock', 'Grant')


# Compute CIs for the data
agg_block_mean_cis <- summarySEwithin(df_plotting, measurevar="Grant", withinvars="GrantYear",
                                      idvar="OrganizationBlock", na.rm=FALSE, conf.interval=.95)

ggplot(agg_block_mean, aes(x = factor(Year), y = Grant, fill = OrganizationBlock)) +
    geom_bar(stat = "identity", position = 'dodge', alpha = 0.85) + 
    ylab("Grants (Billions of USD)") +
    labs(fill = "Funding Block") + 
    scale_y_continuous(breaks = breaks, labels = formatted_labels, expand = c(0,0)) +
    scale_x_discrete(expand = c(0,0)) + 
    geom_errorbar(aes(ymin=len-ci, ymax=len+ci),
                  width=.2,                    # Width of the error bars
                  position=position_dodge(.9))

















































