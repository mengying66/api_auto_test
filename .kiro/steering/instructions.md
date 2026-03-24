# 🤖 Kiro 全局开发规范 (Merged Persistent Instructions)
> 本文件为项目最高优先级指令。AI 在生成任何代码、执行任何任务前必须严格遵守。
> 适用技术栈：Python (Backend) + React/TypeScript (Frontend)

## 1. 技术栈约束 (Tech Stack)
- **后端**: Python 3.9+, Flask/FastAPI, SQLAlchemy/Prisma, PostgreSQL
- **前端**: React 18+, TypeScript 5+, TailwindCSS, Shadcn/UI
- **包管理**: 
  - Python: `pip` 或 `poetry` (严禁混用)
  - Frontend: `pnpm` (严禁使用 npm/yarn)
- **环境**: 必须使用 `.env` 管理敏感信息，严禁硬编码 Secret Key。

## 2. 代码生成核心原则 (Core Principles)

### 🐍 Python 后端规范
- **类型注解 (强制)**: 所有函数参数、返回值必须包含 Type Hints。
  - ✅ 正确: `def add(a: int, b: int) -> int:`
  - ❌ 禁止: `def add(a, b):`
- **文档字符串**: 所有公共函数必须包含 Google Style 或 NumPy Style Docstring。
- **错误处理**: 
  - 严禁裸 `except:`，必须捕获具体异常 (如 `ValueError`, `DatabaseError`)。
  - API 响应必须统一格式：`{ "success": bool, "data": Any, "error": str | None }`。
- **数据库**: 
  - 严禁拼接 SQL 字符串，必须使用 ORM 参数化查询。
  - 修改表结构必须先编写 Migration 脚本。

### ⚛️ 前端 (React/TS) 规范
- **类型安全**: 严禁使用 `any`。所有 Props、State、API 响应必须定义 Interface/Type。
- **组件化**: 
  - 单个组件文件不超过 300 行。
  - 必须使用 Functional Components + Hooks。
- **样式**: 优先使用 TailwindCSS 类名，避免内联 style。

## 3. 文件与目录结构 (File Structure)
- **后端**: 
  - `app.py` (入口)
  - `routes/` (路由控制)
  - `models/` (数据库模型)
  - `services/` (业务逻辑)
  - `utils/` (通用工具函数，禁止散落在各处)
- **前端**: 
  - `src/features/[feature-name]/` (功能模块聚合)
  - `src/components/` (通用 UI 组件)
  - `src/lib/` (工具库)
- **配置**: 
  - `.env` (环境变量，不提交到 Git)
  - `.cursorrules` (本规范文件)

## 4. 工作流自动化 (Workflow Automation)
- **生成代码后**: 
  - Python: 自动运行 `black` 格式化 (如果可用) 或遵循 PEP8。
  - Frontend: 自动运行 `pnpm lint`。
- **测试**: 
  - 新功能必须伴随单元测试 (`pytest` for Python, `Jest` for JS)。
  - 修改核心逻辑时，先展示测试计划。
- **文档**: 
  - 修改 API 接口后，必须同步更新 `docs/api.md` 或 Swagger 注释。

## 5. 安全与最佳实践 (Security & Best Practices)
- **XSS 防护**: 前端渲染用户输入时必须转义。
- **SQL 注入**: 100% 依赖 ORM 防注入。
- **日志**: 
  - 后端使用 `logging` 模块，严禁使用 `print()` 调试生产代码。
  - 日志等级区分：INFO (正常流程), WARNING (可恢复错误), ERROR (系统异常)。

## 6. 沟通与响应风格 (Communication Style)
- **思维链**: 解决复杂问题前，先列出步骤计划 (Plan)。
- **代码优先**: 直接给出可运行的代码块，减少理论解释，除非用户询问。
- **中文优先**: 注释、提交信息、对话均使用中文。
- **自我修正**: 如果生成的代码报错，主动分析原因并提供修复方案，不要让用户反复提示。

## 7. 特别指令 (Special Instructions)
- 当用户请求“写一个简单的函数”时，**必须**默认包含：类型注解 + 文档注释 + 基础错误处理。
- 当用户未指定语言时，根据当前打开的文件或项目上下文自动推断 (如当前在 `app.py` 则用 Python)。