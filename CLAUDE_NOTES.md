# PC Monitor 프로젝트 노트

## 프로젝트 개요
자녀 PC 사용 모니터링 도구 (Windows)

## 주요 기능
- 브라우저 방문 기록 (Chrome, Edge)
- 프로그램 실행 기록 (Prefetch, UserAssist, BAM)
- PC 사용 시간 (로그인/로그아웃 이벤트)
- 최근 파일 접근 기록
- 로블록스 게임 기록
- 날짜별 HTML 리포트 생성
- 대시보드에서 날짜별 조회
- Gmail로 일일 리포트 발송 (하루 1회)

## 파일 구조
```
pc-monitor/
├── main.py                 # 메인 실행 스크립트
├── email_config.txt        # 이메일 설정 (git 제외)
├── setup_startup.py        # 시작 프로그램 등록
├── src/
│   ├── browser_history.py  # 브라우저 기록 수집
│   ├── app_usage.py        # 프로그램 실행 기록
│   ├── pc_time.py          # PC 사용 시간
│   ├── recent_files.py     # 최근 파일 접근
│   ├── roblox_games.py     # 로블록스 게임 기록
│   ├── report_generator.py # HTML 리포트 생성
│   ├── data_storage.py     # JSON 데이터 저장
│   └── email_sender.py     # 이메일 발송
├── data/                   # 수집된 JSON 데이터 (git 제외)
└── output/                 # 생성된 HTML 리포트 (git 제외)
```

## 실행 방법
```bash
python main.py
```

## 남은 작업 / 개선 아이디어
- [ ] Windows 작업 스케줄러로 자동 실행
- [ ] 특정 사이트/프로그램 알림 기능
- [ ] 주간/월간 리포트
- [ ] 사용 시간 제한 알림

## 최근 변경 사항 (2026-01-08)
- 날짜별 데이터 필터링 구현
- 최근 7일치 데이터 수집
- Gmail 이메일 발송 기능 추가
- 하루 1회 이메일 발송 제한
