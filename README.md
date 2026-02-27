# Image Match Skills

为长文自动生成高质量配图的 Cursor Skill，基于 **LLM 语义分块 + Unsplash 图片搜索**，一键生成带配图的 Markdown 文章。

## 功能简介

- **语义分块**：大模型按语义段落理解文章结构，而不是机械按字数切分。
- **智能决策是否配图**：并非每段都配图，仅在需要视觉辅助的关键段落插入配图。
- **结构化配图标记**：以 `<!--IMAGE_N[english keywords]-->` 的形式插入标记，关键词为可被摄影表现的具体场景/物体，便于检索。
- **调用 Unsplash 搜索 API**：Python 脚本按关键词搜索 Unsplash，强制使用 `orientation=landscape` 横图。
- **多候选 + 智能选择**：每个位置默认取 5 张候选图，由 LLM 结合上下文选择最合适的一张。
- **生成最终配图文章**：把标记替换为真实图片 URL，自动追加摄影师与 Unsplash 归属信息，输出 Markdown。

## 目录结构

```bash
image-match-skills/
├── SKILL.md                  # Skill 主说明与使用流程
├── README.md                 # 本项目说明
└── scripts/
    ├── search_images.py      # 调用 Unsplash API 的搜索脚本
    └── requirements.txt      # Python 依赖（requests）
```

> `.cursor/skills/image-match/` 下是在本地项目中安装后的拷贝，一般不需要提交到其他仓库，可通过 `.gitignore` 忽略。

## 安装与使用

### 1. 克隆仓库

```bash
git clone git@github.com:chenningling/image-match-skills.git
cd image-match-skills
```

### 2. 安装依赖

```bash
pip install -r scripts/requirements.txt
```

### 3. 配置 Unsplash API Key（重要）

本项目 **不会** 提供任何真实 API Key，仓库中所有密钥均已移除。你需要：

1. 打开 Unsplash 开发者平台：`https://unsplash.com/developers`
2. 使用自己的账号登录并创建一个应用（Demo 级别即可）
3. 在应用详情页获取 `Access Key`
4. 在终端中设置环境变量（以 macOS / Linux 为例）：

```bash
export UNSPLASH_ACCESS_KEY=你的_access_key
```

> Windows PowerShell 可使用：`$env:UNSPLASH_ACCESS_KEY="你的_access_key"`

脚本 `search_images.py` 会从环境变量 **`UNSPLASH_ACCESS_KEY`** 读取密钥，如果未设置会直接报错提示。

### 4. 标注配图位置（LLM / 手动均可）

推荐在 Cursor 中配合本 Skill 使用，由 LLM 自动完成“语义分块 + 标记插入”。

如果你希望在命令行手动体验，可以自己在 Markdown 里加入标记，例如：

```markdown
远程工作已成为现代职场的重要趋势。越来越多企业开始拥抱这种灵活的办公方式。

<!--IMAGE_1[person working on laptop in bright home office]-->

## 效率与自由的平衡

研究表明，远程工作者的生产力并不低于办公室员工。关键在于找到效率与自由之间的平衡点。

<!--IMAGE_2[focused woman typing on computer with coffee cup]-->
```

规则：
- 标记格式：`<!--IMAGE_N[english search keywords]-->`
- `N` 为从 1 开始的连续编号
- 关键词必须是 **英文**，且为可拍摄的具象场景/物体（3–6 个英文单词）

### 5. 调用脚本搜索图片

假设你已经有标记好的 Markdown 文件 `marked_article.md`：

```bash
python scripts/search_images.py marked_article.md output/candidates.json
```

脚本行为：
- 解析所有 `<!--IMAGE_N[...]-->` 标记
- 对每个关键词调用 Unsplash `/search/photos` 接口：
  - `orientation=landscape`
  - `order_by=relevant`
  - `content_filter=high`
  - 默认每个位置 `per_page=5`
- 将候选结果写入 `output/candidates.json`

你可以在 Cursor 里继续用 LLM 读取 `candidates.json`，结合上下文选择每个位置最合适的图片，并把标记替换为真实图片链接，生成最终的 `output_article.md`。

### 6. 作为 Cursor Project Skill 使用

如果你想在某个 Cursor 项目中长期使用这个 Skill：

1. 在目标项目根目录下创建目录：`.cursor/skills/image-match/`
2. 将本仓库中的 `SKILL.md` 与 `scripts/` 拷贝进去：

```bash
mkdir -p .cursor/skills/image-match/scripts
cp SKILL.md .cursor/skills/image-match/SKILL.md
cp scripts/* .cursor/skills/image-match/scripts/
```

3. 在该项目中与 AI 对话时，说「帮我给这篇文章配图」，Cursor 会自动根据 `SKILL.md` 中的说明调用脚本和工作流。

## 图片 API 替换说明

- 本项目当前使用 **Unsplash Search Photos API**：`https://api.unsplash.com/search/photos`
- 所有调用都只依赖环境变量 `UNSPLASH_ACCESS_KEY`，因此：
  - 你可以在本地/服务器安全地配置自己的 Key
  - 随时可以更换为其他 Key，而无需改动代码或提交新版本
- 如果未来你希望更换到其他图片源（如 Pexels、Pixabay 等）：
  - 只需修改 `scripts/search_images.py` 中的 `API_URL` 与参数组装逻辑
  - 保持输出 JSON 结构不变，后续 LLM 选图与替换逻辑可以完全复用

## 安全与合规

- 仓库中 **不包含**、也不会包含任何真实的 Unsplash API Key。
- 建议在生产环境中通过环境变量或秘密管理服务（如 GitHub Actions Secrets、1Password、Vault 等）注入 `UNSPLASH_ACCESS_KEY`，避免写入代码或配置文件。
- 使用 Unsplash 图片时，请遵循其 [API 使用条款](https://unsplash.com/documentation) 和授信规范：
  - 在文章中保留类似：`Photo by [摄影师名](链接) on Unsplash` 的署名信息（本项目生成的 Markdown 已自动附带）。
