package mk.ukim.finki.das.ta.model.dto;

import lombok.Data;
import mk.ukim.finki.das.ta.model.enums.TaSignal;

@Data
public class TimeframeSignal {
    private TaSignal signal;
    private SignalStats stats;

    private TaSignal baseSignal;
    private String filterReason;
}
