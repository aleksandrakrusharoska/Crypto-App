package mk.ukim.finki.das.prototype.service;

import mk.ukim.finki.das.prototype.model.technical.TechnicalAnalysisResult;

public interface TechnicalAnalysisService {
    TechnicalAnalysisResult analyze(String symbol);
}
