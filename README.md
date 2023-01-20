# "Who speaks for the autistic community?" aka TWITAUT

This documentation is intended as a guideline for those wishing to replicate the methodology of the paper. Please note that Twitter API Academic Research Accesss prohibits authors from publishing full data-sets containing Tweets or user descriptions, so in many cases, a direct replication may not be possible. All Tweets and user descriptions for TWITAUT were collected between April and July of 2022 using the documented code.

## The _scraping_ folder: retrieving user descriptions and Tweets 

Before beginning to collect data from Twitter through the following scripts, several personalized tokens and keys must be obtained by applying for [Twitter API access](https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api) and passed into the terminal as environmental variables using the `os` package. Much of this code was adapted for the purposes of TWITAUT from the sample code provided by the Twitter Dev team, available on [GitHub](https://github.com/twitterdev/Twitter-API-v2-sample-code). 

+ get_user_details_270622.py: from a list of user IDs, retrieves details such as a user's username, public display name, self-written biography, the date of account creation, and whether or not the account is verified. Essential step for assembling the annotation set, training the classification models, and creating distinct corpora of Tweets for each of the samples of interest. 

+ retrieving_charities_280522.py: from a set of keywords, conducts a relevance-based search of public user accounts and returns user details. Used as a preliminary method of assembling a list of Twitter accounts associated with autism charities and autistic self-advocacy groups (final human-checked lists available on [OSF](https://osf.io/vkqx2/) as _ac_list_220712.txt_ and _ac_list_220712.txt_, respectively). 

+ tweets_from_orgs_300522.py: from a list of usernames, retrieves up to 3,200 Tweets for each account. 

+ tweets_with_keywords_270622.py: from a list of keywords (available on [OSF](https://osf.io/vkqx2/) as _autism-keywords.txt_), retrieves Tweets containing keywords. The `get_random_time` function selects several random 24-hour time periods within a range of years (from a base year until the scrape date), and restricts the search to all Tweets made between these time intervals. The number of intervals per year and the earliest possible search dates are adjustable parameters. Additionally, code safeguards against the small chance of duplicates by removing time intervals represented in  previous scrapes from sampling space through `existing_start_times` function. 

## The _analysis_ folder: training classification model for user descriptions and generating word embeddings of Tweets

+ feature_extraction_220819.py: mostly experimental code, but contains useful function `feature_extraction`, which returns the most distinct uni-grams and bi-grams for users in different classification groups, allowing for more relevant and precise searching criteria when creating annotation sets. Discussed in further details under _Manual data augmentation procedure_ in the Appendix.

+ following_network_APIV2_220713.py & following_networks_220712.py: not used in the study, but could be useful for related work. Collects a node-and-edge list of which users a specific user is following for network-based analyses and visualizations.

+ training_selfidentification_labels_220705.py: creates annotation sample, reads completed annotation data-set, then trains several classification models (2 embedding types x 4 estimators), conducts a grid-search to tune hyper-parameters, and outputs model performances. Dependencies: Doc2VecTransformer.py.

+ final_classification_220829.py: uses best-performing model from previous script to train a classifier and append predicted labels onto the full set of user descriptions, creating distinct corpora for autistic people and parents of autistic children.

+ word2vec_training_220902.py: reads baseline corpus, trains 48 baseline Word2Vec models with different hyper-parameter combinations, updates each baseline model on the four corpora of interest separately, then generate cosine similarity score for each relevant pairing per identical word. Final dataset of cosine similarities can be found on [OSF](https://osf.io/vkqx2/) as _cosine_similarity_dataset_final.txt_.

## The _plotting_ folder: bootstrapping and plotting results

+ final_results_plot.r: performs bootstrapping procedure, selecting 1,000 samples of 10,000 shared words per specification, then plots retrieved effect size and significant values on a specification curve plot. Also generates a simple baseline "random" plot by shuffling cosine similarity values. Can be used on the cosine similarity data-set on OSF to replicate results directly; however, note that due to lack of seed in the randomization, results may not be identical. 

+ oversamplingplot.r: used to generate simple bar-graph of oversampling and undersampling procedure for imbalanced datasets. More detail on theoretical justification and implementation of over/undersampling procedure can be found in Appendix.

