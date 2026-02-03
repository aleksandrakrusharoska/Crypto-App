package mk.ukim.finki.das.prototype.repository;

import mk.ukim.finki.das.prototype.model.entity.Prediction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.Optional;

public interface LstmPredictionRepository extends JpaRepository<Prediction, Long> {

    Optional<Prediction> findFirstBySymbolOrderByPredictionDateDesc(String symbol);

    Optional<Prediction> findBySymbolAndPredictionDate(String symbol, LocalDate predictionDate);
}
