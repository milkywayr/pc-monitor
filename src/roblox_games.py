"""
로블록스 게임 기록 수집 모듈
Roblox 로그 파일 분석 + 브라우저 기록에서 roblox.com 추출
"""

import os
import re
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import Counter
import json


def get_roblox_logs_path() -> str:
    """Roblox 로그 폴더 경로 반환"""
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    return os.path.join(local_app_data, 'Roblox', 'logs')


def parse_roblox_log_file(log_path: str) -> List[Dict]:
    """로블록스 로그 파일에서 게임 접속 정보 추출

    로그에서 찾을 수 있는 정보:
    - PlaceId: 게임 ID
    - UniverseId: 게임 유니버스 ID
    - GameJoin 이벤트
    """
    records = []

    try:
        # 로그 파일 수정 시간으로 날짜 추정
        mtime = os.path.getmtime(log_path)
        log_date = datetime.fromtimestamp(mtime)

        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # PlaceId 패턴 찾기
        place_id_patterns = [
            r'placeId["\s:=]+(\d+)',
            r'PlaceId["\s:=]+(\d+)',
            r'place_id["\s:=]+(\d+)',
            r'placeid["\s:=]+(\d+)',
            r'GameJoin.*?placeId["\s:=]+(\d+)',
            r'"placeId":(\d+)',
            r'placeId=(\d+)',
        ]

        found_place_ids = set()
        for pattern in place_id_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for place_id in matches:
                if place_id and len(place_id) >= 6:  # 유효한 PlaceId는 보통 6자리 이상
                    found_place_ids.add(place_id)

        # 게임 접속 시간 패턴 찾기
        time_patterns = [
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
            r'(\d{2}:\d{2}:\d{2}\.\d+)',
        ]

        timestamps = []
        for pattern in time_patterns:
            matches = re.findall(pattern, content)
            timestamps.extend(matches)

        # 게임 시작/종료 이벤트 찾기
        join_patterns = [
            r'(GameJoin|JoinGame|startgame)',
            r'(Connection accepted)',
        ]

        has_game_session = any(re.search(p, content, re.IGNORECASE) for p in join_patterns)

        for place_id in found_place_ids:
            records.append({
                'place_id': place_id,
                'log_file': os.path.basename(log_path),
                'log_date': log_date.strftime('%Y-%m-%d %H:%M:%S'),
                'has_session': has_game_session
            })

    except Exception as e:
        pass

    return records


def get_roblox_game_name(place_id: str) -> str:
    """PlaceId로 게임 이름 조회 (캐시된 목록 또는 기본값)

    참고: 실제로는 Roblox API를 호출해야 하지만,
    여기서는 잘 알려진 게임들의 ID를 매핑해둠
    """
    # 인기 로블록스 게임 ID 매핑 (예시)
    known_games = {
        '286090429': 'Adopt Me!',
        '4924922222': 'Brookhaven RP',
        '920587237': 'Tower of Hell',
        '2788229376': 'Blox Fruits',
        '6284583030': 'Doors',
        '189707': 'Natural Disaster Survival',
        '185655149': 'Murder Mystery 2',
        '3956818381': 'Bedwars',
        '2753915549': 'Pet Simulator X',
        '1962086868': 'Tower Defense Simulator',
        '4520749081': 'King Legacy',
        '537413528': 'Mega Easy Obby',
        '606849621': 'Jailbreak',
        '301549746': 'Royale High',
        '292439477': 'Phantom Forces',
        '3527629287': 'Blade Ball',
        '142823291': 'Murder Mystery',
        '7449423635': 'Toilet Tower Defense',
    }

    return known_games.get(place_id, f'게임 ID: {place_id}')


def get_roblox_logs(days: int = 7) -> List[Dict]:
    """Roblox 로그 폴더에서 게임 기록 수집"""
    logs_path = get_roblox_logs_path()

    if not os.path.exists(logs_path):
        print(f"[!] Roblox 로그 폴더를 찾을 수 없음: {logs_path}")
        print("    (로블록스가 설치되지 않았거나 실행된 적이 없음)")
        return []

    records = []
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

    try:
        # 모든 로그 파일 조회
        log_files = glob.glob(os.path.join(logs_path, '*.log'))
        log_files.extend(glob.glob(os.path.join(logs_path, '**', '*.log'), recursive=True))

        for log_file in log_files:
            try:
                mtime = os.path.getmtime(log_file)
                if mtime < cutoff_time:
                    continue

                file_records = parse_roblox_log_file(log_file)
                records.extend(file_records)
            except:
                continue

        print(f"[+] Roblox 로그: {len(records)}개 게임 기록 수집")

    except Exception as e:
        print(f"[!] Roblox 로그 읽기 실패: {e}")

    return records


