import SwiftUI

@Observable
final class ScheduleViewModel {
    var tasks: [AgentTask] = []
    var isLoading = false
    var showCreateSheet = false
    var newTitle = ""
    var newPriority = "medium"

    func load() async {
        isLoading = true
        defer { isLoading = false }
        tasks = (try? await APIClient.shared.request(Constants.API.schedule)) ?? []
    }

    func create() async {
        guard !newTitle.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        let body = AgentTaskCreate(title: newTitle, description: nil, dueDate: nil, priority: newPriority, category: nil)
        if let task: AgentTask = try? await APIClient.shared.request(Constants.API.schedule, method: "POST", body: body) {
            tasks.insert(task, at: 0)
        }
        newTitle = ""
        showCreateSheet = false
    }

    func delete(_ task: AgentTask) async {
        try? await APIClient.shared.requestVoid(Constants.API.scheduleItem(task.id), method: "DELETE")
        tasks.removeAll { $0.id == task.id }
    }
}

struct ScheduleView: View {
    @State private var vm = ScheduleViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.tasks.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if vm.tasks.isEmpty {
                    ContentUnavailableView("No Tasks", systemImage: "checklist", description: Text("Tap + to create a task"))
                } else {
                    List {
                        ForEach(vm.tasks) { task in
                            TaskRow(task: task)
                        }
                        .onDelete { idxs in
                            for i in idxs {
                                let task = vm.tasks[i]
                                Task { await vm.delete(task) }
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Schedule")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button { vm.showCreateSheet = true } label: { Image(systemName: "plus") }
                }
            }
            .sheet(isPresented: $vm.showCreateSheet) {
                CreateTaskSheet(vm: vm)
            }
            .task { await vm.load() }
            .refreshable { await vm.load() }
        }
    }
}

private struct TaskRow: View {
    let task: AgentTask

    var priorityColor: Color {
        switch task.priority {
        case "high": return .red
        case "low": return .green
        default: return .orange
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Circle()
                    .fill(priorityColor)
                    .frame(width: 8, height: 8)
                Text(task.title)
                    .font(.headline)
                Spacer()
                Text(task.status.uppercased())
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.secondary.opacity(0.2))
                    .clipShape(Capsule())
            }
            if let desc = task.description {
                Text(desc)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

private struct CreateTaskSheet: View {
    @Bindable var vm: ScheduleViewModel

    var body: some View {
        NavigationStack {
            Form {
                Section("Title") {
                    TextField("Task title", text: $vm.newTitle)
                }
                Section("Priority") {
                    Picker("Priority", selection: $vm.newPriority) {
                        Text("Low").tag("low")
                        Text("Medium").tag("medium")
                        Text("High").tag("high")
                    }
                    .pickerStyle(.segmented)
                }
            }
            .navigationTitle("New Task")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { vm.showCreateSheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") { Task { await vm.create() } }
                        .disabled(vm.newTitle.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }
}
