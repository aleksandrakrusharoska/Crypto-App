package mk.ukim.finki.das.prototype.model.sentiment_onchain;

import java.util.List;


public class SentimentOnChain {

    public String symbol;

    public SentimentPart sentiment;
    public OnChainPart onchain;
    public CombinedPart combined;

    // ================= SENTIMENT =================

    public static class SentimentPart {
        public int articleCount;
        public double positiveRatio;
        public double neutralRatio;
        public double negativeRatio;
        public double sentimentScore;
        public String interpretation;
        public List<SampleArticle> samples;
    }

    public static class SampleArticle {
        public String title;
        public String label;        // POSITIVE / NEUTRAL / NEGATIVE
        public double score;        // FinBERT score
        public String source;
        public String publishedAt;
    }

    // ================= ON-CHAIN =================

    public static class OnChainPart {
        public double marketCap;
        public double volume24h;
        public double priceChange24h;
        public Double nvt;
        public double onchainScore;
        public String interpretation;
        public List<String> signals;
    }

    // ================= COMBINED =================

    public static class CombinedPart {
        public double finalScore;
        public String signal;
        public String explanation;
    }
}

