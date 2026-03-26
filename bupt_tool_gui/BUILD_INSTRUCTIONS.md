# BUPT 抢课工具 - Rust + Slint GUI 版本

## 项目概述

本项目是将原有 Python 版本的 BUPT 抢课工具使用 **Rust** 语言重写，并使用 **Slint** 跨平台 GUI 框架开发的现代化桌面应用。

## 已完成的工作

### ✅ 项目结构

```
bupt_tool_gui/
├── Cargo.toml              # Rust 项目配置文件
├── build.rs                # Slint UI 编译脚本
├── README.md               # 项目说明文档
├── .gitignore             # Git 忽略文件配置
├── src/
│   ├── main.rs            # GUI 主入口和事件处理
│   └── lib.rs             # 核心业务逻辑模块
└── ui/
    └── app.slint          # Slint UI 界面定义
```

### ✅ 核心功能模块 (src/lib.rs)

1. **UserConfig** - 用户配置结构体
   - 学号、密码
   - 课程 ID 列表
   - 检查间隔时间
   - 自动提交选项

2. **CourseInfo** - 课程信息
   - 课程 ID、名称、教师
   - 时间、地点
   - 容量、已选人数
   - 课程状态（可选/已满/关闭/未知）

3. **AuthManager** - 认证管理器
   - HTTP 客户端管理
   - Cookie 会话管理
   - 登录验证
   - 会话状态检查

4. **CourseGrabber** - 课程抓取器
   - 课程列表获取
   - HTML 解析（需完善）
   - 抢课请求发送
   - 结果处理

5. **BUPTTool** - 主入口类
   - 统一 API 接口
   - 登录管理
   - 抢课循环控制
   - 配置管理

### ✅ GUI 界面 (ui/app.slint)

界面包含以下区域：

1. **登录区域**
   - 学号输入框
   - 密码输入框（隐藏模式）
   - 登录/退出登录按钮

2. **抢课配置区域**
   - 课程 ID 输入（支持多个，逗号分隔）
   - 检查间隔设置（毫秒）
   - 开始/停止抢课按钮

3. **状态栏**
   - 实时状态显示
   - 状态指示灯（颜色区分）

4. **日志区域**
   - 实时日志列表
   - 成功/失败颜色区分
   - 最多保留 100 条日志

### ✅ 主程序 (src/main.rs)

- Slint 窗口初始化
- 事件回调绑定
- 异步任务处理
- 线程间通信（mpsc 通道）
- 日志实时更新

## 如何在您的环境中构建

### 前置要求

1. **Rust 工具链** (1.70+)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   rustup install stable
   ```

2. **系统依赖**

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential cmake qtbase5-dev \
     libqt5widgets5 libqt5gui5 libqt5core5a
   ```

   **macOS:**
   ```bash
   brew install cmake qt
   ```

   **Windows:**
   - 安装 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - 安装 [Qt](https://www.qt.io/download-qt-installer)

### 构建步骤

```bash
cd bupt_tool_gui

# 开发模式构建
cargo build

# 发布模式构建（优化）
cargo build --release

# 直接运行
cargo run --release
```

构建完成后，可执行文件位于：
- Linux/macOS: `target/release/bupt_tool_gui`
- Windows: `target\release\bupt_tool_gui.exe`

## 使用说明

1. **启动应用**
   ```bash
   ./target/release/bupt_tool_gui
   ```

2. **登录**
   - 输入学号和密码
   - 点击"登录"按钮
   - 状态栏显示"登录成功"表示成功

3. **配置抢课**
   - 在"课程 ID"输入框中输入课程 ID
   - 多个课程用逗号分隔，如：`12345,67890`
   - 设置检查间隔（建议 100ms 以上）

4. **开始抢课**
   - 点击"开始抢课"按钮
   - 观察日志区域的实时输出
   - 成功时显示绿色 ✓，失败时显示红色 ✗

5. **停止抢课**
   - 点击"停止抢课"按钮
   - 或关闭应用

## 需要完善的部分

### ⚠️ 重要提示

以下部分需要根据北邮教务系统的实际 API 进行调整：

1. **登录 URL 和参数** (`src/lib.rs` 第 85-105 行)
   ```rust
   let login_url = "https://jwxt.bupt.edu.cn/jwlogin";
   // 需要根据实际登录接口调整
   ```

2. **课程列表 URL** (`src/lib.rs` 第 136 行)
   ```rust
   let courses_url = "https://jwxt.bupt.edu.cn/courses";
   // 需要根据实际接口调整
   ```

3. **HTML 解析逻辑** (`src/lib.rs` 第 153-162 行)
   ```rust
   fn parse_course_list(&self, html: &str) -> Result<Vec<CourseInfo>> {
       // 需要添加真实的 HTML 解析逻辑
       // 建议使用 scraper 或 html5ever 库
   }
   ```

4. **抢课 URL** (`src/lib.rs` 第 168 行)
   ```rust
   let grab_url = format!("https://jwxt.bupt.edu.cn/grab/{}", course_id);
   // 需要根据实际抢课接口调整
   ```

### 建议添加的依赖

在 `Cargo.toml` 中添加：

```toml
[dependencies]
scraper = "0.18"  # HTML 解析
regex = "1.10"    # 正则表达式
tokio = { version = "1", features = ["full"] }
```

## 跨平台编译

### Windows (交叉编译)

```bash
rustup target add x86_64-pc-windows-msvc
cargo build --release --target x86_64-pc-windows-msvc
```

### macOS

```bash
rustup target add x86_64-apple-darwin
rustup target add aarch64-apple-darwin
cargo build --release --target x86_64-apple-darwin
cargo build --release --target aarch64-apple-darwin
```

### Linux

```bash
# x86_64
cargo build --release

# ARM64
rustup target add aarch64-unknown-linux-gnu
cargo build --release --target aarch64-unknown-linux-gnu
```

## 性能优化建议

1. **HTTP 连接池** - 复用 TCP 连接
2. **异步并发** - 同时监控多个课程
3. **智能退避** - 失败后动态调整请求间隔
4. **本地缓存** - 减少重复请求

## 安全注意事项

1. **密码存储** - 建议使用系统密钥环（keyring）
2. **HTTPS** - 确保所有请求使用加密连接
3. **请求频率** - 避免过于频繁的请求导致被封禁
4. **日志脱敏** - 不要记录敏感信息

## 故障排除

### 常见问题

1. **编译错误：找不到 slint 模块**
   ```bash
   cargo clean
   cargo update
   cargo build
   ```

2. **运行时错误：无法加载 Qt**
   ```bash
   # Ubuntu
   sudo apt-get install qtbase5-dev
   
   # macOS
   brew install qt
   ```

3. **登录失败**
   - 检查网络连接
   - 确认学号密码正确
   - 查看北邮教务系统是否维护

## 开发计划

- [ ] 完善 HTML 解析逻辑
- [ ] 添加课程表可视化
- [ ] 支持多账号管理
- [ ] 添加通知功能（系统通知/邮件/微信）
- [ ] 配置文件持久化
- [ ] 自动更新检查
- [ ] 深色模式支持

## 许可证

GPL-3.0 License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请在 GitHub 上提 Issue。

---

**注意**: 本工具仅供学习研究使用，请合理使用，避免对教务系统造成过大压力。
