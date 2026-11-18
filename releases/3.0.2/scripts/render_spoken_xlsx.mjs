// Compatibility entry point; the sole v2 export contract lives in export_xlsx.py.
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const script=path.join(path.dirname(fileURLToPath(import.meta.url)),'export_xlsx.py');
execFileSync(process.env.CODEX_PRIMARY_RUNTIME_PYTHON||'python3',[script,...process.argv.slice(2)],{stdio:'inherit'});
