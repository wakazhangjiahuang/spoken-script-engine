// Compatibility test runner. Tests assert both single-platform and 18-script exports.
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON||'python3',[path.join(path.dirname(fileURLToPath(import.meta.url)),'test_v2.py')],{stdio:'inherit',env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}});
