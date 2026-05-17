# 启动 Chatbot 服务
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$Root\backend"
if (-not (Test-Path "$Root\.env")) {
    Write-Host "请先复制 .env.example 为 .env 并配置 DASHSCOPE_API_KEY" -ForegroundColor Yellow
}
$Python = "$Root\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "正在创建虚拟环境并安装依赖..." -ForegroundColor Cyan
    python -m venv "$Root\.venv"
    & $Python -m ensurepip --upgrade
    & $Python -m pip install -r "$Root\backend\requirements.txt"
}
# 结束占用 8000 端口的旧进程（避免跑到过期代码）
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$env:PYTHONPATH = "$Root\backend"
& $Python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
