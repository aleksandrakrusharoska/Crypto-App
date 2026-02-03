package mk.ukim.finki.das.ta.model.dto;


import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TechnicalAnalysisDto {
    private Double rsi;
    private String macdSignal;
    private String movingAverageSignal;
    private String summarySignal;
}

