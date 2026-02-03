package mk.ukim.finki.das.app.web.api;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/api")
public class SentimentProxyController {

    private final RestTemplate restTemplate;

    @Value("${sentiment.service.url}")
    private String sentimentServiceUrl;

    public SentimentProxyController(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @GetMapping("/analyze/{symbol}")
    public ResponseEntity<String> analyze(@PathVariable String symbol) {
        String url = sentimentServiceUrl + "/api/analyze/" + symbol;
        try {
            return restTemplate.getForEntity(url, String.class);

        } catch (Exception ex) {
            return ResponseEntity
                    .status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body("""
                                {
                                  "error": "Sentiment service is temporarily unavailable"
                                }
                            """);
        }
    }
}
