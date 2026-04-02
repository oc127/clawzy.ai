import Foundation
import Observation

/// Service for agent detail sub-resources (tools, memories, skills, tasks, channels)
@Observable
final class AgentDetailService {
    var tools: [AgentTool] = []
    var memories: [AgentMemory] = []
    var skills: [AgentSkill] = []
    var tasks: [AgentTask] = []
    var channels: [AgentChannel] = []

    var isLoading = false
    var errorMessage: String?

    private let api = APIClient.shared

    // MARK: - Tools

    func fetchTools(agentId: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            tools = try await api.request(Constants.API.agentTools(agentId))
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func toggleTool(agentId: String, toolName: String, enabled: Bool) async {
        do {
            let body = ["name": toolName, "enabled": enabled] as [String : Any]
            let jsonData = try JSONSerialization.data(withJSONObject: body)

            guard let url = URL(string: Constants.baseURL + Constants.API.agentTools(agentId)) else { return }
            var request = URLRequest(url: url)
            request.httpMethod = "PATCH"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            if let token = KeychainHelper.shared.readString(for: Constants.accessTokenKey) {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            request.httpBody = jsonData
            let _ = try await URLSession.shared.data(for: request)

            if let idx = tools.firstIndex(where: { $0.name == toolName }) {
                tools[idx] = AgentTool(name: tools[idx].name, description: tools[idx].description, enabled: enabled)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Memories

    func fetchMemories(agentId: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            memories = try await api.request(Constants.API.agentMemories(agentId))
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func deleteMemory(agentId: String, memoryId: String) async {
        do {
            try await api.requestVoid(
                Constants.API.agentMemory(agentId, memoryId: memoryId),
                method: "DELETE"
            )
            memories.removeAll { $0.id == memoryId }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Skills

    func fetchSkills(agentId: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            skills = try await api.request(Constants.API.agentSkills(agentId))
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Tasks

    func fetchTasks(agentId: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            tasks = try await api.request(Constants.API.agentTasks(agentId))
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func createTask(agentId: String, cron: String, prompt: String, description: String) async {
        do {
            let body = CreateTaskRequest(cronExpression: cron, prompt: prompt, description: description)
            let task: AgentTask = try await api.request(
                Constants.API.agentTasks(agentId),
                method: "POST",
                body: body
            )
            tasks.append(task)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func toggleTask(agentId: String, taskId: String, enabled: Bool) async {
        do {
            let body = UpdateTaskRequest(enabled: enabled, cronExpression: nil, prompt: nil, description: nil)
            let updated: AgentTask = try await api.request(
                Constants.API.agentTask(agentId, taskId: taskId),
                method: "PATCH",
                body: body
            )
            if let idx = tasks.firstIndex(where: { $0.id == taskId }) {
                tasks[idx] = updated
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func deleteTask(agentId: String, taskId: String) async {
        do {
            try await api.requestVoid(
                Constants.API.agentTask(agentId, taskId: taskId),
                method: "DELETE"
            )
            tasks.removeAll { $0.id == taskId }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Channels

    func fetchChannels(agentId: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            channels = try await api.request(Constants.API.agentChannels(agentId))
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func createChannel(agentId: String, type: String, config: [String: String]) async {
        do {
            let body = CreateChannelRequest(type: type, config: config)
            let channel: AgentChannel = try await api.request(
                Constants.API.agentChannels(agentId),
                method: "POST",
                body: body
            )
            channels.append(channel)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func deleteChannel(agentId: String, channelId: String) async {
        do {
            try await api.requestVoid(
                Constants.API.agentChannel(agentId, channelId: channelId),
                method: "DELETE"
            )
            channels.removeAll { $0.id == channelId }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
