package mk.ukim.finki.das.prototype.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import mk.ukim.finki.das.prototype.model.entity.Record;

import java.util.List;

public interface HistoricalDataRepository extends JpaRepository<Record, Long> {

    List<Record> findTop7BySymbolOrderByDateDesc(String symbol);

    List<Record> findBySymbolOrderByDateAsc(String symbol);
}
