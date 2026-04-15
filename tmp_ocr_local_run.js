const { spawn } = require('child_process');
const child = spawn('node', ['skills/ocr-local/scripts/ocr.js', '/tmp/ocr_local_test.png', '--lang', 'eng'], { stdio: 'inherit' });
child.on('exit', code => process.exit(code || 0));
