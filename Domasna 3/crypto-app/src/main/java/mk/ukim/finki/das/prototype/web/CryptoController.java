package mk.ukim.finki.das.prototype.web;

import mk.ukim.finki.das.prototype.model.dto.InsightsViewModel;
import mk.ukim.finki.das.prototype.model.exceptions.LstmTrainingException;
import mk.ukim.finki.das.prototype.model.sentiment_onchain.SentimentOnChain;
import mk.ukim.finki.das.prototype.model.entity.Coin;
import mk.ukim.finki.das.prototype.model.entity.Prediction;
import mk.ukim.finki.das.prototype.service.CryptoService;
import mk.ukim.finki.das.prototype.service.LstmService;
import mk.ukim.finki.das.prototype.service.SentimentOnChainService;
import mk.ukim.finki.das.prototype.service.TechnicalAnalysisService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

@Controller
public class CryptoController {

    private final CryptoService cryptoService;
    private final LstmService lstmService;
    private final SentimentOnChainService sentimentOnChainService;


    public CryptoController(CryptoService cryptoService, LstmService lstmService, SentimentOnChainService sentimentOnChainService, TechnicalAnalysisService technicalAnalysisService) {
        this.cryptoService = cryptoService;
        this.lstmService = lstmService;
        this.sentimentOnChainService = sentimentOnChainService;
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
                               @RequestParam(defaultValue = "1D") String tf,
                               Model model) {

        List<Coin> coins = cryptoService.getAllCoins();
        InsightsViewModel insights = cryptoService.getInsights(symbol);
//        Prediction prediction = lstmService.getLatestPrediction(symbol);

        model.addAttribute("coins", coins);
        model.addAttribute("selectedSymbol", symbol);
        model.addAttribute("weeklyData", insights.getWeeklyData());
        model.addAttribute("historyData", insights.getHistoryData());
        model.addAttribute("dates", insights.getDates());
        model.addAttribute("closePrices", insights.getClosePrices());
        model.addAttribute("periodStart", insights.getPeriodStart());
        model.addAttribute("periodEnd", insights.getPeriodEnd());
        model.addAttribute("tab", tab);

        model.addAttribute("technical", insights.getTechnical());
        model.addAttribute("tf", tf);
        model.addAttribute("technicalError", insights.getTechnicalError());

        model.addAttribute("activePage", "insights");
        model.addAttribute("pageTitle", "Crypto App - " + symbol);
        model.addAttribute("bodyContent", "insights");

        return "master-template";
    }

    @PostMapping("/insights/predict")
    public String predictTomorrow(@RequestParam String symbol,
                                  RedirectAttributes redirectAttributes) {

        redirectAttributes.addFlashAttribute("lstmMessage",
                "Generating prediction... Please wait.");
        try {
            Prediction result = lstmService.runTraining(symbol);

            redirectAttributes.addFlashAttribute("prediction", result);
            redirectAttributes.addFlashAttribute("lstmMessage",
                    "");

            DateTimeFormatter fmt = DateTimeFormatter.ofPattern("MMM dd, yyyy", Locale.ENGLISH);
            String formattedDate = result.getPredictionDate().format(fmt);
            redirectAttributes.addFlashAttribute("tomorrowDate", formattedDate);
        } catch (LstmTrainingException ex) {
            redirectAttributes.addFlashAttribute(
                    "lstmMessage",
                    ex.getMessage()
            );

            redirectAttributes.addFlashAttribute("prediction", null);
        }

        return "redirect:/insights?symbol=" + symbol + "&tab=chart";
    }

    @GetMapping("/analysis/sentiment-onchain/{symbol}")
    public String sentimentOnChain(
            @PathVariable String symbol,
            Model model) {

        SentimentOnChain dto = sentimentOnChainService.analyze(symbol);

        model.addAttribute("sentiment", dto.sentiment);
        model.addAttribute("onchain", dto.onchain);
        model.addAttribute("combined", dto.combined);

        return "insights";
    }


}
