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

# From http://www.cookbook-r.com/Graphs/Plotting_means_and_error_bars_(ggplot2)/
source("r_cookBook_helper_fns.R")

# ------------------------------------------------ #
setwd("~/Google Drive/Programming Projects/ZeitSci/analysis/R")
setwd(paste0(MAIN_FOLDER(), "R"))

# Read in Data
df <- read.csv("funding_data.csv", na.strings=c("","NA", "NAN", 'nan', 'NaN'))

# Strange
df <- df[df$Grant > 0 & df$GrantYear <= 2015, ]

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

df_plotting <- df[!(is.na(df$Grant)),]

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

# Data on ~ 56% of Entries in the Database
nrow(df[!(is.na(df$InstitutionType)),]) / nrow(df[(is.na(df$InstitutionType)),])
# ---------------------------

# Over time -- From 2007 and on because of Small N in 2000-2007
agg_inst <- data.frame(aggregate(round(Grant, 2) ~ GrantYear + InstitutionType
                                 , data = df[df$GrantYear > 2007,]
                                 , FUN = function(x){c(m = median(x), c = length(x))}))
colnames(agg_inst) <- c('Year', 'InstitutionType', 'Grant')
agg_inst$metric <- data.frame(agg_inst$Grant)$m
agg_inst$count <- data.frame(agg_inst$Grant)$c
agg_inst <- data.frame(subset(agg_inst, select = -Grant))
agg_inst$prop <- apply(agg_inst[, c('Year', 'count')], 1, FUN = function(x){
    prop <- x[[2]]/sum(agg_inst$count[agg_inst$Year == x[[1]]])
    return(prop)
})

agg_inst$weighted_median <- agg_inst$metric * agg_inst$prop

ggplot(agg_inst, aes(x = Year, y = metric, fill = InstitutionType, color = InstitutionType)) +
    geom_bar(stat = "identity", position = 'dodge', alpha = 0.85) + 
    scale_y_continuous(expand = c(0,0)) +
    scale_x_continuous(breaks = seq(min(agg_inst$Year), max(agg_inst$Year)), expand = c(0,0))

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


















































