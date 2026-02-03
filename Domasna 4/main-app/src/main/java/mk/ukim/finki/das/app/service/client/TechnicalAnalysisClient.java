package mk.ukim.finki.das.app.service.client;

import mk.ukim.finki.das.app.model.dto.technical.TechnicalAnalysisResult;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

@Service
public class TechnicalAnalysisClient {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${technical.service.url}")
    private String technicalServiceUrl;

    public TechnicalAnalysisResult analyze(String symbol) {

        String url = technicalServiceUrl +
                "/api/technical/analyze?symbol=" + symbol;

        try {
            return restTemplate.getForObject(url, TechnicalAnalysisResult.class);
        } catch (HttpClientErrorException ex) {
            throw new RuntimeException(ex.getResponseBodyAsString());
        }
    }
}
