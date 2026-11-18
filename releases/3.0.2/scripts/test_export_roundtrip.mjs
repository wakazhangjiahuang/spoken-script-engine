// Compatibility test runner. Tests assert both single-platform and 18-script exports.
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const dir = path.dirname(fileURLToPath(import.meta.url));
const python = process.env.CODEX_PRIMARY_RUNTIME_PYTHON || 'python3';
const env = {...process.env, PYTHONDONTWRITEBYTECODE:'1'};
execFileSync(python,[path.join(dir,'test_layout_contract.py')],{stdio:'inherit',env});
execFileSync(python,[path.join(dir,'test_v2.py')],{stdio:'inherit',env});
