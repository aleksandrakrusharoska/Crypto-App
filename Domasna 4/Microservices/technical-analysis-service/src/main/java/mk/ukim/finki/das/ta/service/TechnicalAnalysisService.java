package mk.ukim.finki.das.ta.service;

import mk.ukim.finki.das.ta.model.dto.TechnicalAnalysisResult;

public interface TechnicalAnalysisService {
    TechnicalAnalysisResult analyze(String symbol);
}
