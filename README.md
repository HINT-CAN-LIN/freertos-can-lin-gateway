<div align="center">

# FreeRTOS CAN-LIN Gateway Project

**FreeRTOS-based CAN-LIN Gateway for multi-ECU vehicle network**
** **

STM32 + FreeRTOS 분산 ECU · CAN FD Backbone · LIN Subnetwork · Motor/Steering

![Team](https://img.shields.io/badge/TEAM-7_MEMBERS-334155?style=flat-square)
![RTOS](https://img.shields.io/badge/MCU_RTOS-FreeRTOS-0A7A3F?style=flat-square)
![Backbone](https://img.shields.io/badge/BACKBONE-CAN_FD-0F766E?style=flat-square)
![LIN](https://img.shields.io/badge/LOCAL_BUS-LIN-0891B2?style=flat-square)
![RTOS](https://img.shields.io/badge/MCU_RTOS-FreeRTOS-0A7A3F?style=flat-square)

[프로젝트 개요](#1-프로젝트-개요) · [전체 아키텍처](#2-전체-아키텍처) · [RTOS 구조](#3-rtos-구조) · [7인 역할](#4-7인-역할) · [개발 문서](#5-개발-문서)

</div>

> **현재 기준:** 
> **핵심 구조:**
> **MCU 실행 환경:** 가능한 STM32 Node는 **FreeRTOS + CMSIS-RTOS2**를 기본으로 설계한다.    

본 프로젝트는 ~~~ 프로젝트다.

***
# :black_circle: TEAM '77CAN터키'
7월에 만난 7명이 CAN 통신 프로젝트를 통해 함께 성장할 터전을 만들고, 실력을 키운다.
| 박준호 | 성대훈 | 권도형 | 김민서 | 김호연 | 박예준 | 전우관 |
|--------|--------|--------|--------|--------|--------|--------|
| <img src="https://github.githubassets.com/images/icons/emoji/unicode/1f468-1f4bb.png?v8" width="100"/> | <img src="https://github.com/user-attachments/assets/23e22012-ae25-477c-8db2-0442cf3f67cc" width="100"/> | <img src="https://github.com/user-attachments/assets/67315a0e-d258-4b18-9ec0-ddc84fac7f37" width="100"/> | <img src="https://github.githubassets.com/images/icons/emoji/unicode/1f469-1f4bb.png?v8" width="100"/> | <img src="https://github.com/user-attachments/assets/3534a4f8-a71d-464e-a9cb-9b8a2ebc3532" width="100"/> | <img src="https://github.com/user-attachments/assets/3534a4f8-a71d-464e-a9cb-9b8a2ebc3532" width="100"/> | <img src="https://github.com/user-attachments/assets/3534a4f8-a71d-464e-a9cb-9b8a2ebc3532" width="100"/> |
| [깃허브](https://github.com/officialboyy) | [깃허브](https://github.com/daehoon0917) | [깃허브](https://github.com/Kwondoryeong) | [깃허브](https://github.com/gnim370717-bot) | [깃허브](https://github.com/Kimoyeon) | [깃허브](https://github.com/suuply) | [깃허브](https://github.com/jwk29134)
***

### 협업 규칙
1. 개발환경(버전, 경로 등) 동일
2. 오류 수정 안 된 코드 절대 Commit/Push 금지
3. Chat GPT 코드 복붙 금지
4. 다른 사람이 짠 코드 맘대로 수정 금지
5. conflict 발생시 - 충돌 난 코드 작업한 사람 불러서 같이 충돌 잡고 merge 할 것
6. syntax 에러 등 코드 오류 이외의 문제 발생 시 → 반드시 질문-및-이슈 채널에 적어놓을 것 (추후 트러블슈팅 내용에 포함시켜야함) 중요

### 코드 컨벤션
1. 스네이크 표기법으로 변수명, 함수명 작성
예시) int input_num = 10;
int send_message(){};

### 깃 컨벤션
1. 커밋메시지
- 기능 개발 시 - [feat] 기능명(영문) - 예시) [feat] login, 설명란에 개발한 기능 간략 설명 추가
- 수정 시 - [fix] 기능명(영문) - 예시) [fix] chat, 설명란에 수정 내용 추가

2. 본인이 작업한 코드 간단하게 설명하는 주석 반드시 달기

- 예시
```
// 회원정보 조회
void show_userdata(auto user){
    // 회원명 출력
    cout << user.name << endl;
}
```

# 1. 프로젝트 개요

---

# 2. 전체 아키텍처

---

# 3. RTOS 구조

---

# 4. 7인 역할

---

# 5. 개발 문서

---

