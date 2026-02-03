package mk.ukim.finki.das.app.web;

import mk.ukim.finki.das.app.model.dto.InsightsViewModel;
import mk.ukim.finki.das.app.model.dto.lstm.PredictionResponse;
import mk.ukim.finki.das.app.model.entity.Coin;
import mk.ukim.finki.das.app.model.enums.TrainingStatus;
import mk.ukim.finki.das.app.model.exceptions.LstmTrainingException;
import mk.ukim.finki.das.app.service.CryptoService;
import mk.ukim.finki.das.app.service.LstmService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Controller
public class CryptoController {

    private final CryptoService cryptoService;
    private final LstmService lstmService;


    public CryptoController(CryptoService cryptoService, LstmService lstmService) {
        this.cryptoService = cryptoService;
        this.lstmService = lstmService;
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

        PredictionResponse prediction = null;
        TrainingStatus lstmStatus = lstmService.getStatus(symbol);

        if (lstmStatus == TrainingStatus.DONE) {
            try {
                prediction = lstmService.getPrediction(symbol);
            } catch (LstmTrainingException ignored) {
            }
        }

        model.addAttribute("prediction", prediction);

        if (prediction != null && prediction.getPrediction_date() != null) {
            LocalDate date = LocalDate.parse(prediction.getPrediction_date());

            DateTimeFormatter fmt =
                    DateTimeFormatter.ofPattern("MMM dd, yyyy", Locale.ENGLISH);

            String formattedDate = date.format(fmt);

            model.addAttribute("tomorrowDate", formattedDate);
        }

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
    public String predictTomorrow(@RequestParam String symbol) {

        lstmService.startTraining(symbol);

        return "redirect:/insights?symbol=" + symbol + "&tab=chart";
    }

    @GetMapping("/api/predict/{symbol}")
    @ResponseBody
    public ResponseEntity<?> getPrediction(@PathVariable String symbol) {

        try {
            PredictionResponse prediction = lstmService.getPrediction(symbol);
            return ResponseEntity.ok(prediction);

        } catch (LstmTrainingException ex) {

            if (ex.getStatus() == TrainingStatus.FAILED) {
                return ResponseEntity
                        .status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("status", "FAILED"));
            }

            if (ex.getStatus() == TrainingStatus.ERROR) {
                return ResponseEntity
                        .status(HttpStatus.SERVICE_UNAVAILABLE)
                        .body(Map.of("status", "ERROR"));
            }

            return ResponseEntity
                    .status(HttpStatus.ACCEPTED)
                    .body(Map.of("status", "RUNNING"));

        }
    }

    @GetMapping("/api/predict/{symbol}/status")
    @ResponseBody
    public Map<String, String> getPredictionStatus(@PathVariable String symbol) {

        TrainingStatus status = lstmService.getStatus(symbol);

        return Map.of("status", status.name());
    }


}