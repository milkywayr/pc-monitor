"""
프로그램 실행 기록 수집 모듈
Windows Prefetch 폴더와 최근 실행 기록 분석
"""

import os
import glob
from datetime import datetime
from typing import List, Dict
from collections import Counter
import ctypes
import struct


def get_prefetch_path() -> str:
    """Prefetch 폴더 경로 반환"""
    windows_dir = os.environ.get('WINDIR', 'C:\\Windows')
    return os.path.join(windows_dir, 'Prefetch')


def parse_prefetch_filename(filename: str) -> Dict:
    """Prefetch 파일명에서 프로그램 정보 추출

    Prefetch 파일명 형식: PROGRAMNAME-XXXXXXXX.pf
    """
    basename = os.path.basename(filename)

    if not basename.upper().endswith('.PF'):
        return None

    # 확장자 제거
    name_part = basename[:-3]

    # 마지막 '-' 기준으로 분리 (해시값 분리)
    if '-' in name_part:
        parts = name_part.rsplit('-', 1)
        program_name = parts[0]
    else:
        program_name = name_part

    # 파일 수정 시간 = 마지막 실행 시간
    try:
        mtime = os.path.getmtime(filename)
        last_run = datetime.fromtimestamp(mtime)
    except:
        last_run = None

    # 파일 생성 시간 = 첫 실행 시간
    try:
        ctime = os.path.getctime(filename)
        first_run = datetime.fromtimestamp(ctime)
    except:
        first_run = None

    return {
        'program': program_name,
        'filename': basename,
        'last_run': last_run.strftime('%Y-%m-%d %H:%M:%S') if last_run else '',
        'first_run': first_run.strftime('%Y-%m-%d %H:%M:%S') if first_run else '',
        'last_run_dt': last_run
    }


def get_prefetch_records() -> List[Dict]:
    """Prefetch 폴더에서 실행 기록 수집

    주의: Prefetch 폴더 접근에는 관리자 권한이 필요할 수 있음
    """
    prefetch_path = get_prefetch_path()

    if not os.path.exists(prefetch_path):
        print(f"[!] Prefetch 폴더를 찾을 수 없음: {prefetch_path}")
        return []

    records = []

    try:
        pf_files = glob.glob(os.path.join(prefetch_path, '*.pf'))

        for pf_file in pf_files:
            info = parse_prefetch_filename(pf_file)
            if info:
                records.append(info)

        # 최근 실행 순으로 정렬
        records.sort(key=lambda x: x.get('last_run_dt') or datetime.min, reverse=True)

        print(f"[+] Prefetch: {len(records)}개 프로그램 기록 수집")

    except PermissionError:
        print("[!] Prefetch 폴더 접근 권한 없음 (관리자 권한 필요)")
    except Exception as e:
        print(f"[!] Prefetch 읽기 실패: {e}")

    return records


def rot13_decode(text: str) -> str:
    """ROT13 디코딩 (UserAssist 키 이름 해독용)"""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(char)
    return ''.join(result)


def parse_userassist_data(data: bytes) -> Dict:
    """UserAssist 바이너리 데이터 파싱"""
    if len(data) < 16:
        return None

    try:
        # UserAssist 데이터 구조 (Windows 7+)
        # Offset 4: 실행 횟수 (4 bytes)
        # Offset 60: 마지막 실행 시간 (8 bytes, FILETIME)
        run_count = struct.unpack('<I', data[4:8])[0]

        # FILETIME을 datetime으로 변환
        if len(data) >= 68:
            filetime = struct.unpack('<Q', data[60:68])[0]
            if filetime > 0:
                # FILETIME: 1601-01-01부터 100나노초 단위
                seconds = filetime / 10000000 - 11644473600
                if seconds > 0:
                    last_run = datetime.fromtimestamp(seconds)
                else:
                    last_run = None
            else:
                last_run = None
        else:
            last_run = None

        return {
            'run_count': run_count,
            'last_run': last_run
        }
    except:
        return None


