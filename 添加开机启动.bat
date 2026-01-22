@echo off
set "startup=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "target=%~dp0main.pyw"
set "shortcut=%startup%\QuickImage.lnk"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%shortcut%'); $s.TargetPath = '%target%'; $s.WorkingDirectory = '%~dp0'; $s.Save()"

if exist "%shortcut%" (
    echo 已添加开机自启动!
) else (
    echo 添加失败，请手动操作：
    echo 1. 按 Win+R，输入 shell:startup
    echo 2. 把 main.pyw 的快捷方式复制进去
)
pause
