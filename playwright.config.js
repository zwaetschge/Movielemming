const { defineConfig } = require('@playwright/test');
const fs = require('fs');
const localChromium = '/usr/bin/chromium';
module.exports = defineConfig({
  testDir:'./tests', timeout:60000,
  use:{baseURL:'http://127.0.0.1:4173',viewport:{width:1440,height:900}, ...(fs.existsSync(localChromium)?{launchOptions:{executablePath:localChromium,args:['--no-sandbox']}}:{})},
  webServer:{command:'python3 -m http.server 4173 -d public',port:4173,reuseExistingServer:true}, reporter:'line'
});
