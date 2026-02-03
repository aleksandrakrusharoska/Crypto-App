package mk.ukim.finki.das.ta.service.impl;

import mk.ukim.finki.das.ta.model.dto.*;
import mk.ukim.finki.das.ta.model.entity.Record;
import mk.ukim.finki.das.ta.model.enums.TaSignal;
import mk.ukim.finki.das.ta.model.exception.InsufficientDataException;
import mk.ukim.finki.das.ta.repository.HistoricalDataRepository;
import mk.ukim.finki.das.ta.service.TechnicalAnalysisService;
import org.springframework.stereotype.Service;
import org.ta4j.core.BarSeries;
import org.ta4j.core.BaseBarSeriesBuilder;
import org.ta4j.core.indicators.*;
import org.ta4j.core.indicators.adx.ADXIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsLowerIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsMiddleIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsUpperIndicator;
import org.ta4j.core.indicators.helpers.ClosePriceIndicator;
import org.ta4j.core.indicators.helpers.VolumeIndicator;
import org.ta4j.core.indicators.statistics.StandardDeviationIndicator;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.List;

@Service
public class TechnicalAnalysisServiceImpl implements TechnicalAnalysisService {

    private final HistoricalDataRepository historicalDataRepository;

    public TechnicalAnalysisServiceImpl(HistoricalDataRepository repo) {
        this.historicalDataRepository = repo;
    }

    @Override
    public TechnicalAnalysisResult analyze(String symbol) {

        List<Record> history =
                historicalDataRepository.findBySymbolOrderByDateAsc(symbol);

        if (history == null || history.size() < 30) {
            throw new InsufficientDataException(
                    "Not enough historical data to perform technical analysis."
            );
        }

        TechnicalAnalysisResult result = new TechnicalAnalysisResult();

        // Series
        BarSeries dailySeries = buildDailySeries(history, symbol);
        BarSeries weeklySeries = aggregateSeries(history, symbol + "_W", 7);
        BarSeries monthlySeries = aggregateSeries(history, symbol + "_M", 30);

        // Daily
        FrameIndicators daily = computeIndicatorsForSeries(dailySeries);
        validateIndicators(daily, "daily");

        result.setDailyIndicators(daily);

        double lastClose = lastClose(dailySeries);

        TimeframeSignal dailyOsc = evaluateOscillators(daily);
        TimeframeSignal dailyMa = evaluateMovingAverages(daily, lastClose(dailySeries));
        TimeframeSignal dailySum = buildSummary(dailyOsc, dailyMa, daily, lastClose);

        result.setDailyOscillators(dailyOsc);
        result.setDailyMovingAverages(dailyMa);
        result.setDailySummary(dailySum);

        // Weekly
        FrameIndicators weekly = computeIndicatorsForSeries(weeklySeries);
        validateIndicators(weekly, "weekly");

        result.setWeeklyIndicators(weekly);

        double weeklyLastClose = lastClose(weeklySeries);

        TimeframeSignal weeklyOsc = evaluateOscillators(weekly);
        TimeframeSignal weeklyMa = evaluateMovingAverages(weekly, lastClose(weeklySeries));
        TimeframeSignal weeklySum = buildSummary(weeklyOsc, weeklyMa, weekly, weeklyLastClose);

        result.setWeeklyOscillators(weeklyOsc);
        result.setWeeklyMovingAverages(weeklyMa);
        result.setWeeklySummary(weeklySum);

        // Monthly
        FrameIndicators monthly = computeIndicatorsForSeries(monthlySeries);
        validateIndicators(monthly, "monthly");

        result.setMonthlyIndicators(monthly);

        double monthlyLastClose = lastClose(monthlySeries);

        TimeframeSignal monthlyOsc = evaluateOscillators(monthly);
        TimeframeSignal monthlyMa = evaluateMovingAverages(monthly, lastClose(monthlySeries));
        TimeframeSignal monthlySum = buildSummary(monthlyOsc, monthlyMa, monthly, monthlyLastClose);

        result.setMonthlyOscillators(monthlyOsc);
        result.setMonthlyMovingAverages(monthlyMa);
        result.setMonthlySummary(monthlySum);

        result.setDailyIndicatorDetails(
                buildIndicatorTable(daily, lastClose)
        );

        result.setWeeklyIndicatorDetails(
                buildIndicatorTable(weekly, weeklyLastClose)
        );

        result.setMonthlyIndicatorDetails(
                buildIndicatorTable(monthly, monthlyLastClose)
        );

        return result;
    }

    // Series builders

    private BarSeries buildDailySeries(List<Record> history, String symbol) {
        BarSeries series = new BaseBarSeriesBuilder()
                .withName(symbol + "_D")
                .build();

        for (Record r : history) {
            ZonedDateTime zdt =
                    r.getDate().atStartOfDay(ZoneId.systemDefault());

            series.addBar(
                    zdt,
                    r.getOpen(),
                    r.getHigh(),
                    r.getLow(),
                    r.getClose(),
                    r.getVolumeTo() != null ? r.getVolumeTo() : 0.0
            );
        }
        return series;
    }

