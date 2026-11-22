function sca-start-backend {
    & 'D:\Technoporada\1POSORTOWANE\przepis-na-ciasto\rach-ciach-google-w-piach\OSZINT\SpectraCam-AIO\backend\env\Scripts\python.exe' 'D:\Technoporada\1POSORTOWANE\przepis-na-ciasto\rach-ciach-google-w-piach\OSZINT\SpectraCam-AIO\backend\main_backend.py'
}

function sca-start-backend-uvicorn {
    & 'D:\Technoporada\1POSORTOWANE\przepis-na-ciasto\rach-ciach-google-w-piach\OSZINT\SpectraCam-AIO\backend\env\Scripts\python.exe' -m uvicorn backend.main_backend:app --host 127.0.0.1 --port 8000 --reload
}

function sca-shell {
    # Open interactive powershell that inherits venv python on PATH
    Write-Host 'Starting PowerShell inside venv environment...'
    & 'D:\Technoporada\1POSORTOWANE\przepis-na-ciasto\rach-ciach-google-w-piach\OSZINT\SpectraCam-AIO\backend\env\Scripts\python.exe' -c "import os,sys;print('venv python:', sys.executable)"
    powershell
}

function sca-exit {
    Write-Host 'Closing SpectraCam-AIO session...'
    exit
}
