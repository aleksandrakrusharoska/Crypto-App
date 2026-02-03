package mk.ukim.finki.das.prototype.model.technical;

import lombok.Data;

@Data
public class FrameIndicators {

    // ========== OSCILLATORS ==========
    private Double rsi;
    private Double macd;
    private Double stoch;
    private Double adx;
    private Double cci;
    private Double momentum;

    // ========== MOVING AVERAGES ==========
    private Double sma;
    private Double ema;
    private Double wma;
    private Double smaShort;
    private Double emaShort;

    // ========== BOLLINGER ==========
    private Double bollingerUpper;
    private Double bollingerLower;

    // ========== VOLUME ==========
//    private Double volumeMa;
}