    private BarSeries aggregateSeries(List<Record> history, String name, int window) {
        BarSeries series = new BaseBarSeriesBuilder().withName(name).build();

        for (int i = 0; i < history.size(); i += window) {
            int end = Math.min(i + window, history.size()) - 1;

            Record first = history.get(i);
            Record last = history.get(end);

            double open = first.getOpen();
            double close = last.getClose();

            double high = history.subList(i, end + 1).stream()
                    .mapToDouble(r -> r.getHigh() != null ? r.getHigh() : open)
                    .max().orElse(open);

            double low = history.subList(i, end + 1).stream()
                    .mapToDouble(r -> r.getLow() != null ? r.getLow() : open)
                    .min().orElse(open);

            double volume = history.subList(i, end + 1).stream()
                    .mapToDouble(r -> r.getVolumeTo() != null ? r.getVolumeTo() : 0)
                    .sum();

            series.addBar(
                    last.getDate().atStartOfDay(ZoneId.systemDefault()),
                    open, high, low, close, volume
            );
        }
        return series;
    }

    // Indicators (values only)

    private FrameIndicators computeIndicatorsForSeries(BarSeries series) {

        if (series == null || series.getBarCount() < 20) {
            throw new InsufficientDataException(
                    "Not enough data to compute technical indicators."
            );
        }

        FrameIndicators fi = new FrameIndicators();

        ClosePriceIndicator close = new ClosePriceIndicator(series);
        VolumeIndicator volume = new VolumeIndicator(series);
        int i = series.getEndIndex();

        fi.setRsi(new RSIIndicator(close, 14).getValue(i).doubleValue());
        fi.setMacd(new MACDIndicator(close, 12, 26).getValue(i).doubleValue());
        fi.setStoch(new StochasticOscillatorKIndicator(series, 14).getValue(i).doubleValue());
        fi.setAdx(new ADXIndicator(series, 14).getValue(i).doubleValue());
        fi.setCci(new CCIIndicator(series, 20).getValue(i).doubleValue());

        ROCIndicator momentum = new ROCIndicator(close, 10);
        fi.setMomentum(momentum.getValue(i).doubleValue());

        fi.setSma(new SMAIndicator(close, 20).getValue(i).doubleValue());
        fi.setEma(new EMAIndicator(close, 20).getValue(i).doubleValue());
        fi.setWma(new WMAIndicator(close, 20).getValue(i).doubleValue());

        fi.setSmaShort(new SMAIndicator(close, 10).getValue(i).doubleValue());
        fi.setEmaShort(new EMAIndicator(close, 10).getValue(i).doubleValue());

        StandardDeviationIndicator sd = new StandardDeviationIndicator(close, 20);
        BollingerBandsMiddleIndicator bbm =
                new BollingerBandsMiddleIndicator(new SMAIndicator(close, 20));

        fi.setBollingerUpper(
                new BollingerBandsUpperIndicator(bbm, sd).getValue(i).doubleValue()
        );
        fi.setBollingerLower(
                new BollingerBandsLowerIndicator(bbm, sd).getValue(i).doubleValue()
        );


        return fi;
    }

    // Validation

    private void validateIndicators(FrameIndicators fi, String tf) {
        if (fi.getRsi() == null || fi.getSma() == null || fi.getEma() == null) {
            throw new InsufficientDataException(
                    "Not enough data to evaluate " + tf + " technical indicators."
            );
        }
    }

    // Signal evaluation

    private TimeframeSignal evaluateOscillators(FrameIndicators fi) {
        return buildSignal(List.of(
                rsiSignal(fi.getRsi()),
                macdSignal(fi.getMacd()),
                stochasticSignal(fi.getStoch()),
                cciSignal(fi.getCci()),
                momentumSignal(fi.getMomentum())
        ));
    }

    private TimeframeSignal evaluateMovingAverages(FrameIndicators fi, double lastClose) {
        return buildSignal(List.of(
                maSignal(lastClose, fi.getSma()),
                maSignal(lastClose, fi.getEma()),
                maSignal(lastClose, fi.getWma()),
                maSignal(lastClose, fi.getSmaShort()),
                maSignal(lastClose, fi.getEmaShort())
        ));
    }

    private TimeframeSignal buildFromCounts(int buy, int sell, int neutral) {
        TaSignal summary;
        if (buy > sell && buy > neutral) {
            summary = TaSignal.BUY;
        } else if (sell > buy && sell > neutral) {
            summary = TaSignal.SELL;
        } else {
            summary = TaSignal.NEUTRAL;
        }

        SignalStats stats = new SignalStats();
        stats.setBuy(buy);
        stats.setSell(sell);
        stats.setNeutral(neutral);

        TimeframeSignal tf = new TimeframeSignal();
        tf.setSignal(summary);
        tf.setStats(stats);

        return tf;
    }

