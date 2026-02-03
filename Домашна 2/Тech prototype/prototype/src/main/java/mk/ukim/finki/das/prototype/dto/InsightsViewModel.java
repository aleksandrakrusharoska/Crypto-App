package mk.ukim.finki.das.prototype.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import mk.ukim.finki.das.prototype.model.Record;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class InsightsViewModel {
    private String symbol;
    private List<String> dates;
    private List<Double> closePrices;
    private String periodStart;
    private String periodEnd;
    private List<Record> weeklyData;
    private List<Record> historyData;
}

