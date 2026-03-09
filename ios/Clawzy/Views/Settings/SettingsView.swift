import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authVM: AuthViewModel

    @State private var name: String = ""
    @State private var isSaving = false
    @State private var showChangePassword = false
    @State private var successMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Profile") {
                    if let user = authVM.currentUser {
                        LabeledContent("Email", value: user.email)

                        TextField("Name", text: $name)
                            .onAppear { name = user.name }

                        if name != user.name {
                            Button("Save") {
                                isSaving = true
                                Task {
                                    do {
                                        let _: User = try await APIClient.shared.request(
                                            path: "/users/me",
                                            method: "PATCH",
                                            body: ["name": name]
                                        )
                                        await authVM.checkAuth()
                                        successMessage = "Name updated."
                                    } catch {}
                                    isSaving = false
                                }
                            }
                            .disabled(isSaving)
                        }
                    }
                }

                Section {
                    Button("Change Password") {
                        showChangePassword = true
                    }
                }

                Section {
                    Button("Log Out", role: .destructive) {
                        authVM.logout()
                    }
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showChangePassword) {
                ChangePasswordView()
            }
            .alert("Success", isPresented: .constant(successMessage != nil)) {
                Button("OK") { successMessage = nil }
            } message: {
                Text(successMessage ?? "")
            }
        }
    }
}

struct ChangePasswordView: View {
    @Environment(\.dismiss) var dismiss

    @State private var currentPassword = ""
    @State private var newPassword = ""
    @State private var confirmPassword = ""
    @State private var isSubmitting = false
    @State private var errorMessage: String?
    @State private var success = false

    var body: some View {
        NavigationStack {
            Form {
                SecureField("Current Password", text: $currentPassword)
                SecureField("New Password", text: $newPassword)
                SecureField("Confirm New Password", text: $confirmPassword)

                if let error = errorMessage {
                    Text(error).foregroundStyle(.red).font(.caption)
                }

                Button("Update Password") {
                    guard newPassword == confirmPassword else {
                        errorMessage = "Passwords do not match."
                        return
                    }
                    isSubmitting = true
                    Task {
                        do {
                            let _: MessageResponse = try await APIClient.shared.request(
                                path: "/users/me/change-password",
                                method: "POST",
                                body: ["current_password": currentPassword, "new_password": newPassword]
                            )
                            success = true
                        } catch {
                            errorMessage = error.localizedDescription
                        }
                        isSubmitting = false
                    }
                }
                .disabled(currentPassword.isEmpty || newPassword.isEmpty || isSubmitting)
            }
            .navigationTitle("Change Password")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .alert("Password Updated", isPresented: $success) {
                Button("OK") { dismiss() }
            }
        }
    }
}
