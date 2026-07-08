import SwiftUI

struct RootView: View {
    @StateObject private var vm = AnalysisViewModel()
    @EnvironmentObject private var auth: Auth
    private let ticker = Timer.publish(every: 0.1, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider().overlay(Brand.border)
            HStack(spacing: 0) {
                leftColumn.frame(minWidth: 520)
                Divider().overlay(Brand.border)
                rightColumn.frame(minWidth: 420)
            }
        }
        .background(Brand.bg)
        .onAppear { vm.start() }
        .onDisappear { vm.stop() }
        .onReceive(vm.camera.$latestImage) { img in
            if vm.frame.eyes.isEmpty { /* aguardando 1ª captura */ }
        }
        .onReceive(ticker) { _ in vm.tickAutoCapture() }
    }

    // MARK: Header com marca (gradiente índigo)
    private var header: some View {
        HStack(spacing: 14) {
            ZStack {
                SwiftUI.Circle().fill(Brand.brandGradient).frame(width: 30, height: 30)
                SwiftUI.Circle().stroke(Brand.bg, lineWidth: 3).frame(width: 14, height: 14)
                SwiftUI.Circle().fill(Brand.bg).frame(width: 8, height: 8)
            }
            VStack(alignment: .leading, spacing: 1) {
                Text("IRIS ANALYZER")
                    .font(.system(size: 15, weight: .bold)).tracking(1.5)
                    .foregroundStyle(Brand.text)
                Text("análise de imagem da íris · bem-estar · nativo macOS")
                    .font(.system(size: 10)).tracking(0.4)
                    .foregroundStyle(Brand.muted)
            }
            Spacer()
            Text(vm.camera.running ? "● CÂMERA ATIVA" : "○ CÂMERA")
                .font(.system(size: 10, weight: .semibold)).tracking(0.5)
                .foregroundStyle(vm.camera.running ? Brand.cyan : Brand.faint)
            Button {
                vm.stop()
                auth.logout()
            } label: {
                Label("Sair", systemImage: "rectangle.portrait.and.arrow.right")
                    .font(.system(size: 11, weight: .medium))
            }
            .buttonStyle(.plain)
            .foregroundStyle(Brand.muted)
            .padding(.leading, 8)
        }
        .padding(.horizontal, 20).padding(.vertical, 14)
        .background(Brand.bgElev)
    }

    // MARK: Coluna esquerda — câmera + controles
    private var leftColumn: some View {
        VStack(spacing: 14) {
            CameraPreview(image: vm.camera.latestImage, eyes: vm.frame.eyes)
                .aspectRatio(4/3, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 14))
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(Brand.border, lineWidth: 1))

            HStack(spacing: 10) {
                Button(action: vm.capture) {
                    Label(vm.analyzing ? "Analisando…" : "Capturar e analisar",
                          systemImage: "camera.aperture")
                }
                .buttonStyle(PrimaryButtonStyle())
                .disabled(vm.analyzing)

                Button(action: vm.generatePDF) {
                    Label("Gerar laudo PDF", systemImage: "doc.richtext")
                }
                .buttonStyle(GhostButtonStyle())
                .disabled(vm.frame.eyes.isEmpty)
            }

            Toggle(isOn: $vm.autoCapture) {
                Text("Captura automática quando a imagem estiver boa")
                    .font(.system(size: 12)).foregroundStyle(Brand.muted)
            }
            .toggleStyle(.switch).tint(Brand.accent)

            VStack(alignment: .leading, spacing: 6) {
                Text("Dados do cliente").sectionLabel()
                TextField("Nome", text: $vm.clientName)
                    .textFieldStyle(.plain).padding(9)
                    .background(Brand.bgElev).clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Brand.border, lineWidth: 1))
                Text("Observações").sectionLabel().padding(.top, 4)
                TextEditor(text: $vm.observations)
                    .font(.system(size: 12)).scrollContentBackground(.hidden)
                    .padding(6).frame(height: 60)
                    .background(Brand.bgElev).clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Brand.border, lineWidth: 1))
            }

            Spacer()
            statusBar
        }
        .padding(18)
    }

    private var statusBar: some View {
        HStack(spacing: 8) {
            if vm.analyzing { ProgressView().scaleEffect(0.6) }
            Text(vm.statusMessage)
                .font(.system(size: 11)).foregroundStyle(Brand.muted)
                .lineLimit(2)
            Spacer()
        }
        .padding(.horizontal, 12).padding(.vertical, 8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .brandCard()
    }

    // MARK: Coluna direita — resultados
    private var rightColumn: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("Resultados").sectionLabel().padding(.top, 4)

                if vm.frame.eyes.isEmpty {
                    emptyState
                } else {
                    if vm.frame.confianca > 0 {
                        confidenceBar
                    }
                    ForEach(vm.frame.eyes) { eye in
                        EyeCardView(analysis: eye)
                    }
                    if !vm.frame.comparacoes.isEmpty {
                        comparisonCard
                    }
                }
                disclaimer
            }
            .padding(18)
        }
        .background(Brand.bg)
    }

    private var emptyState: some View {
        VStack(spacing: 10) {
            Image(systemName: "eye.trianglebadge.exclamationmark")
                .font(.system(size: 34, weight: .thin)).foregroundStyle(Brand.faint)
            Text("Capture para ver o resumo da análise.")
                .font(.system(size: 12)).foregroundStyle(Brand.muted)
        }
        .frame(maxWidth: .infinity).padding(.vertical, 50)
    }

    private var confidenceBar: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Confiança da análise").sectionLabel()
                Spacer()
                Text("\(Int(vm.frame.confianca * 100))%")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(Brand.qualityColor(vm.frame.confianca * 100))
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(Brand.bgElev)
                    Capsule().fill(Brand.brandGradient)
                        .frame(width: geo.size.width * vm.frame.confianca)
                }
            }.frame(height: 6)
        }
        .padding(14).brandCard(highlighted: true)
    }

    private var comparisonCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Comparação entre olhos").sectionLabel()
            ForEach(vm.frame.comparacoes, id: \.self) { c in
                Label(c, systemImage: "arrow.left.arrow.right")
                    .font(.system(size: 12)).foregroundStyle(Brand.text)
            }
        }
        .padding(14).frame(maxWidth: .infinity, alignment: .leading).brandCard()
    }

    private var disclaimer: some View {
        Text("Aviso: a iridologia não é reconhecida pela ciência como método "
             + "de diagnóstico. Este app é educacional/bem-estar e não substitui "
             + "avaliação médica profissional.")
            .font(.system(size: 10)).foregroundStyle(Brand.faint)
            .padding(12).frame(maxWidth: .infinity, alignment: .leading)
            .background(Brand.bgElev).clipShape(RoundedRectangle(cornerRadius: 10))
    }
}
