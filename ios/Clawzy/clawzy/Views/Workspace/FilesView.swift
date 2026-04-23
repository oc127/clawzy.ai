import SwiftUI

@Observable
final class FilesViewModel {
    var files: [AgentFile] = []
    var isLoading = false

    func load() async {
        isLoading = true
        defer { isLoading = false }
        files = (try? await APIClient.shared.request(Constants.API.files)) ?? []
    }

    func delete(_ file: AgentFile) async {
        try? await APIClient.shared.requestVoid(Constants.API.file(file.id), method: "DELETE")
        files.removeAll { $0.id == file.id }
    }
}

struct FilesView: View {
    @State private var vm = FilesViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.files.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if vm.files.isEmpty {
                    ContentUnavailableView("No Files", systemImage: "folder", description: Text("Files created by agents appear here"))
                } else {
                    List {
                        ForEach(vm.files) { file in
                            FileRow(file: file)
                        }
                        .onDelete { idxs in
                            for i in idxs {
                                let file = vm.files[i]
                                Task { await vm.delete(file) }
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Files")
            .task { await vm.load() }
            .refreshable { await vm.load() }
        }
    }
}

private struct FileRow: View {
    let file: AgentFile

    var icon: String {
        guard let type = file.fileType?.lowercased() else { return "doc" }
        if type.contains("image") { return "photo" }
        if type.contains("pdf") { return "doc.richtext" }
        if type.contains("text") { return "doc.text" }
        return "doc"
    }

    var sizeString: String {
        guard let size = file.fileSize else { return "" }
        if size < 1024 { return "\(size) B" }
        if size < 1024 * 1024 { return String(format: "%.1f KB", Double(size) / 1024) }
        return String(format: "%.1f MB", Double(size) / 1024 / 1024)
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(.blue)
                .frame(width: 32)
            VStack(alignment: .leading, spacing: 2) {
                Text(file.filename)
                    .font(.headline)
                HStack {
                    if !sizeString.isEmpty {
                        Text(sizeString)
                    }
                    if let desc = file.description {
                        Text(desc)
                    }
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }
            Spacer()
            Text(file.createdBy)
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .padding(.vertical, 4)
    }
}
