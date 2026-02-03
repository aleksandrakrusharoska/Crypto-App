package mk.ukim.finki.das.ta.repository;

import mk.ukim.finki.das.ta.model.entity.Record;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface HistoricalDataRepository extends JpaRepository<Record, Long> {
    List<Record> findBySymbolOrderByDateAsc(String symbol);
}
