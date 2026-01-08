"""
이메일 발송 모듈
Gmail SMTP를 사용하여 일일 리포트 발송
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, Optional


# 이메일 설정 (사용 전 수정 필요)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': '',      # 발신자 Gmail 주소
    'sender_password': '',   # Gmail 앱 비밀번호 (16자리)
    'receiver_email': '',    # 수신자 이메일 주소
}


def load_email_config() -> Dict:
    """설정 파일에서 이메일 설정 로드"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'email_config.txt')

    config = EMAIL_CONFIG.copy()

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key in config:
                            config[key] = value
        except Exception as e:
            print(f"[!] 이메일 설정 파일 읽기 실패: {e}")

    return config


def create_summary_html(data: Dict, date: str) -> str:
    """데이터 요약 HTML 생성"""

    # 통계 계산
    browser_count = len(data.get('browser_history', []))
    app_count = len(data.get('app_usage', {}).get('prefetch', []))
    file_count = len(data.get('recent_files', {}).get('files', []))

    # 상위 도메인
    domain_stats = data.get('domain_stats', [])[:5]
    domain_list = ''.join([
        f"<li>{domain}: {count}회</li>"
        for domain, count in domain_stats
    ]) if domain_stats else "<li>기록 없음</li>"

    # 상위 프로그램
    apps = data.get('app_usage', {}).get('prefetch', [])[:5]
    app_list = ''.join([
        f"<li>{app.get('program', 'Unknown')}</li>"
        for app in apps
    ]) if apps else "<li>기록 없음</li>"

    # PC 사용 시간
    pc_time = data.get('pc_time', {})
    boot_time = pc_time.get('boot_time', '알 수 없음')
    uptime = pc_time.get('uptime', '알 수 없음')
    events = pc_time.get('events', [])
    event_count = len(events)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
            h2 {{ color: #333; margin-top: 25px; }}
            .stat-box {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 25px; border-radius: 10px; margin: 5px; text-align: center; }}
            .stat-number {{ font-size: 24px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; opacity: 0.9; }}
            ul {{ padding-left: 20px; }}
            li {{ margin: 5px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PC Monitor 일일 리포트</h1>
            <p><strong>날짜:</strong> {date}</p>
            <p><strong>생성 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <h2>요약</h2>
            <div>
                <div class="stat-box">
                    <div class="stat-number">{browser_count}</div>
                    <div class="stat-label">웹사이트 방문</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{app_count}</div>
                    <div class="stat-label">프로그램 실행</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{file_count}</div>
                    <div class="stat-label">파일 접근</div>
                </div>
            </div>

            <h2>PC 사용 시간</h2>
            <p><strong>부팅 시간:</strong> {boot_time}</p>
            <p><strong>가동 시간:</strong> {uptime}</p>
            <p><strong>로그인/로그아웃:</strong> {event_count}회</p>

            <h2>자주 방문한 사이트 (Top 5)</h2>
            <ul>{domain_list}</ul>

            <h2>실행한 프로그램 (Top 5)</h2>
            <ul>{app_list}</ul>

            <div class="footer">
                <p>PC Monitor - 자녀 PC 사용 모니터링 도구</p>
                <p>자세한 내용은 첨부된 리포트를 확인하세요.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_email(data: Dict, date: str, report_path: Optional[str] = None) -> bool:
    """이메일 발송

    Args:
        data: 수집된 데이터
        date: 리포트 날짜
        report_path: HTML 리포트 파일 경로 (첨부용)

    Returns:
        발송 성공 여부
    """
    config = load_email_config()

    # 설정 확인
    if not config['sender_email'] or not config['sender_password']:
        print("[!] 이메일 설정이 필요합니다. email_config.txt 파일을 확인하세요.")
        return False

    if not config['receiver_email']:
        config['receiver_email'] = config['sender_email']  # 기본값: 자신에게 발송

    try:
        # 이메일 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[PC Monitor] {date} 일일 리포트"
        msg['From'] = config['sender_email']
        msg['To'] = config['receiver_email']

        # HTML 본문
        html_content = create_summary_html(data, date)
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # 리포트 파일 첨부
        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename="daily_{date}.html"'
                )
                msg.attach(attachment)

        # SMTP 연결 및 발송
        print(f"[*] 이메일 발송 중... ({config['receiver_email']})")

        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)

        print(f"[+] 이메일 발송 완료!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[!] 이메일 인증 실패. Gmail 앱 비밀번호를 확인하세요.")
        print("    (https://myaccount.google.com/apppasswords 에서 생성)")
        return False
    except Exception as e:
        print(f"[!] 이메일 발송 실패: {e}")
        return False


def test_email_config() -> bool:
    """이메일 설정 테스트"""
    config = load_email_config()

    print("\n[이메일 설정 테스트]")
    print(f"  발신자: {config['sender_email'] or '(미설정)'}")
    print(f"  수신자: {config['receiver_email'] or '(미설정)'}")
    print(f"  비밀번호: {'****' if config['sender_password'] else '(미설정)'}")

    if not config['sender_email'] or not config['sender_password']:
        print("\n[!] email_config.txt 파일에 설정을 입력하세요.")
        return False

    # 테스트 이메일 발송
    try:
        msg = MIMEText("PC Monitor 이메일 테스트입니다.", 'plain', 'utf-8')
        msg['Subject'] = "[PC Monitor] 이메일 설정 테스트"
        msg['From'] = config['sender_email']
        msg['To'] = config['receiver_email'] or config['sender_email']

        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)

        print("\n[+] 테스트 이메일 발송 성공!")
        return True

    except Exception as e:
        print(f"\n[!] 테스트 실패: {e}")
        return False


# 테스트용
if __name__ == '__main__':
    test_email_config()
