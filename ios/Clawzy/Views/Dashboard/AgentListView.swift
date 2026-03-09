import SwiftUI

@MainActor
final class AgentListViewModel: ObservableObject {
    @Published var agents: [Agent] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var showCreate = false

    func loadAgents() async {
        isLoading = true
        defer { isLoading = false }
        do {
            agents = try await APIClient.shared.request(path: "/agents")
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func createAgent(name: String, model: String) async {
        do {
            let _: Agent = try await APIClient.shared.request(
                path: "/agents",
                method: "POST",
                body: ["name": name, "model_name": model]
            )
            await loadAgents()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func deleteAgent(_ agent: Agent) async {
        do {
            try await APIClient.shared.requestVoid(path: "/agents/\(agent.id)", method: "DELETE")
            agents.removeAll { $0.id == agent.id }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func startAgent(_ agent: Agent) async {
        do {
            let _: Agent = try await APIClient.shared.request(
                path: "/agents/\(agent.id)/start", method: "POST"
            )
            await loadAgents()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func stopAgent(_ agent: Agent) async {
        do {
            let _: Agent = try await APIClient.shared.request(
                path: "/agents/\(agent.id)/stop", method: "POST"
            )
            await loadAgents()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct AgentListView: View {
    @StateObject private var vm = AgentListViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.agents.isEmpty {
                    ProgressView()
                } else if vm.agents.isEmpty {
                    ContentUnavailableView(
                        "No Agents",
                        systemImage: "cpu",
                        description: Text("Create your first AI agent to get started.")
                    )
                } else {
                    List {
                        ForEach(vm.agents) { agent in
                            NavigationLink(destination: ChatView(agent: agent)) {
                                AgentRow(agent: agent, vm: vm)
                            }
                        }
                        .onDelete { indexSet in
                            guard let index = indexSet.first else { return }
                            let agent = vm.agents[index]
                            Task { await vm.deleteAgent(agent) }
                        }
                    }
                    .refreshable {
                        await vm.loadAgents()
                    }
                }
            }
            .navigationTitle("Agents")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        vm.showCreate = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $vm.showCreate) {
                CreateAgentView(vm: vm)
            }
            .task {
                await vm.loadAgents()
            }
            .alert("Error", isPresented: .constant(vm.errorMessage != nil)) {
                Button("OK") { vm.errorMessage = nil }
            } message: {
                Text(vm.errorMessage ?? "")
            }
        }
    }
}

// MARK: - Agent Row

struct AgentRow: View {
    let agent: Agent
    let vm: AgentListViewModel

    var statusColor: Color {
        switch agent.status {
        case .running: .green
        case .creating: .orange
        case .stopped: .gray
        case .error: .red
        }
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(agent.name)
                    .font(.headline)
                Text(agent.model_name)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            // Status badge
            HStack(spacing: 4) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                Text(agent.status.rawValue)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .swipeActions(edge: .leading) {
            if agent.status == .stopped {
                Button("Start") {
                    Task { await vm.startAgent(agent) }
                }
                .tint(.green)
            } else if agent.status == .running {
                Button("Stop") {
                    Task { await vm.stopAgent(agent) }
                }
                .tint(.orange)
            }
        }
    }
}

// MARK: - Create Agent Sheet

struct CreateAgentView: View {
    @ObservedObject var vm: AgentListViewModel
    @Environment(\.dismiss) var dismiss

    @State private var name = ""
    @State private var selectedModel = "deepseek-chat"
    @State private var models: [ModelInfo] = []
    @State private var isSubmitting = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Agent Name") {
                    TextField("My Agent", text: $name)
                }

                Section("Model") {
                    Picker("Model", selection: $selectedModel) {
                        ForEach(models) { model in
                            Text("\(model.name) (\(model.provider))")
                                .tag(model.id)
                        }
                    }
                    .pickerStyle(.menu)
                }
            }
            .navigationTitle("New Agent")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        isSubmitting = true
                        Task {
                            await vm.createAgent(name: name, model: selectedModel)
                            isSubmitting = false
                            dismiss()
                        }
                    }
                    .disabled(name.isEmpty || isSubmitting)
                }
            }
            .task {
                do {
                    models = try await APIClient.shared.request(path: "/models")
                    if let first = models.first {
                        selectedModel = first.id
                    }
                } catch {
                    // Fallback — keep default
                }
            }
        }
    }
}
