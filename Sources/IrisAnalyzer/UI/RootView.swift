import SwiftUI

struct RootView: View {
    @StateObject private var vm = AnalysisViewModel()
    @EnvironmentObject private var auth: Auth
    private let ticker = Timer.publish(every: 0.1, on: .main, in: .common).autoconnect()

    var body: some View {
        NavigationStack {
            HSplitView {
                capturePane
                    .frame(minWidth: 460, idealWidth: 560)
                resultsPane
                    .frame(minWidth: 380, idealWidth: 460)
            }
            .navigationTitle("Iris Analyzer")
            .navigationSubtitle(vm.statusMessage)
            .toolbar { toolbarContent }
        }
        .onAppear { vm.start() }
        .onDisappear { vm.stop() }
        .onReceive(ticker) { _ in vm.tickAutoCapture() }
    }

    // MARK: Toolbar nativa
    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .navigation) {
            HStack(spacing: 7) {
                IrisMark(size: 18)
                if vm.camera.running {
                    Label("câmera", systemImage: "circle.fill")
                        .labelStyle(.iconOnly)
                        .font(.system(size: 7))
                        .foregroundStyle(Brand.accent2)
                }
            }
        }
        ToolbarItemGroup(placement: .primaryAction) {
            Button(action: vm.capture) {
                Label("Capturar", systemImage: "camera.aperture")
            }
            .buttonStyle(.borderedProminent)
            .tint(Brand.accent)
            .disabled(vm.analyzing)

            Button(action: vm.generatePDF) {
                Label("Laudo PDF", systemImage: "doc.richtext")
            }
            .disabled(vm.frame.eyes.isEmpty)

            Button {
                vm.stop(); auth.logout()
            } label: {
                Label("Sair", systemImage: "rectangle.portrait.and.arrow.right")
            }
        }
    }

    // MARK: Painel de captura (esquerda)
    private var capturePane: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                CameraPreview(image: vm.camera.latestImage, eyes: vm.frame.eyes)
                    .aspectRatio(4/3, contentMode: .fit)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .strokeBorder(Brand.border, lineWidth: 1))
                    .shadow(color: .black.opacity(0.15), radius: 10, y: 4)

                if vm.analyzing {
                    HStack(spacing: 8) {
                        ProgressView().controlSize(.small)
                        Text("Analisando…").foregroundStyle(.secondary).font(.callout)
                    }
                }

                Toggle(isOn: $vm.autoCapture) {
                    Label("Captura automática quando a imagem estiver boa",
                          systemImage: "wand.and.stars")
                }
                .toggleStyle(.switch)

                GroupBox {
                    VStack(alignment: .leading, spacing: 12) {
                        LabeledContent("Nome") {
                            TextField("Nome do cliente", text: $vm.clientName)
                                .textFieldStyle(.roundedBorder)
                                .frame(maxWidth: 260)
                        }
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Observações").font(.callout)
                            TextEditor(text: $vm.observations)
                                .font(.body).frame(height: 64)
                                .scrollContentBackground(.hidden)
                                .padding(6)
                                .background(RoundedRectangle(cornerRadius: 6).fill(Brand.bgElev))
                                .overlay(RoundedRectangle(cornerRadius: 6)
                                    .strokeBorder(Brand.border, lineWidth: 1))
                        }
                    }
                    .padding(6)
                } label: {
                    Label("Dados do cliente", systemImage: "person.text.rectangle")
                        .font(.headline)
                }
            }
            .padding(20)
        }
        .background(Brand.bg)
    }

    // MARK: Painel de resultados (direita)
    private var resultsPane: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if vm.frame.eyes.isEmpty {
                    ContentUnavailableView {
                        Label("Sem análise ainda", systemImage: "eye")
                    } description: {
                        Text("Enquadre o olho e clique em Capturar para ver o resumo.")
                    }
                    .padding(.top, 40)
                } else {
                    if vm.frame.confianca > 0 { confidenceCard }
                    ForEach(vm.frame.eyes) { EyeCardView(analysis: $0) }
                    if !vm.frame.comparacoes.isEmpty { comparisonCard }
                }
                disclaimer
            }
            .padding(20)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(VisualEffectBackground(material: .contentBackground).ignoresSafeArea())
    }

    private var confidenceCard: some View {
        GroupBox {
            HStack(spacing: 14) {
                Gauge(value: vm.frame.confianca) {
                    EmptyView()
                } currentValueLabel: {
                    Text("\(Int(vm.frame.confianca * 100))")
                }
                .gaugeStyle(.accessoryCircularCapacity)
                .tint(Brand.qualityColor(vm.frame.confianca * 100))
                .scaleEffect(0.9)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Confiança da análise").font(.headline)
                    Text("Média ponderada da qualidade dos olhos capturados.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
            }
            .padding(6)
        }
    }

    private var comparisonCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(vm.frame.comparacoes, id: \.self) { c in
                    Label(c, systemImage: "arrow.left.and.right")
                        .font(.callout)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(6)
        } label: {
            Label("Comparação entre olhos", systemImage: "eyes")
                .font(.headline)
        }
    }

    private var disclaimer: some View {
        Text("A iridologia não é reconhecida cientificamente como método de "
             + "diagnóstico. Ferramenta educacional/bem-estar — não substitui "
             + "avaliação médica profissional.")
            .font(.caption2).foregroundStyle(.secondary)
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 8).fill(Brand.bgElev))
    }
}

/// Marca da íris em miniatura (usada na toolbar / login).
struct IrisMark: View {
    var size: CGFloat = 20
    var body: some View {
        ZStack {
            SwiftUI.Circle().fill(Brand.brandGradient)
            SwiftUI.Circle().fill(Color(nsColor: .windowBackgroundColor))
                .frame(width: size * 0.42, height: size * 0.42)
            SwiftUI.Circle().fill(.white.opacity(0.9))
                .frame(width: size * 0.1, height: size * 0.1)
                .offset(x: -size * 0.1, y: -size * 0.1)
        }
        .frame(width: size, height: size)
    }
}
