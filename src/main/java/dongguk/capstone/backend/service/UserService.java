package dongguk.capstone.backend.service;

import dongguk.capstone.backend.domain.Account;
import dongguk.capstone.backend.domain.Card;
import dongguk.capstone.backend.repository.AccountRepository;
import dongguk.capstone.backend.repository.CardRepository;
import dongguk.capstone.backend.userdto.LoginRequestDTO;
import dongguk.capstone.backend.userdto.LoginResponseDTO;
import dongguk.capstone.backend.userdto.SignupRequestDTO;
import dongguk.capstone.backend.repository.UserRepository;
import dongguk.capstone.backend.domain.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
@RequiredArgsConstructor
@Transactional // JPA를 사용할 때는 모든 작업을 트랜잭션 안에서 실행해야 하므로 @Transactional 애노테이션 추가 (주로 서비스 계층에서 작업이 이루어지므로, 서비스에 추가하는 것)
public class UserService {

    private final UserRepository userRepository;
    private final AccountRepository accountRepository;
    private final CardRepository cardRepository;

    /**
     * 회원 가입 로직
     * @param signupRequestDTO
     * @return
     */
    // DTO로 얻은 데이터 값들을 Entity로 전달하는 작업은 비즈니스 로직이므로 Service에서 이루어짐.
    public User save(SignupRequestDTO signupRequestDTO) { // 여기서 DTO가 아니라 user를 해야될 듯
        User user = new User();
        // 근데 여기에 if문으로 조건이 붙어야 되지 않을까? 예를 들어 이메일 확인 되면 이 밑에 애들이 진행되게끔..!
        user.setNickname(signupRequestDTO.getNickname());
        user.setEmail(signupRequestDTO.getEmail());
        user.setPassword(signupRequestDTO.getPassword());
        user.setMajor(signupRequestDTO.getMajor());
        user.setGrade(signupRequestDTO.getGrade());
        user.setGender(signupRequestDTO.getGender());
        user.setIncomeBracket(signupRequestDTO.getIncome_bracket());
        user.setScholarshipStatus(signupRequestDTO.getScholarship_status());
        user.setDistrict(signupRequestDTO.getDistrict());
        user.setAccountStatus(0); // 회원가입 시에는 계좌가 등록되어 있지 않은 상태이므로 0
        user.setCardStatus(0); // 회원가입 시에는 카드가 등록되어 있지 않은 상태이므로 0
        userRepository.save(user);
        // if문 여기까지
        // 이메일 확인이 잘못되는 등 잘못된 것이 있으면 여기에 else로 처리
        // 그리고 뭐 하나라도 입력 안했을 때도 처리해야 됨!!!!

        return user;
    }

    /**
     * 로그인 로직
     * @param loginRequestDTO
     * @return
     */
    public LoginResponseDTO login(LoginRequestDTO loginRequestDTO) {
        Optional<User> user = userRepository.findByEmail(loginRequestDTO.getEmail());

        if (user.isPresent()) {
            if (loginRequestDTO.getPassword().equals(user.get().getPassword())) { // 입력한 비밀번호가 이메일에 대응되는 비밀번호와 맞을 경우
                Long userId = user.get().getUser_id();

                // Account와 Card 확인
                Optional<Account> account = accountRepository.findByUserId(userId);
                Optional<Card> card = cardRepository.findByUserId(userId);

                user.get().setAccountStatus(account.isPresent()? 1 : 0);
                user.get().setCardStatus(card.isPresent()? 1 : 0);
                userRepository.save(user.get()); // 상태 업데이트 후 저장
                if(account.isPresent() && card.isPresent()){ // 계좌와 카드 등록을 이미 했을 경우
                    return new LoginResponseDTO(1, userId, user.get().getNickname(), user.get().getAccountStatus(), user.get().getCardStatus(), account.get().getAccountEmbedded().getBankAccountNum());
                } else { // 계좌와 카드 등록이 안되어 있을 경우
                    return new LoginResponseDTO(1, userId, user.get().getNickname(), user.get().getAccountStatus(), user.get().getCardStatus(), null);
                }
            } else { // 비밀번호가 틀렸을 경우
                return new LoginResponseDTO(0, null, null, 0, 0, null);
            }
        } else { // 이메일이 틀렸을 경우
            return new LoginResponseDTO(0, null, null, 0, 0, null);
        }
    }
}
