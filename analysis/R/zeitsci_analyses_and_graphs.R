# -----------------------------------------------------------------------
# Science Funding Analysis                       
# -----------------------------------------------------------------------

# Import Modules
library('ez')
library('lme4')
library('plyr')
library('ggvis')
library('scales')
library('plotly')
library('pbapply')
library('ggplot2')
library('stringr')
library('reshape2')
library('extrafont')
library('gridExtra')
options(scipen=10)

# Set seed
set.seed(100)

# Import extra fonts
# font_import()

# ------------------------------------------------ 
# General Use Functions
# ------------------------------------------------ 

count_unique <- function(search_string, input_string){
    count = 0
    for (i in strsplit(input_string, "")[[1]]){
        if (i == search_string){
            count = count + 1
        }
    }
    return(count)
}

random_df_rows <- function(data_frame, percent){
    row_numb <- round(nrow(data_frame) * (percent/100))
    subsection <- data_frame[sample(nrow(data_frame), row_numb),]
    return(subsection)
}

# Define a permutation test -- Not currently used.
permutation_test <- function(vector_a, vector_b, rep_num=250){
    #' @param vector_a: subsection 1
    #' @param vector_b: subsection 2
    #' @param rep_num: number of replications
    
    # Get the descriptive stat
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
    mean_diff_vector <- pbapply(X = vector_a_random, MARGIN = 2, FUN = mean) - pbapply(X = vector_b_random, MARGIN = 2, FUN = mean)
    
    # Compute a p-value
    p <- (sum(abs(mean_diff_vector) >= mean_diff)) / rep_num
    
    return(list(p, mean_diff, mean_diff_vector))
}

# Test
# permutation_test(rnorm(100000), rnorm(100000))[[1]] # 1

boot_ci = function(data1, data2, alpha=0.05, nsamps=1000){
    lower <- alpha/2
    upper <- 1 - lower
    d1 = pbreplicate(nsamps, mean(sample(data1, length(data1), replace = TRUE)) ) 
    d2 = pbreplicate(nsamps, mean(sample(data2, length(data2), replace = TRUE)) )
    b = sort(d1 - d2)
    ci = c(b[round(lower*nsamps, 1)], b[round(upper*nsamps, 1)])
    return(ci)
}

comprss <- function(tx) { 
    # source: http://stackoverflow.com/a/28160474/4898004
    labels <- c(""," K"," M"," B"," T")
    div <- findInterval(as.numeric(gsub("\\,", "", tx)), c(1, 1e3, 1e6, 1e9, 1e12) )
    paste0(round( as.numeric(gsub("\\,","",tx))/10^(3*(div-1)), 2), labels[div])
}

# ------------------------------------------------------------------------------------------------------------
# Read in the Data
# ------------------------------------------------------------------------------------------------------------

setwd("~/Google Drive/Programming Projects/ZeitSci/analysis/R")
df <- read.csv("funding_data.csv", na.strings=c("","NA", "NAN", 'nan', 'NaN'))

# Numeric Conversions
df$Grant <- as.numeric(df$Grant)
df$Endowment <- as.numeric(df$Endowment)
df$NormalizedAmount <- as.numeric(df$NormalizedAmount)

# Limit to Grants > 0
df <- df[df$NormalizedAmount > 0,]

# Convert StartDate to a format R understands
df$StartDate <- as.Date(df$StartDate, "%d/%m/%Y")

# Work out grant start year and limit to >= 2000
df$StartYear <- as.numeric(strftime(df$StartDate, "%Y"))
df <- df[df$StartYear > 1999,]

df$StartYear <- df$StartYear + (df$Quarter/4 - 0.25)

# ------------------------------------------------------------------------------------------------------------
# Science Funding Over the Years
# ------------------------------------------------------------------------------------------------------------

# recession_df <- data.frame(xmin=c(2007.92), xmax=c(2009.50)) # National Bureau of Economic Research (http://www.nber.org/cycles/cyclesmain.html)

timeseries_df <- df[!is.na(df$Quarter) & !is.na(df$NormalizedAmount),]
timeseries_df <- timeseries_df[timeseries_df$StartDate >= "2004/01/01",]

