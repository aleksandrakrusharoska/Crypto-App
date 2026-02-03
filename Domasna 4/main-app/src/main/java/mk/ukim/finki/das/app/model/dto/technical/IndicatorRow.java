package mk.ukim.finki.das.app.model.dto.technical;

import lombok.AllArgsConstructor;
import lombok.Data;
import mk.ukim.finki.das.app.model.enums.TaSignal;

@Data
@AllArgsConstructor
public class IndicatorRow {
    private String name;
    private double value;
    private TaSignal action;
}
