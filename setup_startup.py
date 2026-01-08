"""
시작 프로그램 등록 스크립트
Windows 시작 시 PC Monitor 자동 실행 설정
"""

import os
import sys
import winreg


def get_python_path():
    """Python 실행 파일 경로"""
    return sys.executable


def get_script_path():
    """main.py 스크립트 경로"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')


def create_startup_vbs():
    """백그라운드 실행을 위한 VBS 스크립트 생성

    VBS를 사용하면 콘솔 창 없이 백그라운드 실행 가능
    """
    vbs_content = f'''
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw ""{get_script_path()}""", 0, False
'''

    vbs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_hidden.vbs')

    with open(vbs_path, 'w', encoding='utf-8') as f:
        f.write(vbs_content.strip())

    print(f"[+] VBS 스크립트 생성: {vbs_path}")
    return vbs_path


def register_startup(silent: bool = True):
    """Windows 시작 프로그램에 등록

    Args:
        silent: True면 콘솔 창 없이 실행
    """
    app_name = "PCMonitor"

    if silent:
        # VBS 스크립트로 백그라운드 실행
        vbs_path = create_startup_vbs()
        command = f'wscript.exe "{vbs_path}"'
    else:
        # 일반 실행 (콘솔 창 표시)
        python_path = get_python_path()
        script_path = get_script_path()
        command = f'"{python_path}" "{script_path}"'

    try:
        # 레지스트리에 시작 프로그램 등록
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)

        print(f"[+] 시작 프로그램 등록 완료!")
        print(f"    이름: {app_name}")
        print(f"    명령: {command}")
        print()
        print("    PC를 켤 때마다 자동으로 PC Monitor가 실행됩니다.")

        return True

    except Exception as e:
        print(f"[!] 시작 프로그램 등록 실패: {e}")
        return False


def unregister_startup():
    """시작 프로그램에서 제거"""
    app_name = "PCMonitor"

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)

        print(f"[+] 시작 프로그램에서 제거 완료!")
        return True

    except FileNotFoundError:
        print("[!] 등록된 시작 프로그램이 없습니다.")
        return False
    except Exception as e:
        print(f"[!] 시작 프로그램 제거 실패: {e}")
        return False


def check_startup():
    """시작 프로그램 등록 여부 확인"""
    app_name = "PCMonitor"

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        value, _ = winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)

        print(f"[+] 시작 프로그램에 등록되어 있습니다.")
        print(f"    명령: {value}")
        return True

    except FileNotFoundError:
        print("[!] 시작 프로그램에 등록되어 있지 않습니다.")
        return False
    except Exception as e:
        print(f"[!] 확인 실패: {e}")
        return False


def main():
    """메인 함수"""
    print()
    print("=" * 60)
    print("   PC Monitor - 시작 프로그램 설정")
    print("=" * 60)
    print()

    print("옵션을 선택하세요:")
    print("  1. 시작 프로그램에 등록 (백그라운드 실행)")
    print("  2. 시작 프로그램에 등록 (콘솔 창 표시)")
    print("  3. 시작 프로그램에서 제거")
    print("  4. 현재 상태 확인")
    print("  5. 취소")
    print()

    try:
        choice = input("선택 (1-5): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n취소됨")
        return

    print()

    if choice == '1':
        register_startup(silent=True)
    elif choice == '2':
        register_startup(silent=False)
    elif choice == '3':
        unregister_startup()
    elif choice == '4':
        check_startup()
    elif choice == '5':
        print("취소됨")
    else:
        print("잘못된 선택입니다.")


if __name__ == '__main__':
    main()
