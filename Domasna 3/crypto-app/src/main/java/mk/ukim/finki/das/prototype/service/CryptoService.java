package mk.ukim.finki.das.prototype.service;

import mk.ukim.finki.das.prototype.model.dto.InsightsViewModel;
import mk.ukim.finki.das.prototype.model.entity.Coin;
import mk.ukim.finki.das.prototype.model.entity.Record;

import java.util.List;

public interface CryptoService {
    List<Coin> getAllCoins();

    List<Record> getWeeklyData(String symbol);

    List<Record> getHistoryForChart(String symbol);

    InsightsViewModel getInsights(String symbol);
}

