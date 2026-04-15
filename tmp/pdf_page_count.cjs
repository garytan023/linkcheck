const fs = require('fs');
(async () => {
  const pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const data = new Uint8Array(fs.readFileSync(process.argv[2]));
  const pdf = await pdfjsLib.getDocument({ data }).promise;
  console.log(JSON.stringify({ pages: pdf.numPages }));
})();