yearly_data_agg <- function(agg_formula, data){
    parse_col = count_unique("+", agg_formula) + 2
    aggregated_data <- aggregate(as.formula(agg_formula)
                                 , data = data
                                 , FUN = function(x) {
                                     return(c(mean(x), length(x)))
                                 })
    aggregated_data$metric <- aggregated_data[,parse_col][,1]
    aggregated_data$count <- as.numeric(aggregated_data[,parse_col][,2])
    aggregated_data <- subset(aggregated_data, select = -parse_col)
    return(aggregated_data)
}

# Limit Date
timeseries_df <- timeseries_df[timeseries_df$StartYear >= 2005,]
timeseries_df <- timeseries_df[timeseries_df$StartYear < 2016,]

# -----------------------------------
# For FunderBlocks with Month Info
# -----------------------------------

sum_funding_quater_rest <- yearly_data_agg("NormalizedAmount ~ StartYear + Quarter + FunderBlock", timeseries_df)

rescale_wrap <- function(vect, scalar=20, floor_val=5){
    scaled <- (reshape::rescaler.default(vect, type = "range") * scalar) + floor_val
    return(scaled)
}

# Scale w.r.t. each FunderBlock
# for (block in unique(sum_funding_quater_rest$FunderBlock)){
#     vect <- sum_funding_quater_rest$count[sum_funding_quater_rest$FunderBlock == block]
#     sum_funding_quater_rest$count[sum_funding_quater_rest$FunderBlock == block] <- rescale_wrap(vect)
# }

# sum_funding_quater_rest$count <- rescale_wrap(sum_funding_quater_rest$count)
sum_funding_quater_rest$scaled_count <- Reduce(c, lapply(sum_funding_quater_rest$count, function(x){
    scaled <- sqrt(x/pi)/2.5 + 6
    return(scaled)
}))

# Correct 'Europe' --> 'European Commission'
sum_funding_quater_rest$FunderBlock <- as.character(sum_funding_quater_rest$FunderBlock)
sum_funding_quater_rest$FunderBlock[sum_funding_quater_rest$FunderBlock == "Europe"] <- 'EU Commission'
sum_funding_quater_rest$FunderBlock <- as.factor(sum_funding_quater_rest$FunderBlock)

# Quater Labels
quater_labels <- apply(sum_funding_quater_rest[,c('Quarter', 'FunderBlock')], 1, FUN = function(x){
    if (x[2] != 'Canada'){
        return(paste0("Q", x[[1]]))
    } else {
        return("Q1-4")
    }
})
sum_funding_quater_rest$QuarterLabels <- Reduce(c, (quater_labels))

# Amount Label
# sum_funding_quater_rest$formatted_money <- dollar_format(largest_with_cents=Inf, prefix = "$", suffix = " (USD)")(sum_funding_quater_rest$metric)
sum_funding_quater_rest$formatted_money <- comprss(sum_funding_quater_rest$metric)

# Colors for countris
colors <- c("#e74c3c", "#2ecc71", "#9b59b6",  "#3498db")

# UK = 9b59b6 - purple
# CA = e74c3c - red
# US = 3498db - blue
# EU = 2ecc71 - green

# Set Font
f <- list(family = "Lucida Grande",
          size = 14,
          color = "#808080")

plot_ly(sum_funding_quater_rest,
        x = ~StartYear,
        y = ~metric,
        color = ~FunderBlock,
        size = ~scaled_count,
        colors = colors,
        type = 'scatter',
        mode = 'markers',
        sizes = range(sum_funding_quater_rest$scaled_count),
        marker = list(symbol = 'circle',
                      sizemode = 'diameter',
                      line = list(width = 1.5, color = '#FFFFFF')
        ),
        text = ~paste('Year:', paste0(floor(StartYear), " (", QuarterLabels, ")"),
                      '<br>Average Value:', formatted_money,
                      '<br>Number of Grants:', dollar_format(prefix="")(c(count))
                      ),
        hoverinfo="text+name"
    ) %>%
    layout(xaxis = list(title = 'Start Date',
                        showgrid = FALSE,
                        dtick = 1,
                        range = c(2004.55, 2015.99),
                        tickwidth = 0),
           yaxis = list(title = 'Average Value of Grant (USD)<br><br>',
                        zerolinewidth = 1,
                        gridwith = 2,
                        tickwidth = 0,
                        zerolinecolor='#EEEEEE'),
           font = f,
           margin = list(b=50),
           legend = list(x = 0.89, y = 1)
    ) %>%
    config(displayModeBar = FALSE)

