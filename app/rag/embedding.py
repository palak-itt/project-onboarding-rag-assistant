

# The first question is what should be embedded, because whatever I embed based on that it will do semantic searching. And I established that embedding should have chunk text but also it's heading tree(parent-child). But since I am using fixed chunking so i cannot have that for now. So I will just embed each chunk.
# The embedding models are different - I can have transformer based, tfidf, word2vec, rnn/cnn based, but for ease of doing things, I will choose one of transformer based. 
# But then which one, how they differ, how should one decide?
# And I don't need to think about which tokenizer to use before embedding. Because each embedding model comes with it's own tokenizer. Why? Because each tokenizer may assign differnt token ID for differnt words, and if th e mdoel is trained using those ID's, with a differnet tokenizer it will mess up and generate incorrect results.

