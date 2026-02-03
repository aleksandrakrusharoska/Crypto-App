package mk.ukim.finki.das.ta.controller;

import mk.ukim.finki.das.ta.model.dto.TechnicalAnalysisResult;
import mk.ukim.finki.das.ta.service.TechnicalAnalysisService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/technical")
public class TechnicalAnalysisController {

    private final TechnicalAnalysisService technicalAnalysisService;

    public TechnicalAnalysisController(TechnicalAnalysisService technicalAnalysisService) {
        this.technicalAnalysisService = technicalAnalysisService;
    }


    @GetMapping("/analyze")
    public TechnicalAnalysisResult analyze(@RequestParam String symbol) {
        return technicalAnalysisService.analyze(symbol);
    }
}
