package mk.ukim.finki.das.prototype.service.impl;

import mk.ukim.finki.das.prototype.model.sentiment_onchain.SentimentOnChain;
import mk.ukim.finki.das.prototype.service.SentimentOnChainService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class SentimentOnChainServiceImpl implements SentimentOnChainService {

    private final RestTemplate restTemplate;

    @Value("${python.sentiment.url:http://localhost:5002}")
    private String pythonBaseUrl;

    public SentimentOnChainServiceImpl() {
        this.restTemplate = new RestTemplate();
    }

    @Override
    public SentimentOnChain analyze(String symbol) {
        String url = pythonBaseUrl + "/api/analyze/" + symbol.toUpperCase();
        return restTemplate.getForObject(url, SentimentOnChain.class);
    }
}


