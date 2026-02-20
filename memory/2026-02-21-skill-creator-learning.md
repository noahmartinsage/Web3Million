# 技能创建器学习记录

**学习时间**: 2026-02-21 01:25 AM  
**学习来源**: `skills/skill-creator/SKILL.md` + references

---

## 📚 核心概念

### 什么是技能 (Skills)
技能是模块化的独立包，用于扩展 AI 助手的能力，提供：
1. **专业化工作流** - 特定领域的多步骤流程
2. **工具集成** - 处理特定文件格式或 API 的指令
3. **领域专业知识** - 公司特定的知识、架构、业务逻辑
4. **捆绑资源** - 脚本、参考资料和资产

### 技能结构
```
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter (name + description)
│   └── Markdown 指令
├── scripts/ (可选) - 可执行代码
├── references/ (可选) - 文档资料
└── assets/ (可选) - 输出用资源
```

---

## 🎯 核心原则

### 1. 简洁至上 (Concise is Key)
- 上下文窗口是公共资源
- 只添加 AI 原本不知道的信息
- 挑战每一段信息："AI 真的需要这个解释吗？"
- 优先使用简洁示例而非冗长说明

### 2. 设置适当的自由度 (Degrees of Freedom)
| 自由度 | 使用场景 | 示例 |
|--------|----------|------|
| **高** | 多种方法都有效，依赖上下文决策 | 文本指令 |
| **中** | 有推荐模式，可接受一些变化 | 伪代码或带参数的脚本 |
| **低** | 操作脆弱易错，需要一致性 | 具体脚本，少参数 |

### 3. 渐进式披露 (Progressive Disclosure)
三层加载系统：
1. **元数据** (name + description) - 始终在上下文中 (~100 词)
2. **SKILL.md 主体** - 触发时加载 (<5k 词)
3. **捆绑资源** - 按需加载 (无限制)

---

## 🛠️ 技能创建流程

### Step 1: 理解技能
- 收集具体使用示例
- 明确触发场景
- 确定功能边界

### Step 2: 规划内容
分析每个示例，识别需要的：
- `scripts/` - 可重复使用的代码
- `references/` - 文档和参考资料
- `assets/` - 模板和资源文件

### Step 3: 初始化技能
```bash
scripts/init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]
```

### Step 4: 编辑技能
- 先实现可复用资源 (scripts/references/assets)
- 测试脚本确保无 bug
- 更新 SKILL.md 的 frontmatter 和主体

### Step 5: 打包技能
```bash
scripts/package_skill.py <path/to/skill-folder>
```
自动验证 + 生成 .skill 文件 (zip 格式)

### Step 6: 迭代优化
1. 在真实任务中使用
2. 发现低效点
3. 更新 SKILL.md 或资源
4. 重新测试

---

## 📝 SKILL.md 编写规范

### Frontmatter (YAML)
```yaml
---
name: skill-name
description: 清晰描述技能功能和触发场景
---
```

**description 要点**:
- 包含技能做什么 + 何时使用
- 列出具体触发场景 (1)(2)(3)...
- 不要放"何时使用"在主体中（主体只在触发后加载）

### 主体编写
- 使用祈使句/不定式
- 保持 <500 行
- 长内容拆分到 references 文件
- 直接引用参考文件，说明何时读取

---

## 🎨 设计模式

### 顺序工作流
```markdown
流程概述：
1. 分析表单 (run analyze_form.py)
2. 创建字段映射 (edit fields.json)
3. 验证映射 (run validate_fields.py)
4. 填充表单 (run fill_form.py)
5. 验证输出 (run verify_output.py)
```

### 条件工作流
```markdown
决策点：
- 创建新内容？→ 跟随"创建工作流"
- 编辑现有内容？→ 跟随"编辑工作流"
```

### 模板模式
**严格要求**：使用精确模板结构  
**灵活指导**：提供默认格式，允许调整

### 示例模式
提供输入/输出对，展示期望的风格和详细程度

---

## ⚠️ 注意事项

### 技能命名
- 小写字母 + 数字 + 连字符
- <64 字符
- 动词开头描述动作
- 按工具命名空间提高清晰度 (如 `gh-address-comments`)

### 不要包含的文件
- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- 其他辅助文档

**原则**: 只包含 AI 执行任务必需的文件

### 参考文件组织
- 保持一层深度（直接从 SKILL.md 引用）
- >100 行的文件添加目录
- 按领域/框架/变体组织内容

---

## 🚀 内化到 Web3Million 系统

### 已掌握机制
1. ✅ 技能结构设计原则
2. ✅ 渐进式披露上下文管理
3. ✅ 工作流模式（顺序 + 条件）
4. ✅ 输出模式（模板 + 示例）
5. ✅ 创建流程 6 步骤
6. ✅ 验证和打包自动化

### 下一步行动
- 应用这些原则优化现有技能
- 为 Web3Million 系统创建专业化技能
- 建立技能迭代和测试流程

---

**学习状态**: 完成 ✅  
**下一步**: 实践应用，创建/优化技能
