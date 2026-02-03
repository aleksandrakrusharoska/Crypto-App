package mk.ukim.finki.das.prototype.model.technical;

import lombok.Data;
import mk.ukim.finki.das.prototype.model.dto.IndicatorRow;

import java.util.List;

@Data
public class TechnicalAnalysisResult {

    // ================= DAILY =================
    private FrameIndicators dailyIndicators;
    private TimeframeSignal dailyOscillators;
    private TimeframeSignal dailyMovingAverages;
    private TimeframeSignal dailySummary;

    // ================= WEEKLY =================
    private FrameIndicators weeklyIndicators;
    private TimeframeSignal weeklyOscillators;
    private TimeframeSignal weeklyMovingAverages;
    private TimeframeSignal weeklySummary;

    // ================= MONTHLY =================
    private FrameIndicators monthlyIndicators;
    private TimeframeSignal monthlyOscillators;
    private TimeframeSignal monthlyMovingAverages;
    private TimeframeSignal monthlySummary;

    private List<IndicatorRow> dailyIndicatorDetails;
    private List<IndicatorRow> weeklyIndicatorDetails;
    private List<IndicatorRow> monthlyIndicatorDetails;

}
