"""
최근 파일 접근 기록 수집 모듈
Windows Recent 폴더 분석
"""

import os
import glob
from datetime import datetime
from typing import List, Dict
from collections import Counter
import struct


def get_recent_folder_path() -> str:
    """Recent 폴더 경로 반환"""
    app_data = os.environ.get('APPDATA', '')
    return os.path.join(app_data, 'Microsoft', 'Windows', 'Recent')


def parse_lnk_target(lnk_path: str) -> str:
    """바로가기(.lnk) 파일에서 대상 경로 추출 (간단한 방식)"""
    try:
        # LNK 파일은 복잡한 구조를 가지므로,
        # 여기서는 shell32를 사용하여 대상 경로를 가져옴
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        return shortcut.TargetPath
    except:
        # win32com이 없으면 파일명에서 추측
        basename = os.path.basename(lnk_path)
        # .lnk 확장자 제거
        if basename.lower().endswith('.lnk'):
            return basename[:-4]
        return basename


def get_file_extension(filename: str) -> str:
    """파일 확장자 추출"""
    _, ext = os.path.splitext(filename)
    return ext.lower() if ext else '(없음)'


def categorize_file(filename: str) -> str:
    """파일 종류 분류"""
    ext = get_file_extension(filename).lower()

    categories = {
        '문서': ['.doc', '.docx', '.pdf', '.txt', '.hwp', '.ppt', '.pptx', '.xls', '.xlsx'],
        '이미지': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
        '동영상': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm'],
        '음악': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
        '압축파일': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        '실행파일': ['.exe', '.msi', '.bat', '.cmd'],
        '코드': ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.h'],
    }

    for category, extensions in categories.items():
        if ext in extensions:
            return category

    return '기타'


def get_recent_files(days: int = 7, filter_date: str = None) -> List[Dict]:
    """최근 열어본 파일 목록 수집

    Args:
        days: 최근 며칠간의 데이터를 수집할지 (filter_date가 없을 때 사용)
        filter_date: 특정 날짜만 필터링 (YYYY-MM-DD)

    Returns:
        최근 열어본 파일 목록
    """
    recent_path = get_recent_folder_path()

    if not os.path.exists(recent_path):
        print(f"[!] Recent 폴더를 찾을 수 없음: {recent_path}")
        return []

    files = []
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

    try:
        # .lnk 파일들 조회
        lnk_files = glob.glob(os.path.join(recent_path, '*.lnk'))

        for lnk_path in lnk_files:
            try:
                # 파일 수정 시간
                mtime = os.path.getmtime(lnk_path)

                # 최근 N일 내의 파일만 (filter_date가 없을 때)
                if not filter_date and mtime < cutoff_time:
                    continue

                access_time = datetime.fromtimestamp(mtime)

                # filter_date가 있으면 해당 날짜만 필터링
                if filter_date:
                    access_date = access_time.strftime('%Y-%m-%d')
                    if access_date != filter_date:
                        continue

                # 대상 파일명 (바로가기 파일명에서 .lnk 제거)
                basename = os.path.basename(lnk_path)
                if basename.lower().endswith('.lnk'):
                    target_name = basename[:-4]
                else:
                    target_name = basename

                # 대상 경로 시도 (win32com 있으면)
                target_path = ''
                try:
                    import win32com.client
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(lnk_path)
                    target_path = shortcut.TargetPath
                except:
                    pass

                files.append({
                    'name': target_name,
                    'target_path': target_path,
                    'access_time': access_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'access_time_dt': access_time,
                    'extension': get_file_extension(target_name),
                    'category': categorize_file(target_name)
                })

            except Exception as e:
                continue

        # 시간순 정렬 (최신순)
        files.sort(key=lambda x: x.get('access_time_dt', datetime.min), reverse=True)

        if filter_date:
            print(f"[+] Recent 폴더: {len(files)}개 파일 ({filter_date})")
        else:
            print(f"[+] Recent 폴더: {len(files)}개 최근 파일 수집")

    except Exception as e:
        print(f"[!] Recent 폴더 읽기 실패: {e}")

    return files


def get_file_statistics(files: List[Dict]) -> Dict:
    """파일 접근 통계"""
    # 확장자별 통계
    ext_counts = Counter(f['extension'] for f in files)

    # 카테고리별 통계
    cat_counts = Counter(f['category'] for f in files)

    # 일별 통계
    daily_counts = Counter(f['access_time'][:10] for f in files)

    return {
        'by_extension': ext_counts.most_common(10),
        'by_category': cat_counts.most_common(),
        'by_date': sorted(daily_counts.items(), reverse=True)
    }


def get_recent_files_summary(filter_date: str = None) -> Dict:
    """최근 파일 접근 요약

    Args:
        filter_date: 특정 날짜만 필터링 (YYYY-MM-DD)

    Returns:
        파일 목록과 통계
    """
    files = get_recent_files(days=7, filter_date=filter_date)
    stats = get_file_statistics(files)

    return {
        'files': files,
        'stats': stats
    }


# 테스트용
if __name__ == '__main__':
    print("=" * 50)
    print("최근 파일 접근 기록 수집 테스트")
    print("=" * 50)

    summary = get_recent_files_summary()
    files = summary['files']
    stats = summary['stats']

    if files:
        print(f"\n[ 최근 열어본 파일 (상위 15개) ]")
        for f in files[:15]:
            print(f"  {f['name']}")
            print(f"      {f['access_time']} | {f['category']}")

        print(f"\n[ 파일 종류별 통계 ]")
        for cat, count in stats['by_category']:
            print(f"  {cat}: {count}개")

        print(f"\n[ 확장자별 통계 ]")
        for ext, count in stats['by_extension'][:10]:
            print(f"  {ext}: {count}개")
    else:
        print("\n최근 파일 기록이 없습니다.")
