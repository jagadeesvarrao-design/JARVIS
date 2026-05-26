Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & "python" & Chr(34) & " -m streamlit run dashboard.py", 0
Set WinScriptHost = Nothing