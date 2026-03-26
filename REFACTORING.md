# BUPT 工具重构说明

## 重构概述

本次重构将原有的单文件 `BUPT_Tool.py`（550 行）拆分为模块化设计，提高了代码的可维护性、可读性和可扩展性。

## 模块结构

```
src/bupt_internal/
├── __init__.py          # 包初始化，导出 BUPT 类
├── bupt.py              # 主入口类，整合所有功能
├── config_manager.py    # 配置管理模块
├── auth.py              # 认证和会话管理模块
├── course_grabber.py    # 课程抢课核心逻辑模块
└── BUPT_Tool.py         # 原始文件（保留用于参考）
```

## 各模块职责

### 1. `config_manager.py` - 配置管理
- **ConfigManager** 类：处理配置文件的读写
- **Credentials** 数据类：存储用户名和密码
- **CourseConfig** 数据类：存储课程列表配置
- 支持配置文件的自动创建和加载
- 使用 dataclasses 提供类型安全的配置对象

### 2. `auth.py` - 认证管理
- **AuthManager** 类：处理用户登录和会话验证
- `login()`: 执行登录操作
- `verify_session()`: 验证并激活选课会话
- `login_with_verify()`: 一站式登录并验证

### 3. `course_grabber.py` - 课程抢课
- **CourseGrabber** 类：处理课程的搜索、选择和退选
- `search_courses()`: 搜索匹配的课程
- `select_course()`: 选择指定类型的课程
- `get_chosen_courses()`: 获取已选课程列表
- `find_chosen_course()`: 查找特定已选课程
- `drop_course()`: 退选课程

### 4. `bupt.py` - 主入口
- **BUPT** 类：提供统一的公共 API
- 整合配置管理、认证和抢课功能
- 提供向后兼容的静态方法接口
- 支持多线程抢课

## 主要改进

### 1. 单一职责原则
每个模块只负责一个明确的功能领域：
- 配置管理只处理配置文件
- 认证模块只处理登录和会话
- 抢课模块只处理课程相关操作

### 2. 类型提示
使用 Python 类型提示提高代码可读性和 IDE 支持：
```python
def get_chosen_courses(self, session: requests.Session) -> Dict[str, str]:
```

### 3. 数据类
使用 `dataclass` 简化数据容器类的定义：
```python
@dataclass
class CourseConfig:
    public_courses: List[str] = field(default_factory=list)
    required_courses: List[str] = field(default_factory=list)
    optional_courses: List[str] = field(default_factory=list)
```

### 4. 文档字符串
为所有公共方法和类添加详细的 docstring，包括：
- 功能描述
- 参数说明
- 返回值说明
- 使用示例

### 5. 错误处理
改进错误处理和日志记录：
- 使用具体的异常类型
- 提供更详细的错误信息
- 统一的日志记录方式

### 6. 代码复用
消除重复代码：
- 搜索参数和数据模板集中管理
- URL 常量统一定义
- 通用逻辑提取为辅助方法

## 向后兼容性

重构后的代码保持与原有 API 的完全兼容：

```python
# 原有代码仍然可以正常运行
from bupt_internal import BUPT

BUPT.init()
session = BUPT.login_with_verify()
BUPT.grab_all_course(session)
BUPT.unchoose_course(session, "课程名")
```

## 使用示例

### 基本用法
```python
from bupt_internal import BUPT

# 初始化
BUPT.init()

# 登录
session = BUPT.login_with_verify()

# 抢课
BUPT.grab_all_course(session)

# 查询已选课程
courses = BUPT.get_chosen_courses(session)
print(courses)

# 退课
BUPT.unchoose_course(session, "课程名")
```

### 高级用法
```python
from bupt_internal import BUPT

BUPT.init()
session = BUPT.login_with_verify()

# 单独抢某类课程
BUPT.grab_required_course(session, "高等数学")
BUPT.grab_optional_course(session, "体育")
BUPT.grab_public_course(session, "艺术鉴赏")

# 查询特定课程
course_name, course_id = BUPT.get_chosen_course_id_by_name(session, "高等数学")
```

## 测试

运行测试脚本验证功能：
```bash
python test.py
```

## 后续改进建议

1. **异步支持**: 使用 asyncio 和 aiohttp 提高并发性能
2. **配置加密**: 对配置文件中的密码进行加密存储
3. **自动换课**: 实现 `grab_when_class_unoccupied` 功能
4. **通知系统**: 抢课成功/失败时发送通知
5. **Web 界面**: 提供 Web 界面方便非技术用户使用
6. **单元测试**: 添加完整的单元测试覆盖

## 注意事项

- 本项目仅作为学习交流使用，请勿用于其它用途
- 在校外网络使用时，请先连接 ATrust VPN
- 配置文件编码为 UTF-8（原为 GBK，已更新）
