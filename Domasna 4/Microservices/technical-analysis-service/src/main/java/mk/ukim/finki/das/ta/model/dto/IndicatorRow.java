package mk.ukim.finki.das.ta.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import mk.ukim.finki.das.ta.model.enums.TaSignal;

@Data
@AllArgsConstructor
public class IndicatorRow {
    private String name;
    private double value;
    private TaSignal action;
}
