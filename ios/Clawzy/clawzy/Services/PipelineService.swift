import Foundation
import Observation

@Observable
final class PipelineService {
    var pipelines: [TaskPipeline] = []
    var isLoading = false
    var errorMessage: String?

    private let api = APIClient.shared

    func fetchPipelines() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response: PipelineListResponse = try await api.request(Constants.API.pipelines)
            pipelines = response.pipelines
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func createPipeline(prompt: String) async -> TaskPipeline? {
        do {
            let pipeline: TaskPipeline = try await api.request(
                Constants.API.pipelines,
                method: "POST",
                body: CreatePipelineRequest(prompt: prompt)
            )
            pipelines.insert(pipeline, at: 0)
            return pipeline
        } catch {
            errorMessage = error.localizedDescription
            return nil
        }
    }

    func runPipeline(_ id: String) async -> TaskPipeline? {
        do {
            let updated: TaskPipeline = try await api.request(
                Constants.API.pipelineRun(id),
                method: "POST"
            )
            _updateLocal(updated)
            return updated
        } catch {
            errorMessage = error.localizedDescription
            return nil
        }
    }

    func cancelPipeline(_ id: String) async {
        do {
            let updated: TaskPipeline = try await api.request(
                Constants.API.pipelineCancel(id),
                method: "POST"
            )
            _updateLocal(updated)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func fetchDetail(_ id: String) async -> TaskPipeline? {
        do {
            return try await api.request(Constants.API.pipeline(id))
        } catch {
            errorMessage = error.localizedDescription
            return nil
        }
    }

    private func _updateLocal(_ updated: TaskPipeline) {
        if let idx = pipelines.firstIndex(where: { $0.id == updated.id }) {
            pipelines[idx] = updated
        }
    }
}