    private TimeframeSignal buildSummary(
            TimeframeSignal osc,
            TimeframeSignal ma,
            FrameIndicators fi,
            double lastClose
    ) {

        int buy = osc.getStats().getBuy() + ma.getStats().getBuy();
        int sell = osc.getStats().getSell() + ma.getStats().getSell();
        int neutral = osc.getStats().getNeutral() + ma.getStats().getNeutral();

        TimeframeSignal base = buildFromCounts(buy, sell, neutral);
        TaSignal baseSignal = base.getSignal();

        TaSignal finalSignal = baseSignal;
        String reason = "NONE";

        boolean strongTrend = isStrongTrend(fi.getAdx());
        TaSignal bbSignal =
                bollingerSignal(lastClose, fi.getBollingerUpper(), fi.getBollingerLower());

        // ADX filter
        if (!strongTrend && finalSignal != TaSignal.NEUTRAL) {
            finalSignal = TaSignal.NEUTRAL;
            reason = "ADX filter (weak trend)";
        }

        // Bollinger override
        if (bbSignal != TaSignal.NEUTRAL && bbSignal != finalSignal) {
            finalSignal = TaSignal.NEUTRAL;
            reason = "Bollinger Bands conflict";
        }

        base.setBaseSignal(baseSignal);
        base.setSignal(finalSignal);
        base.setFilterReason(reason);

        return base;
    }

    private TimeframeSignal buildSignal(List<TaSignal> signals) {

        int buy = (int) signals.stream().filter(s -> s == TaSignal.BUY).count();
        int sell = (int) signals.stream().filter(s -> s == TaSignal.SELL).count();
        int neutral = signals.size() - buy - sell;

        return buildFromCounts(buy, sell, neutral);
    }

    private List<IndicatorRow> buildIndicatorTable(FrameIndicators fi, double lastClose) {

        return List.of(
                // Oscillators
                new IndicatorRow("RSI (14)", fi.getRsi(), rsiSignal(fi.getRsi())),
                new IndicatorRow("MACD (12,26)", fi.getMacd(), macdSignal(fi.getMacd())),
                new IndicatorRow("Stochastic %K (14)", fi.getStoch(), stochasticSignal(fi.getStoch())),
                new IndicatorRow("CCI (20)", fi.getCci(), cciSignal(fi.getCci())),
                new IndicatorRow("Momentum (10)", fi.getMomentum(), momentumSignal(fi.getMomentum())),

                // Moving Averages
                new IndicatorRow("SMA (20)", fi.getSma(), maSignal(lastClose, fi.getSma())),
                new IndicatorRow("EMA (20)", fi.getEma(), maSignal(lastClose, fi.getEma())),
                new IndicatorRow("WMA (20)", fi.getWma(), maSignal(lastClose, fi.getWma())),
                new IndicatorRow("SMA (10)", fi.getSmaShort(), maSignal(lastClose, fi.getSmaShort())),
                new IndicatorRow("EMA (10)", fi.getEmaShort(), maSignal(lastClose, fi.getEmaShort()))
        );
    }

    // Signal rules

    private TaSignal rsiSignal(double v) {
        if (v < 30) return TaSignal.BUY;
        if (v > 70) return TaSignal.SELL;
        return TaSignal.NEUTRAL;
    }

    private TaSignal macdSignal(double v) {
        if (v > 0) return TaSignal.BUY;
        if (v < 0) return TaSignal.SELL;
        return TaSignal.NEUTRAL;
    }

    private TaSignal stochasticSignal(double v) {
        if (v < 20) return TaSignal.BUY;
        if (v > 80) return TaSignal.SELL;
        return TaSignal.NEUTRAL;
    }

    private TaSignal cciSignal(double v) {
        if (v < -100) return TaSignal.BUY;
        if (v > 100) return TaSignal.SELL;
        return TaSignal.NEUTRAL;
    }

    private TaSignal maSignal(double close, double ma) {
        if (close > ma) return TaSignal.BUY;
        if (close < ma) return TaSignal.SELL;
        return TaSignal.NEUTRAL;
    }

    private boolean isStrongTrend(double adx) {
        return adx >= 25;
    }

    private TaSignal bollingerSignal(double close, double upper, double lower) {
        if (close < lower) return TaSignal.BUY;
        if (close > upper) return TaSignal.SELL;
        return TaSignal.NEUTRAL;
    }

    private TaSignal momentumSignal(double v) {
        if (v > 0) return TaSignal.BUY;
        if (v < 0) return TaSignal.SELL;
        return TaSignal.NEUTRAL;
    }

    private double lastClose(BarSeries series) {
        return series.getLastBar().getClosePrice().doubleValue();
    }
}
