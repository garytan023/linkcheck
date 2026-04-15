const { spawn } = require('child_process');
const args = process.argv.slice(2);
const langs = args[0] || 'eng';
const child = spawn('node', ['skills/ocr-local/scripts/ocr.js', '/tmp/ocr_local_test.png', '--lang', langs], { stdio: 'inherit' });
child.on('exit', code => process.exit(code || 0));
