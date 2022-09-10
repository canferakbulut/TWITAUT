#oversampling plot
under <- c(40, 60, 80)
over <- c(40, 50, 60)
original_sample <- c(12128, 932, 392)
label <- c("Neither", "Autistic", "Parent")
df <- data.frame(trans = rep("Original", 3), label = label, sample = original_sample)
for(i in seq_along(under)){
  for(j in seq_along(over)){
    maj <- ceiling(original_sample[1] * under[i]/100)
    min <- c(ceiling(original_sample[1] * over[j]/100), ceiling(original_sample[1] * over[j]/100))
    sample <- as.numeric(cO=(maj, min))
    trans <- rep(paste0(as.character(under[i]), "% Under : ", as.character(over[j]), "% Over"), 3)
    df <- rbind(df, cbind(trans, label, sample))
  }2
}

df$label <- factor(c("Neither", "Autistic", "Parent"), levels = c("Neither", "Autistic", "Parent"))

df$trans <- factor(df$trans, levels =  unique(df$trans))
library(ggplot2)
plot <- ggplot(df, aes(x = label, y = as.numeric(sample), fill = label)) + geom_bar(stat = "identity") + facet_wrap(~trans) + 
  theme_minimal() + scale_fill_grey() + guides(fill=guide_legend(title="Group")) +
  theme(axis.text.x=element_blank(),
        axis.title.x = element_blank(),
        axis.title.y = element_blank(),#remove x axis labels
        axis.ticks.x=element_blank(),
        axis.text.y = element_text(angle = -25, hjust = 0.4, size = 12),
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.border = element_rect(colour = "lightgray", fill=NA, size=1),
        legend.position = c(0.6, 0.205),
        legend.title = element_text(size = 18),
        legend.text=element_text(size=16),
        strip.text.x = element_text(size = 18),
        legend.key.size = unit(1, 'cm'))
        #remove x axis ticks #remove y axis ticks
plot  

