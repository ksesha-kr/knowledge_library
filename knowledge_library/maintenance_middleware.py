import os
from pathlib import Path
from django.http import HttpResponse
from django.utils import timezone


class MaintenanceModeMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        project_root = Path(__file__).parent.parent
        self.lock_file = project_root / 'maintenance.lock'

    def __call__(self, request):
        if self.lock_file.exists():
            if request.path.startswith('/admin/'):
                return self.get_response(request)

            if request.path in ['/accounts/login/', '/accounts/logout/', '/login/', '/logout/']:
                return self.get_response(request)

            return self.get_maintenance_response(request)

        return self.get_response(request)

    def get_maintenance_response(self, request):

        file_time = ""
        if self.lock_file.exists():
            mtime = self.lock_file.stat().st_mtime
            from datetime import datetime
            file_time = datetime.fromtimestamp(mtime).strftime('%d.%m.%Y %H:%M')

        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ведется техническая работа</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                    padding: 20px;
                }}
                .maintenance-card {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 700px;
                    width: 100%;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    text-align: center;
                    animation: fadeIn 0.5s ease-out;
                }}
                @keyframes fadeIn {{
                    from {{ opacity: 0; transform: translateY(-20px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
                .maintenance-icon {{
                    font-size: 80px;
                    color: #667eea;
                    margin-bottom: 20px;
                    animation: pulse 2s infinite;
                }}
                @keyframes pulse {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.1); }}
                    100% {{ transform: scale(1); }}
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                    font-weight: 700;
                }}
                .status-badge {{
                    background: #ff6b6b;
                    color: white;
                    padding: 8px 20px;
                    border-radius: 50px;
                    font-weight: 600;
                    display: inline-block;
                    margin-bottom: 25px;
                }}
                .info-box {{
                    background: #f8f9fa;
                    border-radius: 15px;
                    padding: 25px;
                    margin: 25px 0;
                    border-left: 5px solid #667eea;
                }}
                .progress-container {{
                    background: #e9ecef;
                    border-radius: 10px;
                    height: 10px;
                    margin: 30px 0;
                    overflow: hidden;
                }}
                .progress-bar {{
                    background: linear-gradient(90deg, #3b82f6, #2563eb);
                    height: 100%;
                    width: 65%;
                    animation: loading 2s infinite alternate;
                }}
                @keyframes loading {{
                    0% {{ width: 65%; }}
                    100% {{ width: 75%; }}
                }}
                .admin-note {{
                    margin-top: 30px;
                    padding: 20px;
                    background: #e3f2fd;
                    border-radius: 15px;
                    font-size: 0.9em;
                    text-align: left;
                }}
                code {{
                    background: #2d3748;
                    color: #e2e8f0;
                    padding: 10px 15px;
                    border-radius: 8px;
                    font-family: 'Courier New', monospace;
                    display: block;
                    margin: 10px 0;
                    white-space: nowrap;
                    overflow-x: auto;
                }}
            </style>
        </head>
        <body>
            <div class="maintenance-card">
                <div class="maintenance-icon">
                    <i class="bi bi-tools"></i>
                </div>

                <div class="status-badge">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    РЕЖИМ ОБСЛУЖИВАНИЯ
                </div>

                <h1>Ведется техническая работа</h1>

                <p class="lead" style="color: #666; line-height: 1.6; font-size: 1.1em;">
                    В настоящее время проводятся плановые технические работы на сайте.
                    Мы улучшаем систему для вашего удобства.
                </p>

                <div class="info-box">
                    <div class="row text-center">
                        <div class="col-md-4 mb-3">
                            <div style="font-size: 2em; color: #667eea; font-weight: bold;">🕐</div>
                            <div style="color: #555;">Ожидаемое время</div>
                            <div style="font-weight: 600; color: #333;">30-60 минут</div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <div style="font-size: 2em; color: #667eea; font-weight: bold;">📅</div>
                            <div style="color: #555;">Дата начала работ</div>
                            <div style="font-weight: 600; color: #333;">{file_time if file_time else 'Сегодня'}</div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <div style="font-size: 2em; color: #667eea; font-weight: bold;">✅</div>
                            <div style="color: #555;">Статус</div>
                            <div style="font-weight: 600; color: #333;">Активные работы</div>
                        </div>
                    </div>
                </div>

                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>

                <p style="color: #777; font-size: 0.95em; margin-bottom: 10px;">
                    <i class="bi bi-arrow-repeat me-1"></i>
                    Страница автоматически обновится, когда работы будут завершены
                </p>

                <div style="margin-top: 30px; color: #888; font-size: 0.9em;">
                    <i class="bi bi-heart-fill text-danger me-1"></i>
                    Спасибо за ваше терпение! Мы работаем для вас.
                </div>
            </div>

            <script>
            setInterval(function() {{
                fetch(window.location.href)
                    .then(response => {{
                        if (response.status !== 503) {{
                            location.reload();
                        }}
                    }})
                    .catch(error => console.log('Проверка статуса...'));
            }}, 30000); 

            function updateTime() {{
                const now = new Date();
                const timeString = now.toLocaleTimeString('ru-RU');
                const dateString = now.toLocaleDateString('ru-RU');
                document.getElementById('current-time').textContent = 
                    `Текущее время: ${{dateString}} ${{timeString}}`;
            }}

            setInterval(updateTime, 1000);
            updateTime();
            </script>

            <div style="position: fixed; bottom: 15px; right: 15px; color: rgba(255,255,255,0.7); font-size: 0.8em;">
                <span id="current-time"></span>
            </div>
        </body>
        </html>
        """

        return HttpResponse(html, status=503, content_type='text/html')