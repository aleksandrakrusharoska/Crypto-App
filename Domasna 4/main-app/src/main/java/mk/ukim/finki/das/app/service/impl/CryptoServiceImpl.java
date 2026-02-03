package mk.ukim.finki.das.app.service.impl;

import mk.ukim.finki.das.app.model.dto.InsightsViewModel;
import mk.ukim.finki.das.app.model.dto.technical.TechnicalAnalysisResult;
import mk.ukim.finki.das.app.model.entity.Coin;
import mk.ukim.finki.das.app.model.entity.Record;
import mk.ukim.finki.das.app.repository.CoinRepository;
import mk.ukim.finki.das.app.repository.HistoricalDataRepository;
import mk.ukim.finki.das.app.service.CryptoService;
import mk.ukim.finki.das.app.service.client.TechnicalAnalysisClient;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

@Service
public class CryptoServiceImpl implements CryptoService {

    private final CoinRepository coinRepository;
    private final HistoricalDataRepository historicalDataRepository;
    private final TechnicalAnalysisClient technicalAnalysisClient;

    public CryptoServiceImpl(CoinRepository coinRepository,
                             HistoricalDataRepository historicalDataRepository, TechnicalAnalysisClient technicalAnalysisClient) {
        this.coinRepository = coinRepository;
        this.historicalDataRepository = historicalDataRepository;
        this.technicalAnalysisClient = technicalAnalysisClient;
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
                : history.getFirst().getDate().format(formatter);

        String periodEnd = history.isEmpty()
                ? ""
                : history.getLast().getDate().format(formatter);

        InsightsViewModel vm = new InsightsViewModel();
        vm.setSymbol(symbol);
        vm.setWeeklyData(weekly);
        vm.setHistoryData(history);
        vm.setDates(dates);
        vm.setClosePrices(closePrices);
        vm.setPeriodStart(periodStart);
        vm.setPeriodEnd(periodEnd);

        try {
            TechnicalAnalysisResult ta =
                    technicalAnalysisClient.analyze(symbol);
            vm.setTechnical(ta);
            vm.setTechnicalError(null);
        } catch (RuntimeException ex) {
            vm.setTechnical(null);
            vm.setTechnicalError(ex.getMessage());
        }


        return vm;
    }

}