# ------------------------------------------------------------------------------------------------------------
# Category of Organization
# ------------------------------------------------------------------------------------------------------------

org_category <- df[, c("FunderNameAbbrev", "FunderBlock", "OrganizationCategory", "NormalizedAmount", "StartYear")]
org_category <- org_category[!is.na(org_category$FunderNameAbbrev),]
org_category <- org_category[!is.na(org_category$NormalizedAmount),]
org_category <- org_category[!is.na(org_category$OrganizationCategory),]
org_category <- org_category[org_category$StartYear >= 2005,]

# Simplify Categories
category_simplify <- function(category){
    # if (grepl("Educational", category) == TRUE){
        # return("Educational")
    if (grepl("Governmental", category) == TRUE){
        return("Governmental")
    } else if (grepl("Industry", category) == TRUE){
        return("Industry")
    } else if (grepl("Institute", category) == TRUE){
        return("Institute")
    } else if ((grepl("Medical", category) == TRUE) & (grepl("NGO", category) == TRUE)){
        return("Medical")
    } else {
        return(category)
    }
}
org_category$OrganizationCategory <- unlist(pblapply(as.vector(org_category$OrganizationCategory), category_simplify))

# Aggregate
funder_org_sum <- aggregate(NormalizedAmount ~ OrganizationCategory + FunderNameAbbrev + FunderBlock + floor(StartYear), data = org_category, FUN = function(x){
    return(c(sum(x), length(x)))
})

# Parse Output
funder_org_sum$TotalAmount <- data.frame(funder_org_sum[,5])[,1]
funder_org_sum$count <- data.frame(funder_org_sum[,5])[,2]
funder_org_sum <- subset(funder_org_sum, select = -NormalizedAmount)
colnames(funder_org_sum)[4] <- 'StartYear'

# Limit to before 2016
funder_org_sum <- funder_org_sum[funder_org_sum$StartYear < 2016,]

# Fix RC-UK --> RCUK
funder_org_sum$FunderNameAbbrev <- gsub("-", " ", funder_org_sum$FunderNameAbbrev)

# Condense Educational; Medical
funder_org_sum$OrganizationCategory[funder_org_sum$OrganizationCategory == 'Educational; Medical'] <- "Medical Edu."

# Amount Labels
funder_org_sum$AmountLabel <- comprss(funder_org_sum$TotalAmount)

# ggplot color pallet (http://www.cookbook-r.com/Graphs/Colors_(ggplot2))
category_plot_colors <- c('#1bb840', '#cc9521', '#93a920', '#f67770', '#1fbfc3', '#1dabfc', '#c680fc', '#e570f0') 

# Generate plot
plot_ly(funder_org_sum,
         x = ~StartYear,
         y = ~TotalAmount,
         color = ~OrganizationCategory, 
         colors = category_plot_colors,
         type = 'bar',
         text = ~paste('Total:', AmountLabel,
                       '<br>Number of Grants:', dollar_format(prefix="")(c(count))),
         hoverinfo="text+name"
    ) %>%
    layout(xaxis = list(
                        title = "Start Year",
                        dtick = 1
                    ),
            yaxis = list(
                        title="Total Grants (USD)",
                        zerolinecolor='#EEEEEE'
                    ),
            hovermode="closest",
            font = f,
            legend = list(x = 0.90, y = 1)
    ) %>%
    config(displayModeBar = FALSE)

# ------------------------------------------------------------------------------------------------------------
# Break on Public vs. Private
# ------------------------------------------------------------------------------------------------------------

# Are these two groups different w.r.t. the amount of funding they receive on average?

