@echo off
REM set_gmail_env.bat - Windows helper script to set Gmail environment variables

echo.
echo 🔐 Gmail Environment Variables Setup
echo ==================================
echo.
echo This script helps you set environment variables for the Gmail article extractor.
echo These variables will be available for the current command prompt session.
echo.

REM Get Gmail username
if defined GMAIL_USERNAME (
    echo ✅ GMAIL_USERNAME already set: %GMAIL_USERNAME%
) else (
    set /p gmail_username="Enter your Gmail username: "
    if defined gmail_username (
        set GMAIL_USERNAME=%gmail_username%
        echo ✅ GMAIL_USERNAME set
    ) else (
        echo ❌ Gmail username is required
        exit /b 1
    )
)

REM Get Gmail password (hidden input)
if defined GMAIL_PASSWORD (
    echo ✅ GMAIL_PASSWORD already set ^(hidden^)
) else (
    echo Enter your Gmail app password:
    set /p GMAIL_PASSWORD=
    if defined GMAIL_PASSWORD (
        echo ✅ GMAIL_PASSWORD set
    ) else (
        echo ❌ Gmail password is required
        exit /b 1
    )
)

REM Get Gmail folder (optional)
if defined GMAIL_FOLDER (
    echo ✅ GMAIL_FOLDER already set: %GMAIL_FOLDER%
) else (
    set /p gmail_folder="Enter Gmail folder name (default: Medium): "
    if defined gmail_folder (
        set GMAIL_FOLDER=%gmail_folder%
    ) else (
        set GMAIL_FOLDER=Medium
    )
    echo ✅ GMAIL_FOLDER set to: %GMAIL_FOLDER%
)

echo.
echo 🎉 Environment variables are now set for this command prompt session!
echo.
echo To make these permanent, add these lines to your System Environment Variables:
echo   GMAIL_USERNAME=%GMAIL_USERNAME%
echo   GMAIL_PASSWORD=your-app-password
echo   GMAIL_FOLDER=%GMAIL_FOLDER%
echo.
echo Or use Windows Settings ^> System ^> About ^> System info ^> Advanced system settings
echo.
echo You can now run: python Read_Medium_From_Gmail.py
echo.
