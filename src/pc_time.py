"""
PC 사용 시간 수집 모듈
Windows 이벤트 로그에서 로그인/로그아웃 시간 분석
"""

import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import ctypes


def get_system_boot_time() -> datetime:
    """시스템 부팅 시간 반환"""
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        tick_count = kernel32.GetTickCount64()
        boot_time = datetime.now() - timedelta(milliseconds=tick_count)
        return boot_time
    except:
        return None


def get_uptime() -> timedelta:
    """현재 PC 가동 시간"""
    try:
        kernel32 = ctypes.windll.kernel32
        tick_count = kernel32.GetTickCount64()
        return timedelta(milliseconds=tick_count)
    except:
        return None


def format_duration(td: timedelta) -> str:
    """timedelta를 읽기 쉬운 형식으로 변환"""
    if td is None:
        return "알 수 없음"

    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}시간 {minutes}분"
    elif minutes > 0:
        return f"{minutes}분 {seconds}초"
    else:
        return f"{seconds}초"


def get_login_events(days: int = 7) -> List[Dict]:
    """Windows 이벤트 로그에서 로그인/로그아웃 이벤트 수집

    주요 이벤트 ID:
    - 4624: 로그온 성공
    - 4634: 로그오프
    - 4647: 사용자가 로그오프 시작
    - 7001: 사용자 로그온 (System 로그)
    - 7002: 사용자 로그오프 (System 로그)
    """
    events = []

    # PowerShell을 사용하여 이벤트 로그 조회
    # Security 로그는 관리자 권한 필요, System 로그는 일반 사용자도 가능

    start_date = datetime.now() - timedelta(days=days)
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')

    # System 로그에서 로그온/로그오프 이벤트 조회
    ps_command = f'''
    $events = @()
    try {{
        # System 로그에서 Winlogon 이벤트
        $sysEvents = Get-WinEvent -FilterHashtable @{{
            LogName = 'System'
            ProviderName = 'Microsoft-Windows-Winlogon'
            StartTime = '{start_str}'
        }} -ErrorAction SilentlyContinue

        foreach ($e in $sysEvents) {{
            $events += [PSCustomObject]@{{
                Time = $e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
                EventId = $e.Id
                Message = $e.Message.Split([Environment]::NewLine)[0]
            }}
        }}
    }} catch {{}}

    try {{
        # 시스템 시작/종료 이벤트
        $kernelEvents = Get-WinEvent -FilterHashtable @{{
            LogName = 'System'
            ProviderName = 'Microsoft-Windows-Kernel-General'
            Id = 12, 13
            StartTime = '{start_str}'
        }} -ErrorAction SilentlyContinue

        foreach ($e in $kernelEvents) {{
            $eventType = if ($e.Id -eq 12) {{ "시스템 시작" }} else {{ "시스템 종료" }}
            $events += [PSCustomObject]@{{
                Time = $e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
                EventId = $e.Id
                Message = $eventType
            }}
        }}
    }} catch {{}}

    $events | Sort-Object Time -Descending | Select-Object -First 50 | ConvertTo-Json
    '''

    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )

        if result.stdout.strip():
            import json
            data = json.loads(result.stdout)

            # 단일 객체인 경우 리스트로 변환
            if isinstance(data, dict):
                data = [data]

            for item in data:
                event_id = item.get('EventId', 0)

                # 이벤트 유형 분류
                if event_id == 7001:
                    event_type = '로그온'
                elif event_id == 7002:
                    event_type = '로그오프'
                elif event_id == 12:
                    event_type = '시스템 시작'
                elif event_id == 13:
                    event_type = '시스템 종료'
                else:
                    event_type = '기타'

                events.append({
                    'time': item.get('Time', ''),
                    'event_id': event_id,
                    'event_type': event_type,
                    'message': item.get('Message', '')
                })

        print(f"[+] 이벤트 로그: {len(events)}개 로그온/로그오프 이벤트 수집")

    except subprocess.TimeoutExpired:
        print("[!] 이벤트 로그 조회 시간 초과")
    except Exception as e:
        print(f"[!] 이벤트 로그 조회 실패: {e}")

    return events


