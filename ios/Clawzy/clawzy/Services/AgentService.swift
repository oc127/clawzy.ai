import Foundation
import Observation

/// Agent 管理服务
@Observable
final class AgentService {
    var agents: [Agent] = []
    var isLoading = false
    var errorMessage: String?

    private let api = APIClient.shared

    /// 获取 Agent 列表
    func fetchAgents() async {
        isLoading = true
        defer { isLoading = false }

        do {
            agents = try await api.request(Constants.API.agents)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 创建新 Agent（可选预设 system prompt）
    func createAgent(name: String, modelName: String, systemPrompt: String? = nil) async -> Agent? {
        do {
            let body = CreateAgentRequest(name: name, modelName: modelName, systemPrompt: systemPrompt)
            let agent: Agent = try await api.request(
                Constants.API.agents,
                method: "POST",
                body: body
            )
            agents.append(agent)
            return agent
        } catch {
            errorMessage = error.localizedDescription
            return nil
        }
    }

    /// 启动 Agent
    func startAgent(_ id: String) async {
        do {
            let updated: Agent = try await api.request(
                Constants.API.agentStart(id),
                method: "POST"
            )
            if let index = agents.firstIndex(where: { $0.id == id }) {
                agents[index] = updated
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 停止 Agent
    func stopAgent(_ id: String) async {
        do {
            let updated: Agent = try await api.request(
                Constants.API.agentStop(id),
                method: "POST"
            )
            if let index = agents.firstIndex(where: { $0.id == id }) {
                agents[index] = updated
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 删除 Agent
    func deleteAgent(_ id: String) async {
        do {
            try await api.requestVoid(
                Constants.API.agent(id),
                method: "DELETE"
            )
            agents.removeAll { $0.id == id }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
