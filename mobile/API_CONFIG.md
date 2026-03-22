# 开发环境 API 地址

模拟器 / 真机要能访问跑后端的电脑，请在 **`app.json`** 里改：

```json
"extra": {
  "apiBaseUrl": "http://你的后端局域网IP/api/v1"
}
```

- 后端在 Linux 服务器上：在服务器上执行 `hostname -I` 或 `ip a` 看 IP。
- Mac 与服务器要同一局域网（同一 Wi‑Fi）。
- 改完后 Metro 里按 `r` 重载；若仍不行，重启 `npx expo run:ios`。

生产环境会自动用 `https://www.nipponclaw.com/api/v1`。
