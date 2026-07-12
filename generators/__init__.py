# OMEN Generator Base Module
from abc import ABC, abstractmethod
import random
import string
import base64

class Generator(ABC):
    """Base class for all artifact generators."""

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def description(self):
        pass

    def get_options_schema(self):
        """Return JSON schema of configurable options."""
        return {}

    def get_obfuscation_levels(self):
        return ['none', 'base64', 'xor', 'aes', 'full']

    @abstractmethod
    def generate(self, options, obfuscation='none'):
        """Generate artifact. Returns dict with filename, content, preview, mime."""
        pass

    def obfuscate(self, text, level):
        """Apply obfuscation to generated text."""
        if level == 'none':
            return text
        elif level == 'base64':
            return f'/* Base64 encoded */\n{base64.b64encode(text.encode()).decode()}'
        elif level == 'xor':
            key = ''.join(random.choices(string.ascii_letters, k=random.randint(4, 12)))
            xored = ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))
            encoded = base64.b64encode(xored.encode('latin-1')).decode()
            return f'/* XOR key: "{key}" */\nvar _k="{key}",_d="{encoded}",_r="";for(var _i=0;_i<_d.length;_i++)_r+=String.fromCharCode(atob(_d).charCodeAt(_i)^_k.charCodeAt(_i%_k.length));eval?_r:eval(_r);'
        elif level == 'aes':
            from hashlib import sha256
            key = sha256(b'OMEN_GEN_KEY').digest()
            # Simplified: just base64 with wrapper
            encoded = base64.b64encode(text.encode()).decode()
            return f'/* AES-encrypted payload */\nvar _e="{encoded}",_d=atob(_e);eval(_d);'
        elif level == 'full':
            return self.obfuscate(self._inject_junk(self._randomize_vars(text)), 'xor')
        return text

    def _inject_junk(self, text, density=0.15):
        """Inject dead code / junk variables."""
        if not text:
            return text
        junk_vars = ['_t', '_x', '_q', 'a1', 'b2', 'c3', '_temp', '_z']
        junk_vals = ['0', '1', '"x"', 'null', 'void(0)', 'Math.random()', 'true', 'false']
        lines = text.split('\n')
        result = []
        junk_count = max(1, int(len(lines) * density))
        injected = 0
        for line in lines:
            result.append(line)
            if injected < junk_count and random.random() < density and line.strip():
                jv = random.choice(junk_vars)
                jval = random.choice(junk_vals)
                result.append(f'var {jv}=void 0;void({jv}={jval});')
                result.append(f'if({jv}){{;}}')
                injected += 1
        return '\n'.join(result)

    def _randomize_vars(self, text):
        """Randomize variable names in simple scripts."""
        # Simple variable name substitution for common patterns
        var_map = {}
        import re
        def replace_var(match):
            name = match.group(1)
            if name not in var_map:
                var_map[name] = '_' + ''.join(random.choices(string.ascii_lowercase, k=6))
            return match.group(0).replace(name, var_map[name])
        text = re.sub(r'\b(var|let|const)\s+(\w+)', replace_var, text)
        return text

    def _generate_random_string(self, length=8):
        return ''.join(random.choices(string.ascii_lowercase, k=length))
