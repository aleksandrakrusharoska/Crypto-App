package mk.ukim.finki.das.app.repository;

import mk.ukim.finki.das.app.model.entity.Coin;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CoinRepository extends JpaRepository<Coin, String> {
}
