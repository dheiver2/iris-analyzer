#!/bin/bash
# Compila o Iris Analyzer (SwiftPM) e monta "Iris Analyzer.app" com Info.plist
# de câmera + assinatura ad-hoc — funciona apenas com Command Line Tools
# (não requer Xcode completo).
#
#   bash build_app.sh              # release na Área de Trabalho
#   bash build_app.sh --debug      # build debug
set -e
cd "$(dirname "$0")"

CONFIG="release"
[ "$1" = "--debug" ] && CONFIG="debug"

echo "▶ Compilando ($CONFIG)…"
swift build -c "$CONFIG"

BIN=".build/$CONFIG/IrisAnalyzer"
[ -f "$BIN" ] || { echo "✗ Binário não encontrado em $BIN"; exit 1; }

APP="$HOME/Desktop/Iris Analyzer.app"
echo "▶ Montando bundle: $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN" "$APP/Contents/MacOS/IrisAnalyzer"
cp Info.plist "$APP/Contents/Info.plist"

# Ícone opcional (se existir icon.png ao lado)
if [ -f "icon.png" ]; then
  TMP="$(mktemp -d)/AppIcon.iconset"; mkdir -p "$TMP"
  for n in 16 32 128 256 512; do
    sips -z $n $n icon.png --out "$TMP/icon_${n}x${n}.png" >/dev/null
    sips -z $((n*2)) $((n*2)) icon.png --out "$TMP/icon_${n}x${n}@2x.png" >/dev/null
  done
  iconutil -c icns "$TMP" -o "$APP/Contents/Resources/AppIcon.icns" 2>/dev/null || true
fi

# Assinatura ad-hoc com entitlements (câmera). Para distribuição/licitação,
# troque "-" por sua identidade Developer ID e notarize (ver README).
if codesign --force --deep --options runtime \
     --entitlements IrisAnalyzer.entitlements \
     --sign - "$APP" 2>/dev/null; then
  echo "✓ Assinado (ad-hoc, hardened runtime + entitlement de câmera)"
else
  codesign --force --deep --sign - "$APP"
  echo "✓ Assinado (ad-hoc, sem hardened runtime)"
fi

echo "✓ App criado: $APP"
echo "  Primeira execução: clique direito → Abrir (app não notarizado)."
echo "  Se a câmera não pedir permissão: tccutil reset Camera br.com.dheiver.irisanalyzer.native"
