@echo off
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yuno0154/markdown-converter-hwp.git
git push -u origin main
echo Done.
