@echo off
echo Setting up Python and Node.js environments...

cd ..\..
python -m pip install -r requirements.txt -r requirements-dev.txt

cd frontend
call npm install

echo Environment setup completed!
pause
