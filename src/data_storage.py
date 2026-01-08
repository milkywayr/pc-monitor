"""
일일 데이터 저장 및 조회 모듈
JSON 형식으로 날짜별 데이터 저장
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def get_data_folder() -> str:
    """데이터 저장 폴더 경로"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_daily_data_path(date: str = None) -> str:
    """일일 데이터 파일 경로

    Args:
        date: 날짜 문자열 (YYYY-MM-DD), None이면 오늘
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    data_folder = get_data_folder()
    return os.path.join(data_folder, f'daily_{date}.json')


def save_daily_data(data: Dict, date: str = None) -> str:
    """일일 데이터 저장

    Args:
        data: 저장할 데이터
        date: 날짜 (None이면 오늘)

    Returns:
        저장된 파일 경로
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    file_path = get_daily_data_path(date)

    # 저장 시간 추가
    data['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['date'] = date

    # datetime 객체를 문자열로 변환 (JSON 직렬화를 위해)
    clean_data = clean_for_json(data)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)

    print(f"[+] 일일 데이터 저장 완료: {file_path}")
    return file_path


def clean_for_json(obj):
    """JSON 직렬화를 위해 datetime 등을 문자열로 변환"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()
                if not k.endswith('_dt') and not k.endswith('_raw')}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, timedelta):
        total_seconds = int(obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}시간 {minutes}분"
    else:
        return obj


def load_daily_data(date: str) -> Optional[Dict]:
    """일일 데이터 로드

    Args:
        date: 날짜 (YYYY-MM-DD)

    Returns:
        저장된 데이터 또는 None
    """
    file_path = get_daily_data_path(date)

    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] 데이터 로드 실패 ({date}): {e}")
        return None


def get_available_dates() -> List[str]:
    """저장된 데이터가 있는 날짜 목록 반환"""
    data_folder = get_data_folder()

    dates = []
    if os.path.exists(data_folder):
        for filename in os.listdir(data_folder):
            if filename.startswith('daily_') and filename.endswith('.json'):
                # daily_2024-01-08.json -> 2024-01-08
                date = filename[6:-5]
                dates.append(date)

    # 최신순 정렬
    dates.sort(reverse=True)
    return dates


def get_date_range_data(start_date: str, end_date: str) -> List[Dict]:
    """날짜 범위 내의 모든 데이터 로드"""
    available_dates = get_available_dates()

    data_list = []
    for date in available_dates:
        if start_date <= date <= end_date:
            data = load_daily_data(date)
            if data:
                data_list.append(data)

    return data_list


def get_summary_for_period(days: int = 7) -> Dict:
    """최근 N일간의 요약 데이터"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    data_list = get_date_range_data(start_date, end_date)

    # 통계 계산
    total_browser_visits = 0
    total_files = 0
    all_domains = {}
    all_games = {}

    for daily_data in data_list:
        # 브라우저 방문
        browser_history = daily_data.get('browser_history', [])
        total_browser_visits += len(browser_history)

        # 도메인 통계
        for item in browser_history:
            domain = item.get('domain', '')
            all_domains[domain] = all_domains.get(domain, 0) + 1

        # 최근 파일
        recent_files = daily_data.get('recent_files', {}).get('files', [])
        total_files += len(recent_files)

        # 로블록스 게임
        roblox = daily_data.get('roblox', {})
        for game in roblox.get('game_stats', []):
            game_name = game.get('game_name', '')
            play_count = game.get('play_count', 0)
            all_games[game_name] = all_games.get(game_name, 0) + play_count

    return {
        'period_days': days,
        'data_count': len(data_list),
        'total_browser_visits': total_browser_visits,
        'total_files': total_files,
        'top_domains': sorted(all_domains.items(), key=lambda x: x[1], reverse=True)[:10],
        'top_games': sorted(all_games.items(), key=lambda x: x[1], reverse=True)[:10],
        'dates': [d.get('date') for d in data_list]
    }


# 테스트용
if __name__ == '__main__':
    print("=" * 50)
    print("데이터 저장 모듈 테스트")
    print("=" * 50)

    # 저장된 날짜 목록
    dates = get_available_dates()
    print(f"\n저장된 데이터: {len(dates)}일")
    for date in dates[:5]:
        print(f"  - {date}")

    # 요약
    if dates:
        summary = get_summary_for_period(7)
        print(f"\n최근 7일 요약:")
        print(f"  데이터 일수: {summary['data_count']}")
        print(f"  총 방문: {summary['total_browser_visits']}")
