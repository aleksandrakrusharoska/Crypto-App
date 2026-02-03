package mk.ukim.finki.das.app.model.dto.technical;

import lombok.Data;

@Data
public class SignalStats {
    private int sell;
    private int neutral;
    private int buy;
}
