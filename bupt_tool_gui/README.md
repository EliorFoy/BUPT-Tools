# BUPT 抢课工具 GUI (Rust + Slint)

这是一个使用 Rust 和 Slint 框架开发的跨平台 GUI 版本的北邮抢课工具。

## 功能特性

- 🖥️ **现代化 GUI 界面** - 使用 Slint 构建的响应式用户界面
- 🔐 **安全登录** - 支持学号密码登录
- ⚡ **自动抢课** - 可配置检查间隔，自动尝试抢课
- 📝 **实时日志** - 显示抢课过程和结果
- 🌍 **跨平台** - 支持 Windows、macOS 和 Linux

## 系统要求

- Rust 1.70+ 
- CMake 3.1+
- Qt 5.15+ 或 Qt 6 (可选，用于原生外观)

## 安装依赖

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake qtbase5-dev libqt5widgets5
```

### macOS

```bash
brew install cmake qt
```

### Windows

确保安装了:
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- [Qt](https://www.qt.io/download-qt-installer)

## 编译项目

```bash
cd bupt_tool_gui
cargo build --release
```

编译后的可执行文件位于 `target/release/bupt_tool_gui`

## 运行

```bash
cargo run --release
```

或者直接使用编译好的二进制文件:

```bash
./target/release/bupt_tool_gui
```

## 使用说明

1. **首次使用必读**: 请先阅读 [API 配置指南](./API_CONFIG_GUIDE.md)，根据实际教务系统接口调整配置
2. **登录**: 输入学号和密码，点击"登录"按钮
3. **配置课程**: 在"课程 ID"输入框中输入要抢的课程 ID，多个课程用逗号分隔
4. **设置检查间隔**: 调整检查间隔时间（毫秒），建议 100ms 以上
5. **开始抢课**: 点击"开始抢课"按钮启动自动抢课
6. **查看日志**: 底部日志区域会实时显示抢课结果

## API 配置 ⚠️

**重要**: 由于北邮教务系统的 API 可能会变化，使用前需要根据实际情况调整配置。

请查看详细的 [API 配置指南](./API_CONFIG_GUIDE.md) 了解如何:
- 获取登录 API 端点
- 获取课程列表 API
- 获取抢课 API
- 调整 HTML 解析选择器
- 配置 JSON 解析结构体

## 项目结构

```
bupt_tool_gui/
├── Cargo.toml          # Rust 项目配置
├── build.rs            # Slint UI 编译脚本
├── src/
│   ├── main.rs         # GUI 主入口
│   └── lib.rs          # 核心业务逻辑
└── ui/
    └── app.slint       # Slint UI 定义
```

## 核心模块

### lib.rs
- `config`: **可配置的 API 端点** (需要根据实际情况调整)
- `UserConfig`: 用户配置结构体
- `CourseInfo`: 课程信息
- `AuthManager`: 认证管理器 (支持 CSRF token 自动提取)
- `CourseGrabber`: 课程抓取器 (支持 HTML 和 JSON 解析)
- `BUPTTool`: 主入口类

### app.slint
定义了完整的 GUI 界面，包括:
- 登录区域
- 抢课配置区域
- 状态栏
- 日志显示区域

### 主要功能特性
- ✅ **CSRF Token 自动处理**: 自动从页面提取 CSRF token
- ✅ **HTML 解析**: 使用 scraper 库解析课程列表
- ✅ **JSON 解析**: 支持多种 JSON 格式的课程数据
- ✅ **错误信息提取**: 自动从响应中提取错误信息
- ✅ **灵活配置**: 所有 API 端点都可配置

## 开发说明

### 添加新功能

1. 在 `lib.rs` 中添加业务逻辑
2. 在 `app.slint` 中添加对应的 UI 元素
3. 在 `main.rs` 中连接 UI 事件和业务逻辑

### 调试

启用详细日志:

```bash
RUST_LOG=debug cargo run
```

## 注意事项

⚠️ **重要提示**: 
- 请合理使用抢课功能，避免对教务系统造成过大压力
- 建议检查间隔不要设置得过小（不低于 50ms）
- 本工具仅供学习研究使用

## 许可证

GPL-3.0 License

## 贡献

欢迎提交 Issue 和 Pull Request!

## 致谢

- [Slint](https://slint.dev/) - 优秀的跨平台 GUI 框架
- [Rust](https://www.rust-lang.org/) - 强大的系统编程语言
