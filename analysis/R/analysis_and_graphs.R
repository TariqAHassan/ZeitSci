# ----------------------------------------------------------------------- #
# Science Funding Analysis                       
# ----------------------------------------------------------------------- #

# Import Modules
library('ez')
library('lme4')
library('plyr')
library('ggvis')
library('plotly')
library('pbapply')
library('ggplot2')
library('stringr')
library('reshape2')
library('gridExtra')
options(scipen=10)

# Set seed
set.seed(100)

# ------------------------------------------------ 
# General Use Functions
# ------------------------------------------------ 

random_df_rows <- function(data_frame, percent){
    row_numb <- round(nrow(data_frame) * (percent/100))
    subsection <- data_frame[sample(nrow(data_frame), row_numb),]
    return(subsection)
}

# Define a permutation test
permutation_test <- function(vector_a, vector_b, rep_num=250, func=mean){
    #' @param vector_a: subsection 1
    #' @param vector_b: subsection 2
    #' @param rep_num: number of replications
    #' @param func: descriptive stat
    
    # Get the means
    vector_a_mean <- mean(vector_a) 
    vector_b_mean <- mean(vector_b)
    
    # Compute the mean difference
    mean_diff <- vector_b_mean - vector_a_mean
    
    # Combine
    both_types <- c(vector_a, vector_b)
    
    # Replicate
    rand_test <- pbreplicate(rep_num, sample(x = both_types))
    
    # Break
    vector_a_random <- rand_test[1:length(vector_a),]
    vector_b_random <- rand_test[(length(vector_a)+1):nrow(rand_test),]
    
    # Compute the differences
    mean_diff_vector <- pbapply(X = vector_a_random, MARGIN = 2, FUN = func) - pbapply(X = vector_b_random, MARGIN = 2, FUN = func)
    
    # Compute a p-value
    p <- (sum(abs(mean_diff_vector) >= mean_diff)) / rep_num
    
    return(list(p, mean_diff, mean_diff_vector))
}

# Test
# permutation_test(rnorm(100000), rnorm(100000))[[1]] # 1

# ------------------------------------------------ #
setwd("~/Google Drive/Programming Projects/ZeitSci/analysis/R")

# Read in Data
df <- read.csv("funding_data.csv", na.strings=c("","NA", "NAN", 'nan', 'NaN'))

# Strange
df <- df[df$GrantYear >= 2000 & df$GrantYear <= 2015,]
df <- df[df$NormalizedAmount > 0,]

# Conversions
df['Grant'] <- as.numeric(df$Grant)
df['Endowment'] <- as.numeric(df$Endowment)

# ------------------------------------------------------------------------------------------------------------
# Break on Public vs. Private
# ------------------------------------------------------------------------------------------------------------

public <- df$NormalizedAmount[df['InstitutionType'] == "Public"]
private <- df$NormalizedAmount[df['InstitutionType'] == "Private"]

# Drop NAs
public <- public[!is.na(public)]
private <- private[!is.na(private)]

# Check Dist of Public
qqnorm(public); qqline(public)
hist(public, xlim = c(0, 1000000), breaks = 100000)

# Check Dist of Private
qqnorm(private); qqline(private)
hist(private, xlim = c(0, 1000000), breaks = 50000)

# Absolutely not normal.
# Try using log data (i.e., the natural logarithm) to correct for this seemingly expoential dist.

qqnorm(log(public)); qqline(log(public))
qqnorm(log(private)); qqline(log(private))

# Better, but the tails are still off here. 

# --------------------------------------------------
# Permutation Test for Institution Type
# --------------------------------------------------

# Abandon t-test and use a nonparametric method: the randomization test.
# Are these two groups different w.r.t. the amount of funding they receive on average?

# Set alpha level
alpha_value = 0.025

# Run a permutation test
per_test_institution_type <- permutation_test(public, private)

# Plot
hist(per_test_institution_type[[3]], breaks = 50)
abline(v=per_test_institution_type[[2]], col = "red") # the bar is so far to the right it doesn't even show up...

