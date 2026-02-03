package mk.ukim.finki.das.app.model.dto.technical;

import lombok.Data;

@Data
public class FrameIndicators {

    private Double rsi;
    private Double macd;
    private Double stoch;
    private Double adx;
    private Double cci;
    private Double momentum;

    private Double sma;
    private Double ema;
    private Double wma;
    private Double smaShort;
    private Double emaShort;

    private Double bollingerUpper;
    private Double bollingerLower;

}
