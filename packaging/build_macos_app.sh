#!/bin/bash
# Cria "Iris Analyzer.app" (macOS) com icone, na Area de Trabalho.
#
#   bash packaging/build_macos_app.sh
#
# Estrategia (testada): instala o codigo numa pasta NAO protegida
# (~/Library/Application Support/IrisAnalyzer) e o app abre via Terminal —
# evita o bloqueio de TCC da pasta Downloads/Desktop e a falha de carregamento
# de bibliotecas do Python do sistema quando lancado direto pelo launchd.
set -e
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
HERE="$PROJ/packaging"
DEST="${1:-$HOME/Desktop}"
APP="$DEST/Iris Analyzer.app"
SUPP="$HOME/Library/Application Support/IrisAnalyzer"

# 1) instala o codigo + modelo em pasta nao protegida
rm -rf "$SUPP"; mkdir -p "$SUPP"
cp -R "$PROJ/iris_analyzer" "$PROJ/run.py" "$PROJ/download_model.py" "$SUPP/"
[ -f "$PROJ/face_landmarker.task" ] && cp "$PROJ/face_landmarker.task" "$SUPP/"

# 2) icone -> .icns
[ -f "$HERE/icon.png" ] || python3 "$HERE/make_icon.py"
TMP="$(mktemp -d)/IrisAnalyzer.iconset"; mkdir -p "$TMP"
for n in 16 32 128 256 512; do
  sips -z $n $n             "$HERE/icon.png" --out "$TMP/icon_${n}x${n}.png"     >/dev/null
  sips -z $((n*2)) $((n*2)) "$HERE/icon.png" --out "$TMP/icon_${n}x${n}@2x.png" >/dev/null
done
iconutil -c icns "$TMP" -o "$TMP/AppIcon.icns"

# 3) bundle .app
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$TMP/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"

# launcher: roda direto (sem Terminal). Em Apple Silicon, forca arm64 para
# carregar as libs nativas (numpy/cv2) — o launchd as vezes inicia em x86_64.
cat > "$APP/Contents/MacOS/IrisAnalyzer" <<'EOF'
#!/bin/bash
cd "$HOME/Library/Application Support/IrisAnalyzer" || exit 1
# Detecta HARDWARE Apple Silicon (sysctl funciona mesmo sob Rosetta;
# uname -m mentiria 'x86_64' quando o launchd inicia o app em x86_64).
ARCHCMD=""
[ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ] && ARCHCMD="arch -arm64"
LOG="$HOME/Library/Logs/IrisAnalyzer.log"
[ -f face_landmarker.task ] || $ARCHCMD /usr/bin/python3 download_model.py >"$LOG" 2>&1
exec $ARCHCMD /usr/bin/python3 run.py >>"$LOG" 2>&1
EOF
chmod +x "$APP/Contents/MacOS/IrisAnalyzer"

cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Iris Analyzer</string>
  <key>CFBundleDisplayName</key><string>Iris Analyzer</string>
  <key>CFBundleIdentifier</key><string>br.com.dheiver.irisanalyzer</string>
  <key>CFBundleVersion</key><string>1.0.0</string>
  <key>CFBundleShortVersionString</key><string>1.0.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>IrisAnalyzer</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>NSCameraUsageDescription</key><string>O Iris Analyzer usa a câmera para capturar a imagem da íris.</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
</dict></plist>
EOF
touch "$APP"
# Assinatura ad-hoc: da identidade estavel ao bundle para a permissao de
# camera (TCC) persistir. Sem isso, app nao-assinado nao recebe/mantem o grant.
codesign --force --deep --sign - "$APP" 2>/dev/null && echo "assinado (ad-hoc)"
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP" 2>/dev/null || true
echo "App criado em: $APP"
echo "Codigo instalado em: $SUPP"
echo "Dica: se a camera nao conectar, rode:"
echo "  tccutil reset Camera br.com.dheiver.irisanalyzer"
echo "  e reabra o app, autorizando a camera quando pedir."
