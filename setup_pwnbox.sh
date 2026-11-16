#!/usr/bin/env bash
mkdir -p ~/ihack/{web,pwn,rev,crypto,forensics,scripts}
cd ~/ihack/scripts

echo "[*] Downloading Burp Suite Community Edition JAR..."
curl -L "https://portswigger-cdn.net/burp/releases/download?product=community&type=Jar" -o burpsuite_community.jar

echo "[*] Creating launcher alias..."
echo 'alias burp="java -jar ~/ihack/scripts/burpsuite_community.jar &"' >> ~/.bashrc
echo "[+] Workspace ready at ~/ihack. Run 'source ~/.bashrc && burp' to launch Burp."