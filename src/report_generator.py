"""
HTML 리포트 생성 모듈
수집된 데이터를 예쁜 HTML 리포트로 생성
"""

import os
import json
from datetime import datetime
from typing import Dict, List


def generate_html_report(data: Dict, output_path: str) -> str:
    """HTML 리포트 생성

    Args:
        data: 수집된 모든 데이터
        output_path: 저장할 파일 경로

    Returns:
        생성된 파일 경로
    """

    report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_date_short = datetime.now().strftime('%Y-%m-%d')

    # 데이터 추출
    browser_history = data.get('browser_history', [])
    domain_stats = data.get('domain_stats', [])
    app_usage = data.get('app_usage', {})
    pc_time = data.get('pc_time', {})
    recent_files = data.get('recent_files', {})
    roblox = data.get('roblox', {})

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PC 사용 리포트 - {report_date_short}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .header h1 {{
            color: #333;
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .header .date {{
            color: #666;
            font-size: 1.1em;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .summary-card .icon {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .summary-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }}
        .summary-card .label {{
            color: #666;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .scrollable {{
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #eee;
            border-radius: 10px;
            margin-top: 10px;
        }}
        .scrollable::-webkit-scrollbar {{
            width: 8px;
        }}
        .scrollable::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 4px;
        }}
        .scrollable::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }}
        .scrollable::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
        .scrollable table {{
            margin: 0;
        }}
        .game-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section h2 .emoji {{
            font-size: 1.3em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .domain-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .bar {{
            height: 20px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 10px;
        }}
        .event-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        .event-login {{ background: #d4edda; color: #155724; }}
        .event-logout {{ background: #f8d7da; color: #721c24; }}
        .event-start {{ background: #cce5ff; color: #004085; }}
        .event-shutdown {{ background: #fff3cd; color: #856404; }}
        .game-card {{
            display: flex;
            align-items: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 10px;
        }}
        .game-card .game-icon {{
            font-size: 2em;
            margin-right: 15px;
        }}
        .game-card .game-info h4 {{
            color: #333;
            margin-bottom: 5px;
        }}
        .game-card .game-info p {{
            color: #666;
            font-size: 0.9em;
        }}
        .file-category {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            background: #e9ecef;
            color: #495057;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PC 사용 리포트</h1>
            <p class="date">생성일시: {report_date}</p>
        </div>

        <div class="summary-cards">
            <div class="summary-card">
                <div class="icon">🌐</div>
                <div class="value">{len(browser_history)}</div>
                <div class="label">웹사이트 방문</div>
            </div>
            <div class="summary-card">
                <div class="icon">⏱️</div>
                <div class="value">{pc_time.get('uptime', 'N/A')}</div>
                <div class="label">오늘 PC 사용</div>
            </div>
            <div class="summary-card">
                <div class="icon">📁</div>
                <div class="value">{len(recent_files.get('files', []))}</div>
                <div class="label">최근 파일</div>
            </div>
            <div class="summary-card">
                <div class="icon">🎮</div>
                <div class="value">{roblox.get('total_games', 0)}</div>
                <div class="label">로블록스 게임</div>
            </div>
        </div>

        <!-- 브라우저 방문 기록 -->
        <div class="section">
            <h2><span class="emoji">🌐</span> 웹사이트 방문 통계</h2>
            {generate_domain_stats_html(domain_stats)}
        </div>

        <!-- 최근 방문 기록 -->
        <div class="section">
            <h2><span class="emoji">📋</span> 최근 방문 기록</h2>
            {generate_browser_history_html(browser_history[:30])}
        </div>

        <!-- PC 사용 시간 -->
        <div class="section">
            <h2><span class="emoji">⏱️</span> PC 사용 시간</h2>
            {generate_pc_time_html(pc_time)}
        </div>

        <!-- 로블록스 게임 -->
        <div class="section">
            <h2><span class="emoji">🎮</span> 로블록스 게임 기록</h2>
            {generate_roblox_html(roblox)}
        </div>

        <!-- 프로그램 실행 기록 -->
        <div class="section">
            <h2><span class="emoji">💻</span> 프로그램 실행 기록</h2>
            {generate_app_usage_html(app_usage)}
        </div>

        <!-- 최근 파일 -->
        <div class="section">
            <h2><span class="emoji">📁</span> 최근 열어본 파일</h2>
            {generate_recent_files_html(recent_files)}
        </div>

        <div class="footer">
            <p>PC Monitor - 자녀 PC 사용 모니터링 도구</p>
            <p>Generated by Claude Code</p>
        </div>
    </div>
</body>
</html>
'''

    # 파일 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[+] HTML 리포트 생성 완료: {output_path}")
    return output_path


def generate_domain_stats_html(stats: List[Dict]) -> str:
    """도메인 통계 HTML 생성"""
    if not stats:
        return '<div class="no-data">방문 기록이 없습니다.</div>'

    max_count = max(s['visit_count'] for s in stats) if stats else 1

    rows = []
    for stat in stats[:15]:
        bar_width = int((stat['visit_count'] / max_count) * 200)
        rows.append(f'''
            <tr>
                <td><strong>{stat['domain']}</strong></td>
                <td>
                    <div class="domain-bar">
                        <div class="bar" style="width: {bar_width}px;"></div>
                        <span>{stat['visit_count']}회</span>
                    </div>
                </td>
            </tr>
        ''')

    return f'''
        <div class="scrollable">
        <table>
            <thead>
                <tr>
                    <th>도메인</th>
                    <th>방문 횟수</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        </div>
    '''


def generate_browser_history_html(history: List[Dict]) -> str:
    """브라우저 기록 HTML 생성"""
    if not history:
        return '<div class="no-data">방문 기록이 없습니다.</div>'

    rows = []
    for item in history:
        title = item.get('title', '')[:50]
        if len(item.get('title', '')) > 50:
            title += '...'
        rows.append(f'''
            <tr>
                <td>{item.get('last_visit', '')}</td>
                <td><strong>{title}</strong></td>
                <td>{item.get('domain', '')}</td>
            </tr>
        ''')

    return f'''
        <div class="scrollable">
        <table>
            <thead>
                <tr>
                    <th>시간</th>
                    <th>제목</th>
                    <th>도메인</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        </div>
    '''


def generate_pc_time_html(pc_time: Dict) -> str:
    """PC 사용 시간 HTML 생성"""
    events = pc_time.get('events', [])

    info_html = f'''
        <p style="margin-bottom: 20px; font-size: 1.1em;">
            <strong>부팅 시간:</strong> {pc_time.get('boot_time', 'N/A')} &nbsp;|&nbsp;
            <strong>현재 가동 시간:</strong> {pc_time.get('uptime', 'N/A')}
        </p>
    '''

    if not events:
        return info_html + '<div class="no-data">이벤트 기록이 없습니다.</div>'

    rows = []
    for event in events[:20]:
        event_type = event.get('event_type', '')
        badge_class = {
            '로그온': 'event-login',
            '로그오프': 'event-logout',
            '시스템 시작': 'event-start',
            '시스템 종료': 'event-shutdown'
        }.get(event_type, '')

        rows.append(f'''
            <tr>
                <td>{event.get('time', '')}</td>
                <td><span class="event-badge {badge_class}">{event_type}</span></td>
            </tr>
        ''')

    return info_html + f'''
        <div class="scrollable">
        <table>
            <thead>
                <tr>
                    <th>시간</th>
                    <th>이벤트</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        </div>
    '''


def generate_roblox_html(roblox: Dict) -> str:
    """로블록스 게임 HTML 생성"""
    game_stats = roblox.get('game_stats', [])
    browser_records = roblox.get('browser_records', [])
    is_sample = roblox.get('is_sample', False)

    if not game_stats and not browser_records:
        return '<div class="no-data">로블록스 기록이 없습니다. (로블록스가 설치되지 않았거나 최근 플레이 기록 없음)</div>'

    # 샘플 데이터 표시
    sample_notice = ''
    if is_sample:
        sample_notice = '''
            <div style="background: #fff3cd; color: #856404; padding: 10px 15px; border-radius: 10px; margin-bottom: 15px;">
                ⚠️ 샘플 데이터입니다 (로블록스 설치 시 실제 데이터로 대체됨)
            </div>
        '''

    cards = []
    for game in game_stats:
        # 플레이 시간 표시 (있으면)
        time_info = ''
        if game.get('total_time_minutes'):
            hours = game['total_time_minutes'] // 60
            minutes = game['total_time_minutes'] % 60
            if hours > 0:
                time_info = f" | 총 {hours}시간 {minutes}분"
            else:
                time_info = f" | 총 {minutes}분"

        cards.append(f'''
            <div class="game-card">
                <div class="game-icon">🎮</div>
                <div class="game-info">
                    <h4>{game.get('game_name', '알 수 없는 게임')}</h4>
                    <p>접속 횟수: {game.get('play_count', 0)}회{time_info}</p>
                </div>
            </div>
        ''')

    # 브라우저에서 발견된 로블록스 방문도 추가
    for record in browser_records[:10]:
        cards.append(f'''
            <div class="game-card">
                <div class="game-icon">🌐</div>
                <div class="game-info">
                    <h4>{record.get('game_name', '알 수 없는 게임')}</h4>
                    <p>웹 방문: {record.get('visit_time', '')}</p>
                </div>
            </div>
        ''')

    content = ''.join(cards) if cards else '<div class="no-data">로블록스 기록이 없습니다.</div>'
    if cards:
        content = f'<div class="scrollable game-list">{content}</div>'
    return sample_notice + content


def generate_app_usage_html(app_usage: Dict) -> str:
    """프로그램 실행 기록 HTML 생성"""
    prefetch = app_usage.get('prefetch', [])

    if not prefetch:
        return '<div class="no-data">프로그램 실행 기록이 없습니다. (관리자 권한으로 실행하면 더 많은 정보를 볼 수 있습니다)</div>'

    rows = []
    for item in prefetch[:50]:  # 최대 50개로 증가
        run_count = item.get('run_count', '')
        run_count_str = f"{run_count}회" if run_count else ''

        rows.append(f'''
            <tr>
                <td><strong>{item.get('program', '')}</strong></td>
                <td>{run_count_str}</td>
                <td>{item.get('last_run', '')}</td>
            </tr>
        ''')

    return f'''
        <div class="scrollable">
        <table>
            <thead>
                <tr>
                    <th>프로그램</th>
                    <th>실행 횟수</th>
                    <th>마지막 실행</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        </div>
    '''


def generate_recent_files_html(recent_files: Dict) -> str:
    """최근 파일 HTML 생성"""
    files = recent_files.get('files', [])

    if not files:
        return '<div class="no-data">최근 파일 기록이 없습니다.</div>'

    rows = []
    for f in files[:50]:  # 최대 50개로 증가
        rows.append(f'''
            <tr>
                <td><strong>{f.get('name', '')}</strong></td>
                <td><span class="file-category">{f.get('category', '기타')}</span></td>
                <td>{f.get('access_time', '')}</td>
            </tr>
        ''')

    return f'''
        <div class="scrollable">
        <table>
            <thead>
                <tr>
                    <th>파일명</th>
                    <th>종류</th>
                    <th>접근 시간</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        </div>
    '''


def generate_dashboard_html(available_dates: List[str], output_path: str, show_days: int = 7) -> str:
    """날짜 선택 가능한 대시보드 HTML 생성

    Args:
        available_dates: 데이터가 있는 날짜 목록
        output_path: 저장할 파일 경로
        show_days: 표시할 최근 일수
    """
    from datetime import timedelta

    report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 최근 N일간의 날짜 생성 (데이터 유무와 관계없이)
    all_dates = []
    for i in range(show_days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        all_dates.append(date)

    # 날짜별 버튼 생성
    date_buttons = []
    for date in all_dates:
        has_data = date in available_dates
        if has_data:
            date_buttons.append(f'''
                <button class="date-btn" onclick="loadDate('{date}')">{date}</button>
            ''')
        else:
            date_buttons.append(f'''
                <button class="date-btn no-data" onclick="loadDate('{date}')" title="데이터 없음">{date} (없음)</button>
            ''')

    if not date_buttons:
        date_buttons_html = '<p style="color: #666;">저장된 데이터가 없습니다. 먼저 main.py를 실행하세요.</p>'
    else:
        date_buttons_html = ''.join(date_buttons)

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PC Monitor - 대시보드</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .header h1 {{ color: #333; font-size: 2em; margin-bottom: 10px; }}
        .header .subtitle {{ color: #666; font-size: 1em; }}
        .section {{
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .date-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .date-btn {{
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .date-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        .date-btn.active {{
            background: #28a745;
        }}
        .date-btn.no-data {{
            background: #ccc;
            color: #666;
        }}
        .date-btn.no-data:hover {{
            background: #bbb;
            box-shadow: none;
        }}
        #report-frame {{
            width: 100%;
            min-height: 800px;
            border: none;
            border-radius: 15px;
            background: white;
        }}
        .loading {{
            text-align: center;
            padding: 50px;
            color: #666;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PC Monitor 대시보드</h1>
            <p class="subtitle">날짜를 선택하여 PC 사용 기록을 확인하세요</p>
            <p class="subtitle" style="margin-top: 10px; font-size: 0.9em;">
                마지막 업데이트: {report_date}
            </p>
        </div>

        <div class="section">
            <h2>📅 날짜 선택</h2>
            <div class="date-buttons">
                {date_buttons_html}
            </div>
        </div>

        <div class="section" id="report-container">
            <h2>📊 리포트</h2>
            <div class="loading" id="loading-msg">
                위에서 날짜를 선택하세요
            </div>
            <iframe id="report-frame" style="display: none;"></iframe>
        </div>

        <div class="footer">
            <p>PC Monitor - 자녀 PC 사용 모니터링 도구</p>
            <p>Generated by Claude Code</p>
        </div>
    </div>

    <script>
        // 데이터가 있는 날짜 목록
        const availableDates = {json.dumps(available_dates)};

        // 날짜별 리포트 파일 로드
        function loadDate(date) {{
            const frame = document.getElementById('report-frame');
            const loading = document.getElementById('loading-msg');
            const reportFile = 'daily_' + date + '.html';

            // 버튼 활성화 표시
            document.querySelectorAll('.date-btn').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.textContent.startsWith(date)) {{
                    btn.classList.add('active');
                }}
            }});

            // 데이터가 없는 날짜인지 확인
            if (!availableDates.includes(date)) {{
                loading.innerHTML = '<div style="text-align:center; padding:50px; color:#666;"><h3>📭 ' + date + '</h3><p>이 날짜에는 수집된 데이터가 없습니다.</p><p style="margin-top:20px; font-size:0.9em;">PC를 사용하지 않았거나 PC Monitor가 실행되지 않았습니다.</p></div>';
                loading.style.display = 'block';
                frame.style.display = 'none';
                return;
            }}

            // 로딩 표시
            loading.textContent = '로딩 중...';
            loading.style.display = 'block';
            frame.style.display = 'none';

            // iframe에 리포트 로드
            frame.onload = function() {{
                loading.style.display = 'none';
                frame.style.display = 'block';
            }};
            frame.onerror = function() {{
                loading.innerHTML = '<div style="text-align:center; padding:50px; color:#666;"><p>리포트를 불러올 수 없습니다.</p></div>';
            }};
            frame.src = reportFile;
        }}

        // 가장 최근 데이터가 있는 날짜 자동 로드
        const firstBtn = document.querySelector('.date-btn:not(.no-data)');
        if (firstBtn) {{
            firstBtn.click();
        }}
    </script>
</body>
</html>
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[+] 대시보드 생성 완료: {output_path}")
    return output_path


# 테스트용
if __name__ == '__main__':
    # 샘플 데이터로 테스트
    sample_data = {
        'browser_history': [
            {'title': '테스트 페이지', 'domain': 'example.com', 'last_visit': '2024-01-08 10:00:00'},
        ],
        'domain_stats': [
            {'domain': 'google.com', 'visit_count': 50},
            {'domain': 'youtube.com', 'visit_count': 30},
        ],
        'pc_time': {
            'boot_time': '2024-01-08 08:00:00',
            'uptime': '5시간 30분',
            'events': []
        },
        'recent_files': {'files': []},
        'roblox': {'game_stats': [], 'total_games': 0},
        'app_usage': {'prefetch': []}
    }

    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'test_report.html')
    generate_html_report(sample_data, output_path)
