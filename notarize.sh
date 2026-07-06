#!/bin/bash
# Assina com Developer ID + notariza + staple o Iris Analyzer.app, e gera um .dmg.
# Pré-requisitos (conta Apple Developer, ~US$99/ano):
#   - Certificado "Developer ID Application" instalado no Keychain
#   - Perfil de credencial guardado:
#       xcrun notarytool store-credentials "IRIS_NOTARY" \
#         --apple-id "SEU_APPLE_ID" --team-id "SEU_TEAMID" --password "APP_SPECIFIC_PASSWORD"
#
# Uso:
#   bash notarize.sh "Developer ID Application: SEU NOME (TEAMID)"
set -e
cd "$(dirname "$0")"

IDENTITY="${1:?Passe a identidade Developer ID como 1º argumento}"
PROFILE="${2:-IRIS_NOTARY}"
APP="$HOME/Desktop/Iris Analyzer.app"
DMG="$HOME/Desktop/IrisAnalyzer.dmg"
ZIP="$(mktemp -d)/IrisAnalyzer.zip"

[ -d "$APP" ] || { echo "✗ App não encontrado. Rode antes: bash build_app.sh"; exit 1; }

echo "▶ 1/4 Assinando com Developer ID…"
codesign --force --deep --options runtime --timestamp \
  --entitlements IrisAnalyzer.entitlements \
  --sign "$IDENTITY" "$APP"
codesign --verify --strict --verbose=2 "$APP"

echo "▶ 2/4 Enviando para notarização (pode levar minutos)…"
ditto -c -k --keepParent "$APP" "$ZIP"
xcrun notarytool submit "$ZIP" --keychain-profile "$PROFILE" --wait

echo "▶ 3/4 Grampeando (staple) o ticket…"
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"

echo "▶ 4/4 Gerando .dmg…"
rm -f "$DMG"
hdiutil create -volname "Iris Analyzer" -srcfolder "$APP" -ov -format UDZO "$DMG"

echo "✓ Pronto: app notarizado + $DMG"
echo "  Verificação Gatekeeper: spctl -a -vvv \"$APP\""