# Define and Drop NAs
type_df <- df[(df$StartYear >= 2005) & (df$StartYear < 2016),]
public <- type_df$NormalizedAmount[type_df['InstitutionType'] == "Public"]
private <- type_df$NormalizedAmount[type_df['InstitutionType'] == "Private"]
public <- public[!is.na(public)]
private <- private[!is.na(private)]

# Assess Viability of using an independent samples t-test to compare these groups

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
# CI for Institution Type
# --------------------------------------------------

# Abandon t-test and use a nonparametric method: the randomization test.

# Set alpha level
alpha_value = 0.05

# Construct a Confidence Interval

# Drop alpha
confidence_interval <- boot_ci(private, public, alpha = alpha_value, nsamps=10000)
delta <- (mean(private) - mean(public)) 

# Descriptive Stats
length(public); mean(public); sd(public)
length(private); mean(private); sd(private)
total_obs <- (length(public) + length(private))
length(public) / total_obs

# CI
delta; confidence_interval

# ---------------------------
# Violin Plot
# ---------------------------

# nrows(df_violinplot) == total_obs
df_violinplot <- type_df[!(is.na(type_df$InstitutionType)),] 

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
        stat_summary(inherit.aes = FALSE
                     , data = data_frame
                     , aes(x = InstitutionType, y = NormalizedAmount/(scale_by), fill = InstitutionType)
                     , fun.y = mean
                     , geom = 'point'
                     , colour = "#333333"
                     , size = 3
                     , position = position_dodge(width = 0.9)) +
        theme(
            legend.position = "none",
            axis.title.y = element_text(margin = margin(r=25)),
            text = element_text(size = 14, color = "#808080", family = "Lucida Grande"),
            axis.text=element_text(size = 12, color = "#808080", family = "Lucida Grande"),
            panel.grid.major.x = element_blank(),
            panel.grid.minor.x = element_blank() 
        )
    return(graph)
}

# 95% percentile for a grant = 90K USD

insitution_type_plot <- funding_violins_general(data_frame=df_violinplot
                                                , q = 95
                                                , x_label = "\n\nType of Institution"
                                                , y_label = "Value of Grant (100000x USD)\n\n"
                                                , scale_by = 10^5)

insitution_type_plotly <- ggplotly(insitution_type_plot, tooltip = c("density")) %>%
                            config(displayModeBar = FALSE)

insitution_type_plotly

# ------------------------------------------------------------------------------------------------------------
# Endowment
# ------------------------------------------------------------------------------------------------------------

# In progress

df_endowment <- df[!(is.na(df$Endowment)) & !(is.na(df$Funder)),]

unique(df_endowment$Funder)

endowment_agg <- aggregate(NormalizedAmount ~ Endowment + Funder, data = df_endowment, FUN = mean)


ggplot(endowment_agg, aes(x = log(Endowment), y = log(NormalizedAmount), color = Funder)) +
    geom_point()

m <- lm(NormalizedAmount ~ log(Endowment), data = df_endowment[df_endowment$Endowment < (1 * 10^9),])
summary(m)

# ------------------------------------------------------------------------------------------------------------
# Investigate if Value of Prior Grants Predicts value of future Grants
# ------------------------------------------------------------------------------------------------------------

# In progress

# Create a grants df by Researcher and Org
prior_grants <- df[!is.na(df$Researcher),]
prior_grants <- prior_grants[!is.na(prior_grants$NormalizedAmount),]
prior_grants <- prior_grants[!is.na(prior_grants$OrganizationName),]

reseacher_total <- aggregate(NormalizedAmount ~ Researcher + OrganizationName, data = df, FUN = 'sum')

# Build a Mixed Effects Model to Predict Total Amount
# from Value of Prior Grants as a fixed effect and Researcher as an Random Effect

# ------------------------------------------------------------------------------------------------------------
# Country Analysis
# ------------------------------------------------------------------------------------------------------------

# In progress

# North America
df_north_america <- df[df$OrganizationBlock %in% c("United States", "Canada"),]
df_north_america <- df_north_america[!(is.na(df_north_america$OrganizationState)),]
df_north_america <- df_north_america[nchar(as.character(df_north_america$OrganizationState)) > 2,]

state_prov_sum <- aggregate(NormalizedAmount ~ OrganizationState, data = df_north_america, FUN = "sum")


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
















































