library(ggplot2)
library(dplyr)
library(MASS)
library(data.table)

dt <- fread("cosine_similarity_data_final.csv")
dt[, `:=`(cos_sim.s = scale(cos_sim)[,1],
          org = as.factor(org),
          indv = as.factor(indv))]

### bootstrapping and retrieving b3 vals

get_spec <- function(dt, spec){
  setkey(dt, specification)
  return(dt[.(spec)])}

chunk <- function(x,n) {
  return(split(x, ceiling(seq_along(x)/n)))
}

bootstrap <- function(spec_dt, chunks, n_words){
  word_sample <- sample(seq_along(chunks), n_words)
  index <- unname(unlist(chunks[word_sample]))
  return(dt[index, ])
  
}

full_bootstrap <- function(dt, bootstrap_per_spec, n_words){
  spec <- unique(dt$specification)
  tot_n <- length(spec) * bootstrap_per_spec
  results <- list(asag_indv = list(b3 = rep(NA, tot_n), p = rep(NA, tot_n),
                                   random_b3 = rep(NA, tot_n), random_p = rep(NA, tot_n)),
                  ac_par = list(b3 = rep(NA, tot_n), p = rep(NA, tot_n),
                                random_b3 = rep(NA, tot_n), random_p = rep(NA, tot_n)))
  contr_list <- list(asag_indv = list(org = contr.treatment(n = 2, base = 1), 
                                 indv = contr.treatment(n = 2, base = 2)),
                ac_par = list(org = contr.treatment(n = 2, base = 2), 
                              indv = contr.treatment(n = 2, base = 1)))
  for(i in seq_along(spec)){ #for each specification
    spec_dt <- get_spec(dt, spec[i]) #get specification dt
    chunks <- chunk(seq_len(nrow(spec_dt)), 4) #split rows into groups of 4, ie by word
    for(j in seq_len(bootstrap_per_spec)){
      word_dt <- bootstrap(spec_dt, chunks, n_words)
      random_dt <- word_dt[, cos_sim.s := sample(cos_sim.s)]
        for(k in seq_along(contr_list)){
          pair <- ifelse(k == 1, "asag_indv", "ac_par")
          linmod <-  summary(lm(formula = cos_sim.s ~ org * indv, data = word_dt,
                                contrasts = contr_list[[pair]]))[["coefficients"]]
          rand_linmod <- summary(lm(formula = cos_sim.s ~ org * indv, data = random_dt,
                                    contrasts = contr_list[[pair]]))[["coefficients"]]
          results[[str]][["b3"]][j] <- linmod[4,1]
          results[[str]][["p"]][j] <- linmod[4,4]
          results[[str]][["random_b3"]][j] <- rand_linmod[4,1]
          results[[str]][["random_p"]][j] <- rand_linmod[4,4]
          }
      }
   }
  return(results)
}

bootstrap_per_spec <- 1000
n_words <- 10000
results <- full_bootstrap(dt, bootstrap_per_spec, n_words)

sig <- function(p){
  if(is.na(p)){
    return(NA)
  } else if(p < 0.001) {
    return("***")
  } else if (p < 0.01){
    return("**")
  } else if (p < 0.05) {
    return("*")
  } else {
    return("ns")
  }
}

to_df <- function(results_list, pair, actual_or_random = "actual"){
  if(actual_or_random == "actual"){
      index <- c(1,2) 
    } else if(actual_or_random == "random") {
      index <- c(3,4)
    }
  return(as.data.frame(do.call(cbind.data.frame, results_list[[pair]][index])))
}
## pass in 
sca_df <- function(results_list, pair1 = "asag_indv", pair2 = "ac_par", actual_or_random = "actual"){
  add <- ifelse(actual_or_random == "actual", "", "_random")
  df1 <- results_list %>% to_df(pair = pair1) %>% mutate(rank = rank(b3), sig = sapply(p, sig), name = paste0(pair1, add))
  df2 <- results_list %>% to_df(pair = pair2) %>% mutate(rank = rank(b3), sig = sapply(p, sig), name =  paste0(pair2, add))
  return(rbind(df1,df2))
}

plot_df <- results %>% sca_df() %>% 
  rbind(sca_df(results, actual_or_random = "random")) %>%
          filter(!is.na(sig))

sca_plot <- function(df){
  
  labels <- c(
    'ac_par' = "Charity x parent",
    'asag_indv'= "Self-advocacy x autistic",
    'asag_indv_random' = "Self-advocacy x autistic (random)",
    'ac_par_random' = "Charity x parent (random)"
  )
  
  sum_df <- df %>% group_by(name) %>% summarize(mean = mean(b3, na.rm = T), sd = sd(b3, na.rm = T)) %>% as.data.frame()
  df %>% ggplot(aes(x = rank, y = b3, color = p)) +  
    guides(color = guide_colorbar(order = 1)) + geom_point() + scale_color_gradient(low="blue", high="pink") +
    facet_wrap(~name, labeller = as_labeller(labels)) + 
    geom_hline(data = sum_df, aes(yintercept = mean), color = "darkblue", linetype = "dashed") +
    geom_hline(data = sum_df, aes(yintercept = mean + sd), color = "gray", linetype = "dashed") +
    geom_hline(data = sum_df, aes(yintercept = mean - sd), color = "gray", linetype = "dashed") +
    theme(panel.grid.major = element_line(color = "white"), 
          panel.grid.minor = element_line(color = "white"), 
          panel.background = element_rect(fill = "white"),
          panel.border = element_rect(color = "gray", fill = NA),
          #axis.line = element_line(colour = "gray"),
          strip.background = element_rect(fill = "white"),
          strip.text.x = element_text(size = 12),
          legend.title = element_text(size = 10),
          legend.text=element_text(size=9),
          legend.key.size = unit(0.8, 'cm')) + 
    labs(x = "Specification # (by effect size)", y = "Beta coefficient")
} 

plot_df %>% sca_plot
