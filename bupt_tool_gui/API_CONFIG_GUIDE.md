# BUPT 抢课工具 - API 配置指南

## ⚠️ 重要提示

本工具中的 URL 和 HTML 解析逻辑需要根据北邮教务系统的**实际接口**进行调整。以下指南将帮助您完成配置。

## 📋 配置步骤

### 1. 使用浏览器开发者工具抓包

1. 打开 Chrome/Edge/Firefox 浏览器
2. 按 `F12` 打开开发者工具
3. 切换到 **Network (网络)** 标签
4. 勾选 **Preserve log (保留日志)**
5. 访问北邮教务系统并执行以下操作:
   - 登录
   - 查看课程列表
   - 尝试选课

### 2. 获取登录 API 端点

在 Network 面板中查找登录请求:

1. 在 Filter 中输入 `login` 或 `sys`
2. 找到登录表单提交的请求
3. 记录以下信息:
   - **Request URL**: 完整的登录 API 地址
   - **Request Method**: POST 或 GET
   - **Form Data**: 表单字段名称 (如 `username`, `password`, `_csrf` 等)

**示例:**
```
Request URL: https://jwxt.bupt.edu.cn/auth/login
Request Method: POST
Form Data:
  userName: 你的学号
  userPwd: 你的密码
  randCode: (如果有验证码)
  _csrf: abc123... (如果有 CSRF token)
```

然后修改 `src/lib.rs` 中的 `config::LOGIN_API`:

```rust
pub const LOGIN_API: &str = "https://jwxt.bupt.edu.cn/auth/login";
```

### 3. 获取课程列表 API 端点

1. 在 Network 面板中查找课程列表请求
2. 可能的方式:
   - **HTML 页面**: 访问类似 `/xs/kcxs.html` 的页面
   - **JSON API**: 访问类似 `/api/courses` 的接口

**如果是 JSON API**, 记录响应格式:
```json
{
  "courses": [
    {
      "id": "12345",
      "name": "高等数学",
      "teacherName": "张三",
      "classTime": "周一 8:00-9:40",
      "location": "教三楼 201",
      "maxCapacity": 60,
      "currentEnrollment": 45,
      "status": true
    }
  ]
}
```

然后修改 `src/lib.rs` 中的 `config::COURSES_URL`:

```rust
pub const COURSES_URL: &str = "https://jwxt.bupt.edu.cn/api/courses";
```

### 4. 获取抢课 API 端点

1. 在 Network 面板中查找选课请求
2. 点击"选课"按钮时发送的请求
3. 记录以下信息:
   - **Request URL**: 抢课 API 地址
   - **Request Method**: POST 或 GET
   - **Parameters**: 需要的参数 (课程 ID、CSRF token 等)

**示例:**
```
Request URL: https://jwxt.bupt.edu.cn/xs/xk.do
Request Method: POST
Form Data:
  courseId: 12345
  action: select
  _csrf: abc123...
```

然后修改 `src/lib.rs` 中的 `config::GRAB_API_PREFIX`:

```rust
pub const GRAB_API_PREFIX: &str = "https://jwxt.bupt.edu.cn/xs/xk.do";
```

### 5. 调整 HTML 解析选择器

如果课程列表是 HTML 页面，需要调整 CSS 选择器。

**在浏览器中查看课程列表页面的 HTML 结构:**

1. 右键点击课程表格 → "检查" (Inspect)
2. 查看表格的 class 名称和结构

**示例 HTML 结构:**
```html
<table class="table table-striped course-list">
  <tbody>
    <tr class="course-row" data-id="12345">
      <td class="course-id">12345</td>
      <td class="course-name">高等数学</td>
      <td class="teacher-name">张三</td>
      <td class="class-time">周一 8:00-9:40</td>
      <td class="location">教三楼 201</td>
      <td class="capacity">60</td>
      <td class="enrolled">45</td>
      <td class="status">可选</td>
    </tr>
  </tbody>
</table>
```

然后修改 `parse_course_list` 函数中的选择器:

```rust
let row_selector = Selector::parse("table.course-list tr.course-row").unwrap();
```

并根据实际的列顺序调整索引:
```rust
let course_id = cells.get(0)...;  // 第 1 列
let name = cells.get(1)...;       // 第 2 列
let teacher = cells.get(2)...;    // 第 3 列
// ...
```

### 6. 调整 JSON 解析结构体

如果课程数据是 JSON 格式，确保 `JsonCourse` 结构体的字段名与 API 返回的一致:

```rust
#[derive(Deserialize)]
struct JsonCourse {
    #[serde(default, rename = "courseId")]  // 如果 API 返回的是驼峰命名
    id: String,
    #[serde(default, rename = "courseName")]
    name: String,
    #[serde(default, alias = "teacherName", alias = "instructor")]
    teacher: String,
    // ...
}
```

## 🔍 常见问题排查

### 问题 1: 登录失败
- 检查登录 API URL 是否正确
- 检查表单字段名称是否匹配
- 查看是否需要处理验证码
- 检查是否需要 CSRF token

### 问题 2: 无法获取课程列表
- 确认已登录且会话有效
- 检查课程列表 URL 是否正确
- 查看响应格式是 HTML 还是 JSON
- 调整 HTML 选择器或 JSON 结构体

### 问题 3: 抢课失败
- 检查抢课 API URL 是否正确
- 确认是否需要 CSRF token
- 查看错误响应内容
- 检查课程 ID 格式是否正确

## 🛠️ 测试建议

1. **先手动测试**: 在浏览器中完整走一遍流程，确保理解每个步骤
2. **启用详细日志**: 在代码中添加 `println!` 输出调试信息
3. **逐步验证**: 先测试登录，再测试获取课程列表，最后测试抢课
4. **使用测试账号**: 避免使用真实账号进行频繁测试

## 📝 配置示例

完整的 `config` 模块示例:

```rust
pub mod config {
    // 根据实际抓包结果修改以下 URL
    pub const LOGIN_URL: &str = "https://jwxt.bupt.edu.cn/";
    pub const LOGIN_API: &str = "https://jwxt.bupt.edu.cn/auth/login";
    pub const COURSES_URL: &str = "https://jwxt.bupt.edu.cn/xs/kcxs.html";
    pub const GRAB_API_PREFIX: &str = "https://jwxt.bupt.edu.cn/xs/xk.do";
    pub const USER_AGENT: &str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
}
```

## 📚 参考资料

- [Scraper Crate 文档](https://docs.rs/scraper/)
- [Reqwest Crate 文档](https://docs.rs/reqwest/)
- [Chrome DevTools Network 面板教程](https://developer.chrome.com/docs/devtools/network/)

---

**注意**: 由于教务系统可能会更新，请定期检查和更新这些配置。
