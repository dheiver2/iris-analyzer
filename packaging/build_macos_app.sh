#!/bin/bash
# Cria "Iris Analyzer.app" (macOS) com icone, na Area de Trabalho.
#
#   bash packaging/build_macos_app.sh
#
# Requer: macOS (iconutil), Python com Pillow. O app chama o codigo do projeto
# em ~/Downloads/iris-analyzer (ajuste PROJ se mover a pasta).
set -e
PROJ="$HOME/Downloads/iris-analyzer"
DEST="${1:-$HOME/Desktop}"
APP="$DEST/Iris Analyzer.app"
HERE="$(cd "$(dirname "$0")" && pwd)"

# 1) icone (gera se faltar) e .icns
[ -f "$HERE/icon.png" ] || python3 "$HERE/make_icon.py"
TMP="$(mktemp -d)/IrisAnalyzer.iconset"; mkdir -p "$TMP"
for n in 16 32 128 256 512; do
  sips -z $n $n        "$HERE/icon.png" --out "$TMP/icon_${n}x${n}.png"     >/dev/null
  sips -z $((n*2)) $((n*2)) "$HERE/icon.png" --out "$TMP/icon_${n}x${n}@2x.png" >/dev/null
done
iconutil -c icns "$TMP" -o "$TMP/AppIcon.icns"

# 2) estrutura do bundle
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$TMP/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"

cat > "$APP/Contents/MacOS/IrisAnalyzer" <<EOF
#!/bin/bash
cd "$PROJ" 2>/dev/null || exit 1
[ -f face_landmarker.task ] || /usr/bin/python3 download_model.py >/tmp/iris_launch.log 2>&1
exec /usr/bin/python3 run.py >>/tmp/iris_launch.log 2>&1
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
  <key>NSCameraUsageDescription</key><string>O Iris Analyzer usa a camera para capturar a imagem da iris.</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
</dict></plist>
EOF

# 3) registra para o icone aparecer
touch "$APP"
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP" 2>/dev/null || true
echo "App criado em: $APP"
