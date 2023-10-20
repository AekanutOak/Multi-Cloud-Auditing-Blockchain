@echo off

:: Activate the virtual environment
call .venv\Scripts\activate


:: Start your Flask applications in separate windows without waiting
python "./init.py"
start cmd /c "python ./CSP/CSP-1.py"
start cmd /c "python ./CSP/CSP-2.py"
start cmd /c "python ./CSP/CSP-3.py"
start cmd /c "python ./utils/organizer.py"
start cmd /c "python ./utils/client.py"

:: Actions while Flask applications are running (optional)

:: Wait for user input or a specific condition to continue (optional)
echo When you terminate all other cmds, press any key to fully exit the program
pause

:: Actions after the Flask applications have started (optional)

:: Deactivate the virtual environment when you're done
call .venv\Scripts\deactivate