p <- per_test_institution_type[[1]]

p < alpha_value # TRUE
# Fail to reject H0

# ---------------------------
# Violin Plot
# ---------------------------

df_violinplot <- df[!(is.na(df$InstitutionType)),]

# funding_violins_block("Canada", 95)
# funding_violins_block("United States", 95)
# funding_violins_block("Europe", 95)

vector_quant <- function(num_vector, q){
    #' @parm num_vector: vector of numerics
    #' @parm q: quantile (0-100)
    quant <- Reduce(c, quantile(num_vector, probs = c(q/100))[paste0(q, "%")])
    return(quant)
}

funding_violins_general <- function(data_frame, q, title="", x_label="", y_label="", scale_by=10^6){
    #' @parm block: funding block in the dataset
    #' @parm q: quantile (0-100)
    quant <- vector_quant(data_frame$NormalizedAmount, q); print(paste0(q, "% quantile: ", round(quant, 2)))
    plotting_data <- data_frame[data_frame$NormalizedAmount <= quant,]
    plotting_data$NormalizedAmount <- plotting_data$NormalizedAmount/(scale_by)
    graph <- ggplot(plotting_data, aes(x = InstitutionType, y = NormalizedAmount, fill = InstitutionType)) +
        geom_violin() +
        xlab(x_label) +
        ylab(y_label) +
        theme_minimal() +
        scale_fill_manual(values=c("#a157db", "#5770db")) + 
        stat_summary(fun.y=mean
                     , geom='point'
                     , colour = "#333333"
                     , size = 3
                     , position = position_dodge(width = 0.9)) +
        theme(
            legend.position="none",
            panel.grid.major.x = element_blank(),
            panel.grid.minor.x = element_blank() # remove?
        )
    return(graph)
}

# 95% percentile for a grant = $738726.30 USD

agency_type_plot <- funding_violins_general(df_violinplot
                                            , q = 95
                                            , x_label = "Type of Institution"
                                            , y_label = "Value of Grants (100000x USD)"
                                            , scale_by = 10^5)
agency_type_plot


a <- ggplotly(agency_type_plot, tooltip = c("density")) %>%
    config(displayModeBar = F)

# Saving without displayModeBar:
# config(ggplotly(), displaylogo = FALSE, modeBarButtonsToRemove = list('Pan'))
htmlwidgets::saveWidget(a, "insitution_type.html")

# --------------------------------------------------------
# Plots - Exploratory
# --------------------------------------------------------

df_plotting <- df[!(is.na(df$GrantYear)) & !(is.na(df$FunderBlock)),]

# Grant Density

ggplot(df_plotting[df_plotting$NormalizedAmount < (2.5*10^5),], aes(x=FunderBlock, y=NormalizedAmount)) +
    geom_violin(aes(fill = FunderBlock), na.rm=TRUE) +
    # scale_x_continuous(limits=c(0, 750000), breaks = seq(0, 750000, 150000), expand = c(0, 0)) +
    # scale_y_continuous(limits=c(0, 0.00005), expand = c(0, 0)) +
    ylab("Value of Grants (USD)") +
    xlab("") +
    labs(color = "Funding Block", fill = "Funding Block") + 
    theme_bw() +
    theme(
        axis.line = element_line(colour = "black"),
        panel.grid.major = element_blank(),
        panel.border = element_blank(),
        axis.ticks=element_blank(),
        panel.grid.major.x = element_blank(),
        panel.grid.minor.x = element_blank(),
        panel.background = element_blank()
    ) 

# ---------------------------
# Institution Type data on ~ 65% of Entries in the Database
nrow(df[!(is.na(df$InstitutionType)),]) / nrow(df)
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

agg_block <- data.frame(aggregate(round(Grant, 2) ~ GrantYear + FunderBlock
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
    scale_y_continuous(breaks = breaks, labels = formatted_labels, expand = c(0, 0)) +
    scale_x_discrete(expand = c(0,0))
















