def get_userassist_records() -> List[Dict]:
    """UserAssist 레지스트리에서 프로그램 실행 기록 수집

    UserAssist는 Windows Shell에서 실행한 프로그램 기록을 저장
    관리자 권한 없이 접근 가능
    """
    records = []

    try:
        import winreg

        # UserAssist GUID (실행 파일용)
        guids = [
            "{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}",  # 실행 파일
            "{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}",  # 바로가기
        ]

        base_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"

        for guid in guids:
            try:
                key_path = f"{base_path}\\{guid}\\Count"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)

                i = 0
                while True:
                    try:
                        name, value, value_type = winreg.EnumValue(key, i)

                        # ROT13 디코딩
                        decoded_name = rot13_decode(name)

                        # 바이너리 데이터 파싱
                        if isinstance(value, bytes):
                            parsed = parse_userassist_data(value)
                            if parsed and parsed['run_count'] > 0:
                                # 프로그램 이름 추출
                                program_name = decoded_name
                                # 경로에서 파일명만 추출
                                if '\\' in program_name:
                                    program_name = program_name.split('\\')[-1]
                                if '/' in program_name:
                                    program_name = program_name.split('/')[-1]

                                records.append({
                                    'program': program_name,
                                    'full_path': decoded_name,
                                    'run_count': parsed['run_count'],
                                    'last_run': parsed['last_run'].strftime('%Y-%m-%d %H:%M:%S') if parsed['last_run'] else '',
                                    'last_run_dt': parsed['last_run'],
                                    'source': 'UserAssist'
                                })

                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(key)
            except FileNotFoundError:
                continue
            except Exception as e:
                continue

        # 최근 실행 순으로 정렬
        records.sort(key=lambda x: x.get('last_run_dt') or datetime.min, reverse=True)
        print(f"[+] UserAssist: {len(records)}개 프로그램 기록 수집")

    except Exception as e:
        print(f"[!] UserAssist 읽기 실패: {e}")

    return records


def get_recent_apps_from_registry() -> List[Dict]:
    """레지스트리에서 최근 실행 앱 목록 수집"""
    records = []

    try:
        import winreg

        # 최근 실행한 프로그램 목록 (Run MRU)
        key_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU",
        ]

        for key_path in key_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if name != 'MRUList' and isinstance(value, str):
                            # 마지막 \1 제거
                            clean_value = value.rstrip('\\1')
                            records.append({
                                'program': clean_value,
                                'source': 'RunMRU'
                            })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except FileNotFoundError:
                continue

        print(f"[+] Registry RunMRU: {len(records)}개 기록 수집")

    except Exception as e:
        print(f"[!] 레지스트리 읽기 실패: {e}")

    return records


def get_installed_apps() -> List[Dict]:
    """설치된 프로그램 목록 (참고용)"""
    apps = []

    try:
        import winreg

        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for hkey, path in paths:
            try:
                key = winreg.OpenKey(hkey, path)
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)

                        try:
                            name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if name:
                                apps.append({'name': name})
                        except FileNotFoundError:
                            pass

                        winreg.CloseKey(subkey)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except FileNotFoundError:
                continue

    except Exception as e:
        print(f"[!] 설치 프로그램 목록 읽기 실패: {e}")

    # 중복 제거
    seen = set()
    unique_apps = []
    for app in apps:
        if app['name'] not in seen:
            seen.add(app['name'])
            unique_apps.append(app)

    return unique_apps


def get_bam_records() -> List[Dict]:
    """BAM (Background Activity Moderator) 레지스트리에서 실행 기록 수집

    Windows 10 1709+ 에서 사용 가능
    모든 실행된 프로그램을 기록함 (UserAssist보다 더 포괄적)
    """
    records = []

    try:
        import winreg

        # BAM 레지스트리 경로
        bam_paths = [
            r"SYSTEM\CurrentControlSet\Services\bam\State\UserSettings",
            r"SYSTEM\CurrentControlSet\Services\bam\UserSettings",
        ]

        for bam_base in bam_paths:
            try:
                base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, bam_base)

                # 사용자 SID 서브키 탐색
                i = 0
                while True:
                    try:
                        sid = winreg.EnumKey(base_key, i)
                        user_key = winreg.OpenKey(base_key, sid)

                        j = 0
                        while True:
                            try:
                                name, value, value_type = winreg.EnumValue(user_key, j)

                                # 실행 파일 경로 필터링
                                if '\\' in name and ('.exe' in name.lower() or '.lnk' in name.lower()):
                                    # 경로에서 파일명 추출
                                    program_name = name.split('\\')[-1]

                                    # 마지막 실행 시간 파싱
                                    last_run = None
                                    if isinstance(value, bytes) and len(value) >= 8:
                                        try:
                                            filetime = struct.unpack('<Q', value[:8])[0]
                                            if filetime > 0:
                                                seconds = filetime / 10000000 - 11644473600
                                                if seconds > 0:
                                                    last_run = datetime.fromtimestamp(seconds)
                                        except:
                                            pass

                                    if last_run:
                                        records.append({
                                            'program': program_name,
                                            'full_path': name,
                                            'last_run': last_run.strftime('%Y-%m-%d %H:%M:%S'),
                                            'last_run_dt': last_run,
                                            'source': 'BAM'
                                        })

                                j += 1
                            except OSError:
                                break

                        winreg.CloseKey(user_key)
                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(base_key)
            except (FileNotFoundError, PermissionError):
                continue

        # 최근 실행 순으로 정렬
        records.sort(key=lambda x: x.get('last_run_dt') or datetime.min, reverse=True)
        print(f"[+] BAM: {len(records)}개 프로그램 기록 수집")

    except Exception as e:
        print(f"[!] BAM 읽기 실패: {e}")

    return records


