# ----------------------------------------------------------------------- #
# Science Funding Analysis                       
# ----------------------------------------------------------------------- #

# Import Modules
library('ez')
library('ggplot2')
library('reshape2')

# ------------------------------------------------ #

# Import
setwd("~/Google Drive/Programming Projects/ZeitSci/analysis/R")

# Read in Data
df <- read.csv("funding_data.csv")

# Conversions
df['Grant'] <- as.numeric(unlist(df['Grant']))
df$OrganizationBlock <- as.character(df$OrganizationBlock)

agg = data.frame(aggregate(Grant ~ Year, data = df, FUN = 'mean'))


































































































