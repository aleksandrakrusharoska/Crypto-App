package mk.ukim.finki.das.app.model.dto.technical;

import lombok.Data;

import java.util.List;

@Data
public class TechnicalAnalysisResult {

    private FrameIndicators dailyIndicators;
    private TimeframeSignal dailyOscillators;
    private TimeframeSignal dailyMovingAverages;
    private TimeframeSignal dailySummary;

    private FrameIndicators weeklyIndicators;
    private TimeframeSignal weeklyOscillators;
    private TimeframeSignal weeklyMovingAverages;
    private TimeframeSignal weeklySummary;

    private FrameIndicators monthlyIndicators;
    private TimeframeSignal monthlyOscillators;
    private TimeframeSignal monthlyMovingAverages;
    private TimeframeSignal monthlySummary;

    private List<IndicatorRow> dailyIndicatorDetails;
    private List<IndicatorRow> weeklyIndicatorDetails;
    private List<IndicatorRow> monthlyIndicatorDetails;

}
