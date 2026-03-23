import Foundation
import Security

/// Keychain 工具类 - 安全存储 JWT token
final class KeychainHelper {
    static let shared = KeychainHelper()
    private init() {}

    func save(_ data: Data, for key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        // 先删除旧值
        SecItemDelete(query as CFDictionary)
        // 再写入新值
        SecItemAdd(query as CFDictionary, nil)
    }

    func read(for key: String) -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var result: AnyObject?
        SecItemCopyMatching(query as CFDictionary, &result)
        return result as? Data
    }

    func delete(for key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)
    }

    // 便捷方法
    func saveString(_ value: String, for key: String) {
        if let data = value.data(using: .utf8) {
            save(data, for: key)
        }
    }

    func readString(for key: String) -> String? {
        guard let data = read(for: key) else { return nil }
        return String(data: data, encoding: .utf8)
    }
}