def filter_by_date(records: List[Dict], filter_date: str) -> List[Dict]:
    """특정 날짜의 기록만 필터링

    Args:
        records: 기록 목록
        filter_date: 필터링할 날짜 (YYYY-MM-DD)

    Returns:
        해당 날짜의 기록만 포함된 목록
    """
    if not filter_date:
        return records

    filtered = []
    for record in records:
        last_run_dt = record.get('last_run_dt')
        if last_run_dt:
            record_date = last_run_dt.strftime('%Y-%m-%d')
            if record_date == filter_date:
                filtered.append(record)

    return filtered


def get_all_app_usage(filter_date: str = None) -> Dict:
    """모든 프로그램 실행 기록 수집

    Args:
        filter_date: 특정 날짜만 필터링 (YYYY-MM-DD), None이면 모든 기록

    Returns:
        프로그램 실행 기록 딕셔너리
    """
    # Prefetch (관리자 권한 필요)
    prefetch = get_prefetch_records()

    # UserAssist (관리자 권한 불필요)
    userassist = get_userassist_records()

    # BAM (더 포괄적인 기록)
    bam = get_bam_records()

    # RunMRU
    run_mru = get_recent_apps_from_registry()

    # 날짜 필터링 적용
    if filter_date:
        prefetch = filter_by_date(prefetch, filter_date)
        userassist = filter_by_date(userassist, filter_date)
        bam = filter_by_date(bam, filter_date)
        print(f"[+] 날짜 필터링 적용: {filter_date}")
        print(f"    - Prefetch: {len(prefetch)}개, UserAssist: {len(userassist)}개, BAM: {len(bam)}개")

    # 모든 기록 병합 (중복 제거)
    all_records = []
    seen_programs = set()

    # BAM 우선 (가장 최신 정보)
    for record in bam:
        prog = record.get('program', '').lower()
        if prog and prog not in seen_programs:
            seen_programs.add(prog)
            all_records.append(record)

    # UserAssist 추가
    for record in userassist:
        prog = record.get('program', '').lower()
        if prog and prog not in seen_programs:
            seen_programs.add(prog)
            all_records.append(record)

    # Prefetch 추가
    for record in prefetch:
        prog = record.get('program', '').lower()
        if prog and prog not in seen_programs:
            seen_programs.add(prog)
            all_records.append(record)

    # 최근 실행 순 정렬
    all_records.sort(key=lambda x: x.get('last_run_dt') or datetime.min, reverse=True)

    # Prefetch가 없으면 병합된 기록 사용
    if not prefetch:
        prefetch = all_records

    return {
        'prefetch': prefetch,
        'userassist': userassist,
        'bam': bam,
        'run_mru': run_mru,
    }


def filter_common_programs(records: List[Dict]) -> List[Dict]:
    """일반적인/시스템 프로그램 필터링 (사용자 프로그램만)"""
    # 시스템 프로그램 제외 패턴
    system_patterns = [
        'DLLHOST', 'SVCHOST', 'CSRSS', 'CONHOST', 'TASKHOST',
        'WUDFHOST', 'SIHOST', 'CTFMON', 'DWMEXE', 'FONTDRVHOST',
        'SEARCHPROTOCOLHOST', 'SEARCHFILTERHOST', 'SEARCHINDEXER',
        'WMIPRVSE', 'RUNTIMEBROKER', 'SHELLEXPERIENCEHOST',
        'APPLICATIONFRAMEHOST', 'SYSTEMSETTINGS', 'LOCKAPP',
    ]

    filtered = []
    for record in records:
        program = record.get('program', '').upper()
        is_system = any(pattern in program for pattern in system_patterns)
        if not is_system:
            filtered.append(record)

    return filtered


# 테스트용
if __name__ == '__main__':
    print("=" * 50)
    print("프로그램 실행 기록 수집 테스트")
    print("=" * 50)

    data = get_all_app_usage()

    prefetch = data['prefetch']
    if prefetch:
        # 시스템 프로그램 필터링
        user_apps = filter_common_programs(prefetch)

        print(f"\n[ 최근 실행 프로그램 (상위 20개) ]")
        for item in user_apps[:20]:
            print(f"  {item['program']}")
            print(f"      마지막 실행: {item['last_run']}")
    else:
        print("\nPrefetch 기록이 없습니다 (관리자 권한으로 실행 필요)")

    run_mru = data['run_mru']
    if run_mru:
        print(f"\n[ 실행 명령 기록 ]")
        for item in run_mru:
            print(f"  {item['program']}")
