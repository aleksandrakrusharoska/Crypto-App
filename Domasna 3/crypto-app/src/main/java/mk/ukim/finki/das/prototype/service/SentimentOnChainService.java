package mk.ukim.finki.das.prototype.service;

import mk.ukim.finki.das.prototype.model.sentiment_onchain.SentimentOnChain;

public interface SentimentOnChainService {
    SentimentOnChain analyze(String symbol);
}

