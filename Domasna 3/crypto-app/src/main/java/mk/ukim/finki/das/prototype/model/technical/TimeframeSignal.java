package mk.ukim.finki.das.prototype.model.technical;

import lombok.Data;
import mk.ukim.finki.das.prototype.model.enums.TaSignal;

@Data
public class TimeframeSignal {
    private TaSignal signal;
    private SignalStats stats;

    private TaSignal baseSignal;
    private String filterReason;
}
