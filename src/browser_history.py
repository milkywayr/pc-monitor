"""
브라우저 방문 기록 수집 모듈
Chrome, Edge의 방문 기록을 SQLite DB에서 읽어옴
"""

import os
import sqlite3
import shutil
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter
from urllib.parse import urlparse


def get_chrome_history_path() -> str:
    """Chrome 히스토리 DB 경로 반환"""
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    return os.path.join(local_app_data, 'Google', 'Chrome', 'User Data', 'Default', 'History')


def get_edge_history_path() -> str:
    """Edge 히스토리 DB 경로 반환"""
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    return os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data', 'Default', 'History')


def chrome_time_to_datetime(chrome_time: int) -> datetime:
    """Chrome 타임스탬프를 datetime으로 변환 (로컬 시간)
    Chrome은 1601년 1월 1일부터 마이크로초 단위로 UTC 저장
    """
    if chrome_time:
        # Chrome 타임스탬프를 Unix 타임스탬프로 변환
        # 1601-01-01 ~ 1970-01-01 = 11644473600 초
        unix_timestamp = (chrome_time / 1000000) - 11644473600
        if unix_timestamp > 0:
            # UTC에서 로컬 시간으로 변환
            return datetime.fromtimestamp(unix_timestamp)
    return None


def read_browser_history(db_path: str, browser_name: str, days: int = 7) -> List[Dict]:
    """브라우저 히스토리 DB에서 방문 기록 읽기

    Args:
        db_path: 히스토리 DB 파일 경로
        browser_name: 브라우저 이름 (Chrome/Edge)
        days: 최근 며칠간의 기록을 가져올지

    Returns:
        방문 기록 리스트
    """
    if not os.path.exists(db_path):
        print(f"[!] {browser_name} 히스토리 파일을 찾을 수 없음: {db_path}")
        return []

    # DB 파일이 잠겨있을 수 있으므로 임시 파일로 복사
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_path = temp_file.name
    temp_file.close()

    try:
        shutil.copy2(db_path, temp_path)

        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()

        # 최근 N일간의 기록만 조회
        cutoff_time = datetime.now() - timedelta(days=days)
        # Chrome 타임스탬프로 변환
        chrome_cutoff = int((cutoff_time - datetime(1601, 1, 1)).total_seconds() * 1000000)

        query = """
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            WHERE last_visit_time > ?
            ORDER BY last_visit_time DESC
        """

        cursor.execute(query, (chrome_cutoff,))
        rows = cursor.fetchall()

        history = []
        for row in rows:
            url, title, visit_count, last_visit_time = row
            visit_datetime = chrome_time_to_datetime(last_visit_time)

            history.append({
                'browser': browser_name,
                'url': url,
                'title': title or '(제목 없음)',
                'visit_count': visit_count,
                'last_visit': visit_datetime.strftime('%Y-%m-%d %H:%M:%S') if visit_datetime else '',
                'domain': urlparse(url).netloc
            })

        conn.close()
        return history

    except Exception as e:
        print(f"[!] {browser_name} 히스토리 읽기 실패: {e}")
        return []
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def get_all_browser_history(days: int = 7, filter_date: str = None) -> List[Dict]:
    """모든 브라우저의 방문 기록 수집

    Args:
        days: 최근 며칠간의 기록을 가져올지
        filter_date: 특정 날짜만 필터링 (YYYY-MM-DD 형식)
    """
    all_history = []

    # Chrome 히스토리
    chrome_path = get_chrome_history_path()
    chrome_history = read_browser_history(chrome_path, 'Chrome', days)
    all_history.extend(chrome_history)
    print(f"[+] Chrome: {len(chrome_history)}개 기록 수집")

    # Edge 히스토리
    edge_path = get_edge_history_path()
    edge_history = read_browser_history(edge_path, 'Edge', days)
    all_history.extend(edge_history)
    print(f"[+] Edge: {len(edge_history)}개 기록 수집")

    # 특정 날짜만 필터링
    if filter_date:
        all_history = [h for h in all_history if h.get('last_visit', '').startswith(filter_date)]
        print(f"[+] {filter_date} 날짜 필터링: {len(all_history)}개")

    return all_history


def get_domain_statistics(history: List[Dict]) -> List[Dict]:
    """도메인별 방문 통계"""
    domain_counts = Counter(item['domain'] for item in history)

    stats = []
    for domain, count in domain_counts.most_common(20):  # 상위 20개
        stats.append({
            'domain': domain,
            'visit_count': count
        })

    return stats


# 테스트용
if __name__ == '__main__':
    print("=" * 50)
    print("브라우저 방문 기록 수집 테스트")
    print("=" * 50)

    history = get_all_browser_history(days=7)

    if history:
        print(f"\n총 {len(history)}개 기록 수집됨\n")

        print("[ 도메인별 방문 통계 ]")
        stats = get_domain_statistics(history)
        for stat in stats[:10]:
            print(f"  {stat['domain']}: {stat['visit_count']}회")

        print("\n[ 최근 방문 기록 10개 ]")
        for item in history[:10]:
            print(f"  [{item['browser']}] {item['title'][:30]}...")
            print(f"         {item['domain']} - {item['last_visit']}")
    else:
        print("수집된 기록이 없습니다.")