def calculate_daily_usage(events: List[Dict]) -> Dict[str, timedelta]:
    """일별 PC 사용 시간 계산"""
    # 간단한 구현: 시스템 시작~종료 시간 계산
    daily_usage = {}

    # 이벤트를 시간순으로 정렬
    sorted_events = sorted(events, key=lambda x: x['time'])

    last_start = None
    for event in sorted_events:
        date = event['time'][:10]  # YYYY-MM-DD

        if event['event_type'] in ['시스템 시작', '로그온']:
            try:
                last_start = datetime.strptime(event['time'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        elif event['event_type'] in ['시스템 종료', '로그오프'] and last_start:
            try:
                end_time = datetime.strptime(event['time'], '%Y-%m-%d %H:%M:%S')
                duration = end_time - last_start

                if date not in daily_usage:
                    daily_usage[date] = timedelta()
                daily_usage[date] += duration
                last_start = None
            except:
                pass

    return daily_usage


def filter_events_by_date(events: List[Dict], filter_date: str) -> List[Dict]:
    """특정 날짜의 이벤트만 필터링

    Args:
        events: 이벤트 목록
        filter_date: 필터링할 날짜 (YYYY-MM-DD)

    Returns:
        해당 날짜의 이벤트만 포함된 목록
    """
    if not filter_date:
        return events

    filtered = []
    for event in events:
        event_date = event.get('time', '')[:10]  # YYYY-MM-DD
        if event_date == filter_date:
            filtered.append(event)

    return filtered


def get_pc_usage_summary(filter_date: str = None) -> Dict:
    """PC 사용 시간 요약 정보

    Args:
        filter_date: 특정 날짜만 필터링 (YYYY-MM-DD), None이면 오늘

    Returns:
        PC 사용 시간 요약
    """
    today = datetime.now().strftime('%Y-%m-%d')

    if filter_date is None:
        filter_date = today

    # 이벤트 로그 수집 (7일치)
    all_events = get_login_events(days=7)

    # 해당 날짜 이벤트만 필터링
    filtered_events = filter_events_by_date(all_events, filter_date)

    # 부팅 시간과 가동 시간은 오늘 날짜일 때만 표시
    if filter_date == today:
        boot_time = get_system_boot_time()
        uptime = get_uptime()
        boot_time_str = boot_time.strftime('%Y-%m-%d %H:%M:%S') if boot_time else '알 수 없음'
        uptime_str = format_duration(uptime)
    else:
        boot_time = None
        uptime = None
        boot_time_str = '해당 없음 (과거 날짜)'
        uptime_str = '해당 없음 (과거 날짜)'

    # 해당 날짜의 일별 사용 시간 계산
    daily_usage = calculate_daily_usage(filtered_events)

    return {
        'boot_time': boot_time_str,
        'uptime': uptime_str,
        'uptime_raw': uptime,
        'events': filtered_events,
        'daily_usage': daily_usage,
        'filter_date': filter_date
    }


# 테스트용
if __name__ == '__main__':
    print("=" * 50)
    print("PC 사용 시간 수집 테스트")
    print("=" * 50)

    summary = get_pc_usage_summary()

    print(f"\n[ 현재 세션 정보 ]")
    print(f"  부팅 시간: {summary['boot_time']}")
    print(f"  가동 시간: {summary['uptime']}")

    print(f"\n[ 최근 로그인/로그아웃 이벤트 ]")
    for event in summary['events'][:15]:
        print(f"  [{event['event_type']}] {event['time']}")

    print(f"\n[ 일별 사용 시간 ]")
    for date, duration in sorted(summary['daily_usage'].items(), reverse=True):
        print(f"  {date}: {format_duration(duration)}")
