package dongguk.capstone.backend.repository;

import dongguk.capstone.backend.domain.Schedule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ScheduleRepository extends JpaRepository<Schedule, Long> {

    Long findMaxScheduleIdByUser_Id(Long userId);

    List<Schedule> findByScheduleEmbeddedUserId(Long userId);

    @Query("SELECT MAX(s.scheduleEmbedded.id) FROM Schedule s WHERE s.user.id = :userId")
    Long findMaxScheduleIdByUserId(@Param("userId") Long userId);
}
