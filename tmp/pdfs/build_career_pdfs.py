from pathlib import Path
from html import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf'
pdfmetrics.registerFont(TTFont('Malgun', 'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold', 'C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('Malgun', normal='Malgun', bold='MalgunBold', italic='Malgun', boldItalic='MalgunBold')
NAVY = colors.HexColor('#132C46')
TEAL = colors.HexColor('#087F87')
GRAY = colors.HexColor('#526476')
LIGHT = colors.HexColor('#EFF5F8')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleK', fontName='MalgunBold', fontSize=25, leading=35, textColor=NAVY, spaceAfter=14, wordWrap='CJK'))
styles.add(ParagraphStyle(name='SubK', fontName='Malgun', fontSize=10.5, leading=17, textColor=GRAY, spaceAfter=16, wordWrap='CJK'))
styles.add(ParagraphStyle(name='H1K', fontName='MalgunBold', fontSize=17, leading=24, textColor=NAVY, spaceAfter=13, wordWrap='CJK'))
styles.add(ParagraphStyle(name='H2K', fontName='MalgunBold', fontSize=11.5, leading=17, textColor=TEAL, spaceBefore=12, spaceAfter=6, wordWrap='CJK'))
styles.add(ParagraphStyle(name='BodyK', fontName='Malgun', fontSize=10, leading=16.5, textColor=NAVY, spaceAfter=8, wordWrap='CJK'))
styles.add(ParagraphStyle(name='SmallK', fontName='Malgun', fontSize=8.3, leading=13, textColor=GRAY, spaceAfter=5, wordWrap='CJK'))
styles.add(ParagraphStyle(name='CellK', fontName='Malgun', fontSize=8.8, leading=14, textColor=NAVY, wordWrap='CJK'))
styles.add(ParagraphStyle(name='HeadCellK', fontName='MalgunBold', fontSize=8.8, leading=14, textColor=colors.white, wordWrap='CJK'))

def p(text, style='BodyK'):
    return Paragraph(text, styles[style])

def h(text): return p(text, 'H2K')

def table(rows, widths):
    data = [[p(escape(str(c)).replace('\n','<br/>'), 'HeadCellK' if i == 0 else 'CellK') for c in row] for i,row in enumerate(rows)]
    t=Table(data, colWidths=widths, hAlign='LEFT', repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
        ('LINEBELOW',(0,0),(-1,0),.6,TEAL),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D7E2EA'))]))
    return t

def callout(title, body):
    t=Table([[p(title,'H2K')],[p(body)]],colWidths=[491])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#C8DDE5')),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,0),0),('BOTTOMPADDING',(0,-1),(-1,-1),7)]))
    return t

def page(title, subtitle, content):
    return [p(title,'H1K'),p(subtitle,'SubK'),*content]

def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#D7E2EA'));c.line(52,793,543,793)
    c.setFont('Malgun',8);c.setFillColor(GRAY)
    c.drawString(52,805,doc.tag)
    c.drawString(52,31,'Motor ECU 개발 기록 | 2026.10.17 | 코드·로그·대화 기준')
    c.drawRightString(543,31,str(doc.page))

def build(filename, tag, pages):
    doc=SimpleDocTemplate(str(OUT/filename),pagesize=(595.28,841.89),leftMargin=52,rightMargin=52,topMargin=67,bottomMargin=57,
        title=tag,author='프로젝트 작업 기록',subject='Motor ECU 구현, 문제해결, 검증 및 자기소개서·면접 준비')
    doc.tag=tag
    story=[]
    for i,content in enumerate(pages):
        if i:story.append(PageBreak())
        story.extend(content)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    rd=PdfReader(OUT/filename)
    assert len(rd.pages)==len(pages),(filename,len(rd.pages),len(pages))
    print(filename,len(rd.pages),'pages')

resume=[]
resume.append([
    p('Motor ECU 개발 경험<br/>자기소개서 활용 노트','TitleK'),
    p('임베디드 펌웨어 · 차량 네트워크 · 검증 직무\n2026년 10월 17일 작업 중심','SubK'),
    callout('경험을 설명하는 중심 문장','CAN 기반 Motor ECU의 제어·통신·출력 경계를 정리하고, RTOS 동시성 구조와 DBC 인터페이스를 코드·시험 도구·문서에 일관되게 반영한 경험이다.'),
    h('기술스택과 실제 사용 목적'),
    table([['분야','사용 기술','이번 작업의 역할'],
        ['MCU / 언어','STM32F446RE, C, STM32 HAL','CAN 수신·송신, 타이머 PWM, 드라이버/서보 출력'],
        ['실시간 OS','FreeRTOS V10.3.1 + CMSIS-RTOS2','5 tasks, mutex 2개, queue 2개, 우선순위 상속'],
        ['차량 통신','Classic CAN 500kbps, DBC','0x100 명령 / 0x110 상태, Alive·timeout 검사'],
        ['물리 출력','MDD3A 2개, DC 4개, SG90 2개','20kHz DC PWM, 50Hz 서보 PWM, 전원/GND 분리'],
        ['PC / 검증','Python, CANgaroo, CANable, GCC','주기 송신·자동 시퀀스, mock 회귀, 전체 ARM 빌드'],
        ['환경 / 산출물','STM32CubeIDE 2.2.0, Git, Markdown','원격 develop 비교, 핀 입출력·구성도·검토 기록']], [76,172,243]),
    h('기록에서 확인되는 결과'),
    p('<b>전체 ARM 빌드 통과</b>, C 제어 회귀와 CMSIS2 task 모의 회귀 통과, 최신 Python script <b>15개 테스트 통과</b>. 공식·시험용 DBC와 펌웨어/스크립트의 조향 배치를 Byte4~5로 동기화했다.'),
    p('수치의 의미: 테스트 수는 Python unittest 기준이다. 서로 다른 C 테스트를 합산하지 않았다. 1ms/10ms는 설정 주기이며 실물 최대 지연이나 성능 향상률을 측정한 값이 아니다.','SmallK'),
])
resume.append(page('01. 작업 과정과 기여 정리','오늘의 변경과 앞선 시행착오를 연결하되, 수행 주체와 검증 수준을 구분한다.',[
    table([['단계','진행 내용','산출물 / 의미'],
        ['요구 파악','VCU 요청 → Motor ECU → DC/서보 출력 구조 확인','실측 모델과 Virtual Motor 모델 구분'],
        ['기존 문제 추적','TX 증가·RX0, RX/TX 배선 착오와 PC 설정 확인','사용자 배선 수정 후 fresh 0x110/READY 로그'],
        ['RTOS 전환','CMSIS v1 API에서 v2로 전환, RX/제어/출력/TX/Health 분리','ISR는 큐 전달, 공유 상태는 mutex로 보호'],
        ['명세 교차 검토','원격 develop 226e88e의 아키텍처·DBC·Excel 대조','조향 Byte3~4와 Body 후보 Byte3의 중복 발견'],
        ['인터페이스 수정','조향을 Byte4~5로 이동, firmware4/script1.4 적용','기존 Torque/Gear/Brake/Alive 위치 유지'],
        ['반복 시험 도구','script1.5 auto 구현: 속도·좌우 조향·전후진 반복','30초 순환, 정지 구간, 통신 고장 시 자동 해제'],
        ['전달·재현성','CN7/CN10 핀 번호와 전원·GND·종단 정리','하드웨어 Pin In/Out 문서 및 연결 확인표']], [55,220,216]),
    h('내 역할을 작성할 때의 기준'),
    p('사용자는 DC 4개·서보 2개 요구를 제시하고 실제 배선·IDE·CANgaroo 실행 로그를 공유했다. RX/TX 배선 착오를 직접 확인해 수정한 사실은 대화에 남아 있다. 코드 변경·테스트 작성·문서 작성은 AI 보조로 진행되었다.'),
    p('자기소개서의 “설계했다·구현했다”는 표현은 본인이 코드를 설명하고 재현할 수 있는 범위에서 사용한다. 팀 전체 소유권, 혼자 작성한 코드량, 실물 최종 검증 완료 등을 이 기록만으로 주장하지 않는다.'),
    callout('주도성을 보여 주는 근거','도구를 사용했다는 사실보다 요구를 구체화한 과정, 로그를 가져와 가설을 좁힌 과정, 다른 ECU와 충돌하는 규격을 확인하고 수정 범위를 일관되게 정한 판단을 설명한다.'),
]))
resume.append(page('02. 문제해결 사례를 STAR로 묶기','사례 A는 인터페이스 정합성, 사례 B는 통신 문제의 원인 분리 역량을 보여 준다.',[
    h('사례 A | 단독 시험에서 보이지 않던 DBC 비트 충돌'),
    table([['STAR','기록에 근거한 내용'],
        ['Situation','DC·서보를 함께 제어하는 시험 확장에서는 조향각을 0x100 Byte3~4에 배치했다. 최신 Gateway Routing 문서에는 Byte3를 램프·도어·윈도 명령으로 쓰는 후보안이 있었다.'],
        ['Task','다른 ECU와 통합했을 때 서로 다른 기능이 같은 바이트를 해석하지 않도록, 인터페이스 충돌을 제거해야 했다.'],
        ['Action','최신 원격 커밋의 DBC·메시지 정의·Routing을 대조했다. 조향 -20도의 raw -200이 38 FF가 되어 Body 후보에서는 Hazard 등의 값으로 읽힐 수 있음을 확인했다. Byte4~5로 이동하고 DBC·C 디코더·Python 송신·테스트를 함께 바꿨다.'],
        ['Result','Byte3 전체 256가지 값이 조향·기존 DC 명령에 영향을 주지 않는 회귀를 통과했다. firmware revision4와 script의 버전 검사를 맞춰 구버전 혼용을 줄였다. 팀 검토·원격 반영과 전체 ECU 통합은 별도다.']], [67,424]),
    h('사례 B | “TX는 늘지만 RX는 0”인 상태의 진단'),
    p('<b>상황:</b> 스크립트 송신 카운터는 증가했지만 0x110 수신이 없었다. 모터 전원과 CAN 통신의 원인을 섞어 판단하기 쉬운 상태였다.'),
    p('<b>접근:</b> PC interface 선택, 500kbps와 Listen-only, MCU 실행 상태, 트랜시버 TX/RX 배선을 구분해 점검했다. 사용자에게서 RX/TX 연결 착오가 확인되었고, 이후 RX 증가·READY·수 ms 수준의 fresh status 로그가 관찰되었다.'),
    p('<b>배운 점:</b> PC의 TX API 호출 성공은 상대 ECU 수신 성공이 아니다. CAN 상태 수신과 실제 PWM·모터 전력은 별도 경로이므로 단계별 관측점을 둬야 한다. 로그 하나만으로 최초 원인을 모두 확정했다고 표현하지 않는다.'),
]))
resume.append(page('03. 자기소개서에 바로 활용하는 초안','지원 직무와 글자 수에 맞춰 다듬을 재료다. 개인이 설명·재현 가능한 내용만 제출한다.',[
    h('경험 중심 초안 | 인터페이스 정합성과 문제해결'),
    callout('초안','CAN-LIN Gateway 프로젝트에서 Motor ECU의 제어 인터페이스와 검증 흐름을 다뤘습니다. DC 모터 네 개와 서보 두 개를 연결하는 과정에서 단독 시험의 동작 여부만으로는 통합 정합성을 판단할 수 없다고 보았습니다. 최신 develop의 아키텍처, DBC와 Gateway Routing을 비교한 결과, 시험용 조향각이 사용하는 Byte3와 Body 명령 후보 영역이 겹치는 점을 확인했습니다. 조향각을 Byte4~5로 이동하고 DBC, 펌웨어 디코더, PC 송신 스크립트와 회귀 테스트를 함께 정렬했습니다. 또한 구버전 펌웨어를 식별하도록 버전 검사를 갱신했습니다. 이 경험을 통해 임베디드 개발의 완성도는 개별 기능의 구현뿐 아니라 인터페이스의 일관성과 재현 가능한 검증에서 나온다는 점을 배웠습니다.'),
    h('직무 역량 초안 | 실시간 구조와 검증 범위'),
    p('Motor ECU를 CMSIS-RTOS2 기반으로 정리하며 수신, 제어, 출력과 송신의 책임을 나누었습니다. ISR에서는 블로킹 없이 큐에 프레임을 전달하고, task 사이의 공유 상태는 우선순위 상속 mutex로 보호했습니다. 제어와 출력 task가 각각 명령 freshness를 확인하도록 하고, 큐 포화와 mutex 획득 실패 상황도 모의 테스트했습니다. 전체 ARM 빌드와 회귀 테스트 통과 후에도 실물 지연, bus-off 복구와 CPU 예외 시 출력 차단은 별도 검증 과제로 남겼습니다. 구현한 기능과 검증하지 못한 영역을 구분해 설명하는 개발 습관을 갖추고자 했습니다.'),
    h('이력서에 넣을 수 있는 짧은 표현'),
    p('• STM32 Motor ECU의 CMSIS-RTOS2 task/queue/mutex 구조 및 CAN 명령·PWM 출력 연동 정리<br/>• 조향각과 Gateway Body 명령 후보의 DBC 비트 중복 분석, Byte4~5 이동 및 송수신 규격 동기화<br/>• CANgaroo 자동 시퀀스·고장 중단 동작 구현 보조 및 Python 회귀 15개 통과'),
    h('제출 전 개인화할 항목'),
    p('지원 회사의 요구 역량과 연결되는 사례 하나를 중심으로 고른다. 본인의 팀 내 책임, 실제 보드에서 직접 확인한 동작, 팀 리뷰 결과를 추가한다. AI 보조 범위를 질문받으면 코드 초안·변경·테스트 작성에 활용한 점과 본인이 검토한 판단을 사실대로 구분한다.'),
]))
resume.append(page('04. 성과를 증거로 설명하기','완료·관찰·미확인을 섞지 않는 것이 면접에서 신뢰를 만든다.',[
    table([['구분','표현 가능한 사실','추가로 필요한 증거'],
        ['구현 / 시험','C 제어 회귀 PASS, RTOS mock PASS, Python 15 tests PASS','테스트 명령과 로그, 실패 사례를 설명할 수 있어야 함'],
        ['빌드','revision4 전체 ARM Debug 빌드 통과','실제 보드의 실행 버전과 연결 확인'],
        ['실물 관찰','RX 증가·READY/fresh status 로그, 서보 회전량이 작다는 사용자 관찰','최신 auto에서 DC4/서보2 전체 동작·정지 영상/로그'],
        ['모델 값','CAN RPM/TorqueApplied는 Virtual Motor 기준','실측 RPM·전류·토크라고 표현하지 않음'],
        ['설계 수치','제어/출력 1ms, CAN10ms, age>30ms inhibit','실물 최대 응답시간·jitter·mutex 점유시간 미측정'],
        ['미해결','CPU fault PWM 차단, bus-off 복구, 3회 확인 계수 정의','해결 전 “고장 복구 완성”이라고 작성하지 않음']], [65,225,201]),
    h('추가 측정 후 채울 성과 항목'),
    p('실물 timeout 검출~출력 차단 최대 지연: [측정값]ms / 시험 부하: [조건]<br/>자동 시퀀스 연속 운전: [시간]분 / CAN 프레임 누락·fault 발생: [횟수]<br/>task별 최소 stack 여유: [bytes] / 최대 mutex 보유: [시간]<br/>버스 오프 및 통신 재개: [절차·소요 시간] / 서보 각도 보정 오차: [측정값]'),
    h('나중에 다시 열어 볼 저장소 산출물'),
    p('Core/Src/freertos.c · motor_can.c · motor_app.c · motor_watchdog.c<br/>cangaroo/motor_control.py · tests/test_cangaroo_script.py<br/>firmware/motor_ECU/RTOS2_ARCHITECTURE.md<br/>firmware/motor_ECU/DEVELOP_ARCHITECTURE_REVIEW.md<br/>network/can/MOTOR_STEERING_INTERFACE.md<br/>docs/hardware/MOTOR_ECU_PINOUT.md','SmallK'),
    p('경로는 저장소 루트 freertos-can-lin-gateway 기준이다. 원격 검토 기준은 develop 커밋 226e88e076171037d9e115e9722ec3cbdc18e268. 현재 로컬 변경이 원격에 push되었다는 뜻은 아니다. 본 문서는 대화와 저장 파일을 요약한 취업 준비용 자료이며 정식 시험성적서는 아니다.','SmallK'),
]))

interview=[]
interview.append([
    p('Motor ECU 개발 경험<br/>기술면접 준비 노트','TitleK'),
    p('설계 이유 · 데이터 흐름 · 장애 진단 · 검증 한계\n2026년 10월 17일 기준','SubK'),
    h('60초 설명 예시'),
    callout('말하기 초안','STM32 기반 CAN-LIN 프로젝트에서 Motor ECU의 CAN 제어와 RTOS 구조를 다뤘습니다. VCU의 0x100 명령을 받아 Virtual Motor의 target RPM을 계산하고, DC 네 개와 SG90 두 개의 보조 출력으로 연결했습니다. CMSIS-RTOS2로 전환하며 수신·제어·출력·송신·상태 감시를 분리하고, 공유 상태를 mutex로 보호했습니다. 최신 Gateway 문서와 비교할 때 조향각과 Body 명령 후보의 Byte3 중복을 발견해 Byte4~5로 옮겼습니다. 전체 ARM 빌드와 모의 회귀 테스트를 통과했으며, 실물 지연 측정과 CPU fault·bus-off 복구는 남은 과제로 구분했습니다.'),
    h('3분으로 늘릴 때의 순서'),
    p('<b>요구 30초:</b> CAN 수신, DC4/SG90 2 출력, Virtual Motor baseline.<br/><b>구조 45초:</b> ISR → RX queue → 상태 mutex → 제어/출력, 별도 TX queue.<br/><b>문제해결 60초:</b> TX/RX 관측점으로 통신과 전력을 분리하고 DBC 충돌을 재현.<br/><b>검증 30초:</b> ARM 빌드, C/RTOS mock, Python15 tests.<br/><b>한계 15초:</b> 실제 최악 지연, CPU fault, bus-off는 미완료.'),
    h('구분해서 말해야 할 네 가지'),
    p('1. CMSIS-RTOS2는 API 계층이고, FreeRTOS 커널은 V10.3.1이다.<br/>2. PWM 요청 비율은 실제 차량 속도나 실측 모터 RPM이 아니다.<br/>3. 조향각은 논리 target이며 실측 SG90 축 각도나 바퀴 각도가 아니다.<br/>4. mock 통과는 커널 선점·전기적 신호·실물 동작의 증명이 아니다.'),
])
interview.append(page('01. 구조를 화이트보드로 설명하기','공유 데이터와 하드웨어 자원의 소유권부터 그린다.',[
    callout('데이터 흐름','CAN RX ISR → 캡처 시각을 포함한 RX queue → canRxTask → motorStateMutex로 보호한 runtime → control/actuator task → PWM<br/><br/>control task → TX queue → canTxTask → canTxMutex → HAL CAN mailbox'),
    table([['Task','우선순위 / 주기','책임'],
        ['actuatorTask','High1(41) / 1ms','DC·서보 PWM target 적용, 자체 freshness 검사'],
        ['motorControlTask','High(40) / 1ms','watchdog, 가상 모델, 고장 상태; 10ms 상태 생성'],
        ['canRxTask','AboveNormal(32) / queue 대기','명령 decode, 캡처 시각·Alive 검증'],
        ['canTxTask','Normal(24) / queue 대기','상태 송신; 20ms보다 오래된 대기 상태 폐기'],
        ['healthTask','BelowNormal(16) / 500ms','LED, task stack 여유 관측']], [110,140,241]),
    h('왜 출력 task와 제어 task를 나눴나?'),
    p('모델 계산·상태 송신과 물리 출력 적용의 책임을 분리했다. 출력 task도 watchdog을 검사하므로 모델 갱신 지연에만 의존하지 않는다. 단, 같은 CPU/커널이 멈추면 둘 다 실행되지 않으므로 독립적인 하드웨어 안전 장치는 별도 문제다.'),
    h('1ms task가 PWM을 1ms마다 토글하나?'),
    p('아니다. task는 CCR duty/펄스 폭을 갱신한다. DC 파형은 TIM1/3/4의 20kHz, 서보는 TIM2의 50Hz 하드웨어 타이머가 생성한다. task 주기와 파형 주파수를 구분해야 한다.'),
    h('핀을 설명한다면'),
    p('CAN PA11/12, DC PA8/9·PB4/5·PB0/1·PB6/7, 서보 PA0/1. MDD3A의 제어 입력과 모터 출력 단자는 이름이 같아도 구분한다. 서보는 외부5V, SN65HVD230은3.3V, GND는 공통이며 모터 전압은 모터 정격에 따른다.'),
]))
interview.append(page('02. CAN·DBC 질문과 바이트 해석','최신 규격: DBC0.7 / firmware revision4 / script1.5.',[
    table([['0x100 VCU_Command','데이터 형식','의미'],
        ['Byte0~1','unsigned16, Intel, 0.1Nm','TorqueRequest 0~4000Nm'],
        ['Byte2 bit0~2 / bit3 / bit4~7','Gear / Brake / Alive','0P 1N 2D 3R / bool / 0~15 wrap'],
        ['Byte3','Motor는 무시, script는0','Gateway Body 명령 후보용 확보'],
        ['Byte4~5','signed16, Intel, 0.1도','SteeringAngle -45~45도'],
        ['Byte6~7','Reserved, script는0','현재 미사용']], [120,180,191]),
    h('예제 | 전진25%, 좌20도, Alive0'),
    callout('10 27 02 00 38 FF 00 00','데모 맵에서 25%는 TorqueRequest1000Nm → raw10000=0x2710 → 10 27. Gear D=2. 좌20도는 raw -200의 16bit 2의 보수0xFF38 → 38 FF. 조향은 Byte4~5에 들어간다.'),
    h('왜 Byte3를 비웠나?'),
    p('Gateway Routing의 Body Command 후보가 Byte3의 bit24~31을 사용했다. 옛 조향 -20도의 Byte3=0x38은 그 후보에서 Hazard=1, DoorLock=3으로 읽힌다. 후보가 공식 DBC에 아직 없더라도 통합 전에 겹침을 제거해야 했다. 이동 후 공식/시험 DBC와 디코더·송신기·테스트를 함께 바꿨다.'),
    h('0x110 응답은 무엇인가?'),
    p('Byte0~1 Virtual RPM, Byte2~3 TorqueApplied, Byte4의 low2bits MotorState와 다음4bits Alive이다. 확장 Byte5~6은 target echo, Byte7 low4bits는 fault flags, high4bits는 firmware revision이다. echo는 위치 센서 피드백이 아니다.'),
    h('DBC와 펌웨어 버전은 왜 함께 바꾸나?'),
    p('같은 CAN ID/DLC여도 바이트 의미가 바뀌면 조용한 오해석이 생긴다. script는 revision4만 구동을 허용한다. 다만 CAN command 자체에 송신기 버전 필드가 없으므로 Raw TX나 다른 VCU까지 자동 보호되는 것은 아니다. 모든 송신기의 규격을 맞춰야 한다.'),
]))
interview.append(page('03. 막힌 부분을 어떻게 좁혔나?','관측 → 가설 → 확인 → 남은 한계를 한 묶음으로 답한다.',[
    table([['관측 / 문제','원인 분리와 처리','면접에서 피할 단정'],
        ['TX 증가, RX0','interface·500kbps·Listen-only·실행 상태·트랜시버 배선을 분리. 사용자 RX/TX 착오 수정 후 READY/fresh 응답 관찰','TX 카운터만으로 CAN 전달 성공 주장'],
        ['명령은 보이나 모터 정지','CAN 수신과 드라이버 전력, PWM 핀, A/B 연결, 낮은 duty 기동 특성을 나눠 확인','통신 정상이라 모터 전력도 정상이라고 추정'],
        ['서보가 안 움직임','초기 script에 mapping deferred 표기가 있었음. 이후 실제 TIM2 출력과 진단 echo를 추가한 revision 적용','초기 미구현과 이후 FAIL_SAFE를 같은 원인으로 단정'],
        ['FAIL_SAFE 반복','timeout/Alive/invalid/RX loss flags를 구분하고 명령 나이·다중0x100 송신 여부를 관측','Alive 검사를 끄면 해결됐다고 주장'],
        ['서보 회전량 작음','±45도 요청이1250~1750µs로 제한된 현재 변환 확인. 2배 확대는 제안만 했으며 적용하지 않음','실제 축 각도가 요청 각도와 같다고 주장'],
        ['auto 입력 즉시 ValueError','interface 번호를 int로 받는 단계에 auto 입력. 먼저256 선택 후 motor 프롬프트에서 auto','이 오류를 CAN 버스 고장으로 해석']], [102,260,129]),
    h('통신·논리·물리 출력의 관측점'),
    p('PC 송신 요청 → 버스의 0x100 → ECU RX/Alive/age → target/duty/CCR → 핀 파형 → 드라이버 출력 → 실제 회전. 어느 지점까지 확인했는지 말하고 그 다음 지점을 측정한다. TX API 호출 수와 실물 전달률, Virtual RPM과 실제 RPM을 혼용하지 않는다.'),
    h('자동 시퀀스는 무엇을 검증하는가?'),
    p('30초 동안 PWM20~35%, 조향0/±20/±40도, 전진·정지·후진을 반복한다. s나 수동 명령이 자동 모드를 해제하며 상태 끊김/OFF/FAIL_SAFE/버전 불일치 후 자동 재개하지 않는다. 반복 명령 생성과 중단 로직을 검증하지만 실제 출력의 완전한 HIL 시험은 아니다.'),
]))
interview.append(page('04. RTOS·고장 처리 심화 질문','답을 암기하기보다 코드의 경계와 미완료 사항을 이해한다.',[
    h('Q1. ISR에서 mutex를 잡지 않는 이유는?'),
    p('mutex는 task 소유권과 대기를 전제로 한다. ISR은 timeout0 message queue put으로 캡처 프레임을 넘기고, task가 mutex로 상태를 갱신한다. CAN IRQ priority5도 RTOS syscall 허용 범위에 맞췄다.'),
    h('Q2. 우선순위 역전은 어떻게 다뤘나?'),
    p('motorStateMutex와 canTxMutex에 priority inheritance를 사용한다. 단, 상속만으로 deadline이 보장되지는 않는다. 임계구역 길이·블로킹 상한과 실물 부하를 측정해야 한다. state mutex는 최대2 ticks 획득 대기하며 출력 task 실패 시 SafeStop으로 간다.'),
    h('Q3. 큐에서 꺼낸 시각을 수신 시각으로 쓰면?'),
    p('오래 대기한 명령이 새 명령처럼 보일 수 있다. ISR 캡처 시각을 보존해 freshness를 판단한다. RX queue loss는 epoch로 추적하고 손실 전 대기 프레임을 버린 뒤 Alive를 재동기화한다.'),
    h('Q4. timeout과 복구는 정확히 어떻게 동작하나?'),
    p('수신 age가30ms를 초과하면 torque/targetRPM을0으로 만들고 Virtual RPM은 감쇠한다. 정상 task 경로에서 서보 target은 중앙이다. timeout 후 첫 프레임은 Alive seed로 쓰고 이후 연속 증가3회, 실제4프레임에서 해제된다. 문서의 “3회 확인”과 계수 기준 정렬은 아직 남아 있다.'),
    h('Q5. bus-off가 되면 자동으로 정상화되나?'),
    p('현재는 아니다. AutoBusOff가 비활성이고 별도 재시작 상태 머신도 없다. 수신이 끊기면 timeout 정지는 하지만 통신 복구까지 완성한 것은 아니다. ABOM 또는 관리된 재시작과 Alive 재동기화 정책을 정하고 주입 시험해야 한다.'),
    h('Q6. HardFault에서도 출력 task가 안전하게 멈추나?'),
    p('현재 예외 핸들러는 무한 대기하고 타이머는 마지막 PWM을 유지할 수 있다. 따라서 task 기반 timeout만으로 CPU fault를 보장하지 못한다. RTOS에 의존하지 않는 출력 차단과 독립 watchdog/하드웨어 차단을 설계할 필요가 있다.'),
]))
interview.append(page('05. 검증 질문·시연·마지막 점검','“테스트를 했다”보다 어떤 실패를 구분했는지 설명한다.',[
    h('Q7. 어떤 테스트를 통과했나?'),
    p('C 모델 회귀는 DBC, 제동/P/N, timeout, invalid, Alive wrap/연속성, 방향 반전 등을 검사했다. RTOS mock은 실제 task 함수의 큐·mutex 경계, 획득 실패 정지, 출력 task의 timeout, 큐 손실 복구를 검사했다. Python15 tests는 바이트 벡터, DBC 동일성/중복, firmware mismatch, 자동 순환·정지·고장 후 미재시작을 포함한다. revision4 ARM 전체 빌드도 통과했다.'),
    h('Q8. 테스트 통과 후에도 왜 완료라고 말하지 않나?'),
    p('mock은 실시간 커널 선점·실제 CAN 전달·전압 강하·타이머 파형을 재현하지 않는다. 실물 최대 지연, jitter, stack 여유, 네 모터 동시 부하, CPU fault·bus-off 복구는 별도 증거가 필요하다. 이번 작업에서 성능 향상률이나 실물 오류율을 측정하지 않았다.'),
    h('Q9. AI는 어디에 사용했고 본인은 무엇을 했나?'),
    p('코드 변경·테스트 작성·문서 초안을 AI 보조로 진행했다. 요구를 구체화하고 배선/실행 로그를 제공했으며 RX/TX 착오를 확인한 과정을 설명할 수 있다. 면접에서는 본인이 실제로 판단·수정·재현한 부분을 더해 구분해서 답한다. 작성하지 않은 코드를 혼자 작성했다고 주장하지 않는다.'),
    h('짧은 시연 순서'),
    p('1. 바퀴를 띄우고 서보 가동 범위·외부 전원·GND를 확인한다.<br/>2. firmware4 실행, CANgaroo COM4/500kbps/normal 측정, script1.5 Load.<br/>3. interface 프롬프트에서256 선택 → motor 프롬프트에서 status 확인.<br/>4. READY/fresh/revision4 확인 후 낮은 출력·개별 조향 시험, 이후 auto.<br/>5. s로 DC0/P/중앙, quit 후 외부 전원 종료. 고장 주입은 별도 계획으로 진행.'),
    h('면접 전 직접 답해 볼 체크리스트'),
    p('□ -200을 38 FF로 설명할 수 있는가? □ Byte3 후보와 Byte4~5를 구분하는가?<br/>□ mutex와 queue의 역할이 다른 이유를 설명하는가?<br/>□ 설정 주기와 실측 지연을 구분하는가? □ 남은 결함 세 가지를 숨기지 않는가?<br/>□ 실제로 확인한 보드 동작과 팀 내 본인 역할을 구체적으로 말할 수 있는가?'),
    p('근거: 저장소의 RTOS2_ARCHITECTURE.md, DEVELOP_ARCHITECTURE_REVIEW.md, MOTOR_STEERING_INTERFACE.md, MOTOR_ECU_PINOUT.md 및 C/Python 테스트·빌드 로그와 대화. 최신 검토 기준 develop226e88e. 역할·성과 수치는 사실 확인 후 개인화한다.','SmallK'),
]))

if __name__ == '__main__':
    build('Motor_ECU_자기소개서_경험정리_2026-10-17.pdf','자기소개서 준비 | 경험·기여·문제해결',resume)
    build('Motor_ECU_기술면접_준비노트_2026-10-17.pdf','기술면접 준비 | 구조·설계 근거·검증',interview)