def get_roblox_from_browser_history(browser_history: List[Dict]) -> List[Dict]:
    """브라우저 기록에서 로블록스 관련 URL 추출"""
    roblox_records = []

    # roblox.com 관련 URL 패턴
    roblox_patterns = [
        r'roblox\.com/games/(\d+)',
        r'roblox\.com/ko/games/(\d+)',
        r'ro\.blox\.com/.*placeId=(\d+)',
    ]

    for item in browser_history:
        url = item.get('url', '')

        for pattern in roblox_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                place_id = match.group(1)
                roblox_records.append({
                    'place_id': place_id,
                    'game_name': get_roblox_game_name(place_id),
                    'url': url,
                    'title': item.get('title', ''),
                    'visit_time': item.get('last_visit', ''),
                    'source': 'browser'
                })
                break

    print(f"[+] 브라우저에서 Roblox 기록: {len(roblox_records)}개 발견")
    return roblox_records


def generate_sample_roblox_data() -> Dict:
    """샘플 로블록스 데이터 생성 (테스트/데모용)"""
    import random

    # 인기 게임 목록
    popular_games = [
        ('286090429', 'Adopt Me!'),
        ('4924922222', 'Brookhaven RP'),
        ('2788229376', 'Blox Fruits'),
        ('6284583030', 'Doors'),
        ('185655149', 'Murder Mystery 2'),
        ('3956818381', 'Bedwars'),
        ('7449423635', 'Toilet Tower Defense'),
        ('3527629287', 'Blade Ball'),
    ]

    # 랜덤하게 3~5개 게임 선택
    selected_games = random.sample(popular_games, random.randint(3, 5))

    game_stats = []
    browser_records = []

    for place_id, game_name in selected_games:
        play_count = random.randint(1, 8)
        play_time = random.randint(30, 180)  # 30분~3시간

        game_stats.append({
            'place_id': place_id,
            'game_name': game_name,
            'play_count': play_count,
            'total_time_minutes': play_time
        })

        # 브라우저 기록도 생성
        for i in range(min(play_count, 3)):
            hours_ago = random.randint(1, 48)
            visit_time = datetime.now() - timedelta(hours=hours_ago)
            browser_records.append({
                'place_id': place_id,
                'game_name': game_name,
                'url': f'https://www.roblox.com/games/{place_id}',
                'title': f'{game_name} - Roblox',
                'visit_time': visit_time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'browser'
            })

    return {
        'log_records': [],
        'browser_records': browser_records,
        'game_stats': game_stats,
        'total_games': len(game_stats),
        'is_sample': True
    }


def get_roblox_summary(browser_history: List[Dict] = None, use_sample: bool = False) -> Dict:
    """로블록스 게임 기록 요약

    Args:
        browser_history: 브라우저 방문 기록
        use_sample: True면 실제 데이터가 없을 때 샘플 데이터 사용
    """
    # 로그 파일에서 수집
    log_records = get_roblox_logs(days=7)

    # 브라우저 기록에서 수집
    browser_records = []
    if browser_history:
        browser_records = get_roblox_from_browser_history(browser_history)

    # 게임별 통계
    all_place_ids = []

    for r in log_records:
        all_place_ids.append(r['place_id'])

    for r in browser_records:
        all_place_ids.append(r['place_id'])

    game_counts = Counter(all_place_ids)

    # 게임 이름과 함께 정리
    game_stats = []
    for place_id, count in game_counts.most_common(20):
        game_stats.append({
            'place_id': place_id,
            'game_name': get_roblox_game_name(place_id),
            'play_count': count
        })

    # 데이터가 없고 use_sample이 True면 샘플 데이터 반환
    if not game_stats and use_sample:
        print("[*] 로블록스 기록이 없어 샘플 데이터를 사용합니다.")
        return generate_sample_roblox_data()

    return {
        'log_records': log_records,
        'browser_records': browser_records,
        'game_stats': game_stats,
        'total_games': len(game_counts),
        'is_sample': False
    }


# 테스트용
if __name__ == '__main__':
    print("=" * 50)
    print("로블록스 게임 기록 수집 테스트")
    print("=" * 50)

    # 단독 테스트 (브라우저 기록 없이)
    summary = get_roblox_summary()

    log_records = summary['log_records']
    game_stats = summary['game_stats']

    if game_stats:
        print(f"\n[ 플레이한 게임 목록 ]")
        for game in game_stats:
            print(f"  {game['game_name']}")
            print(f"      접속 횟수: {game['play_count']}회")
    else:
        print("\n로블록스 기록이 없습니다.")
        print("(로블록스가 설치되지 않았거나 최근 플레이 기록이 없음)")

    # 브라우저 기록과 연동 테스트
    print("\n[ 브라우저 기록 연동 테스트 ]")
    try:
        from browser_history import get_all_browser_history
        browser_history = get_all_browser_history(days=7)

        summary_with_browser = get_roblox_summary(browser_history)

        if summary_with_browser['browser_records']:
            print("\n[ 브라우저에서 발견된 로블록스 방문 ]")
            for r in summary_with_browser['browser_records'][:10]:
                print(f"  {r['game_name']}")
                print(f"      방문: {r['visit_time']}")
    except Exception as e:
        print(f"  브라우저 기록 연동 실패: {e}")
