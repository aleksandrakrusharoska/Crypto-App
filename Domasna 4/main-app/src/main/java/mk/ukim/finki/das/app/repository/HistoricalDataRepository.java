package mk.ukim.finki.das.app.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import mk.ukim.finki.das.app.model.entity.Record;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface HistoricalDataRepository extends JpaRepository<Record, Long> {

    List<Record> findTop7BySymbolOrderByDateDesc(String symbol);

    List<Record> findBySymbolOrderByDateAsc(String symbol);
}
