package mk.ukim.finki.das.prototype.web;

import mk.ukim.finki.das.prototype.dto.InsightsViewModel;
import mk.ukim.finki.das.prototype.model.Coin;
import mk.ukim.finki.das.prototype.model.Record;
import mk.ukim.finki.das.prototype.service.CryptoService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

@Controller
public class CryptoController {

    private final CryptoService cryptoService;

    public CryptoController(CryptoService cryptoService) {
        this.cryptoService = cryptoService;
    }


    @GetMapping({"/", "/coins"})
    public String showCoins(Model model) {
        List<Coin> coins = cryptoService.getAllCoins();
        model.addAttribute("coins", coins);

        model.addAttribute("activePage", "coins");
        model.addAttribute("pageTitle", "Crypto App - Market Coins");
        model.addAttribute("bodyContent", "coins");

        return "master-template";
    }


    @GetMapping("/insights")
    public String showInsights(@RequestParam String symbol,
                               @RequestParam(defaultValue = "table") String tab,
                               Model model) {

        List<Coin> coins = cryptoService.getAllCoins();
        InsightsViewModel insights = cryptoService.getInsights(symbol);

        model.addAttribute("coins", coins);
        model.addAttribute("selectedSymbol", symbol);
        model.addAttribute("weeklyData", insights.getWeeklyData());
        model.addAttribute("historyData", insights.getHistoryData());
        model.addAttribute("dates", insights.getDates());
        model.addAttribute("closePrices", insights.getClosePrices());
        model.addAttribute("periodStart", insights.getPeriodStart());
        model.addAttribute("periodEnd", insights.getPeriodEnd());
        model.addAttribute("tab", tab);

        model.addAttribute("activePage", "insights");
        model.addAttribute("pageTitle", "Crypto App - " + symbol);
        model.addAttribute("bodyContent", "insights");

        return "master-template";
    }
}
