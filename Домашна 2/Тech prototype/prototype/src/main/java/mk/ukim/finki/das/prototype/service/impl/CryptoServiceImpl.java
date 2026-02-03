package mk.ukim.finki.das.prototype.service.impl;

import mk.ukim.finki.das.prototype.dto.InsightsViewModel;
import mk.ukim.finki.das.prototype.model.Coin;
import mk.ukim.finki.das.prototype.model.Record;
import mk.ukim.finki.das.prototype.repository.CoinRepository;
import mk.ukim.finki.das.prototype.repository.HistoricalDataRepository;
import mk.ukim.finki.das.prototype.service.CryptoService;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

@Service
public class CryptoServiceImpl implements CryptoService {

    private final CoinRepository coinRepository;
    private final HistoricalDataRepository historicalDataRepository;

    public CryptoServiceImpl(CoinRepository coinRepository,
                             HistoricalDataRepository historicalDataRepository) {
        this.coinRepository = coinRepository;
        this.historicalDataRepository = historicalDataRepository;
    }

    @Override
    public List<Coin> getAllCoins() {
        return coinRepository.findAll();
    }

    @Override
    public List<Record> getWeeklyData(String symbol) {
        return historicalDataRepository
                .findTop7BySymbolOrderByDateDesc(symbol);
    }

    @Override
    public List<Record> getHistoryForChart(String symbol) {
        return historicalDataRepository.findBySymbolOrderByDateAsc(symbol);
    }

    @Override
    public InsightsViewModel getInsights(String symbol) {
        List<Record> weekly = getWeeklyData(symbol);
        List<Record> history = getHistoryForChart(symbol);

        List<String> dates = history.stream()
                .map(h -> h.getDate().toString())
                .toList();

        List<Double> closePrices = history.stream()
                .map(Record::getClose)
                .toList();

        DateTimeFormatter formatter =
                DateTimeFormatter.ofPattern("MMM dd, yyyy", Locale.ENGLISH);

        String periodStart = history.isEmpty()
                ? ""
                : history.get(0).getDate().format(formatter);

        String periodEnd = history.isEmpty()
                ? ""
                : history.get(history.size() - 1).getDate().format(formatter);

        InsightsViewModel vm = new InsightsViewModel();
        vm.setSymbol(symbol);
        vm.setWeeklyData(weekly);
        vm.setHistoryData(history);
        vm.setDates(dates);
        vm.setClosePrices(closePrices);
        vm.setPeriodStart(periodStart);
        vm.setPeriodEnd(periodEnd);

        return vm;
    }

}
