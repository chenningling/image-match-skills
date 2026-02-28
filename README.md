# Image Match — 文章智能配图

为长文自动生成高质量配图的 AI Agent Skill，基于 **LLM 语义分块 + Unsplash 图片搜索**，一键生成带配图、带排版的 Markdown 文章。

适用于所有支持 Agent Skills 的 AI 编程助手和智能体平台。

## 功能简介

- **语义分块**：大模型按语义段落理解文章结构，在适合配图的位置插入标记。
- **基本排版**：配图同时做 Markdown 格式化（标题层级、段落空行、列表、引用等），不改写原文。
- **短关键词**：标记采用 **2–4 个英文单词**，适配 Unsplash 等图库的传统搜索逻辑，提高命中率。
- **结构化配图标记**：以 `<!--IMAGE_N[english keywords]-->` 形式插入，便于脚本解析与检索。
- **Unsplash 搜索 + 降级重试**：脚本按关键词搜索横版图；若返回 0 结果则自动简化关键词重试（最多 2 次），仍无结果则标记为 `remove`，最终输出时删除该位置。
- **多候选 + 智能选择**：每个位置默认 5 张候选，由 LLM 结合上下文选最合适的一张。
- **输出命名**：最终文章命名为 **「原始文件名_已配图.md」**，与原文同目录或工作区根目录。

## 目录结构

```
image-match1.0/
├── SKILL.md                     # Skill 主说明与完整工作流
├── README.md                    # 本项目说明
├── scripts/
│   ├── search_images.py         # Unsplash 搜索脚本（含降级重试）
│   └── requirements.txt         # Python 依赖（requests）
├── output/                      # 工作目录（可忽略提交）
│   ├── input_article.md         # 转换后的原文
│   ├── marked_article.md        # 带配图标记 + 排版的中间稿
│   ├── candidates.json          # 每位置候选图片 JSON
│   └── *_已配图.md              # 最终配图文章（或保存到用户指定路径）
└── .cursor/skills/image-match/  # Cursor 技能目录（可选）
    ├── SKILL.md
    └── scripts/
        ├── search_images.py
        └── requirements.txt
```

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

本项目 **不会** 提供任何真实 API Key。你需要：

1. 打开 [Unsplash 开发者平台](https://unsplash.com/developers)，登录并创建应用（Demo 即可）。
2. 在应用详情页获取 **Access Key**。
3. 在终端设置环境变量：

```bash
export UNSPLASH_ACCESS_KEY=你的_access_key
```

> Windows PowerShell：`$env:UNSPLASH_ACCESS_KEY="你的_access_key"`

脚本从环境变量 **`UNSPLASH_ACCESS_KEY`** 读取密钥，未设置时会报错并提示。

### 4. 标注配图位置（推荐由 LLM 按 SKILL 完成）

在支持 Skills 的 AI 助手中说「帮我给这篇文章配图」，由 LLM 自动完成：获取文章 → 语义分块 + 排版 + 插入标记 → 运行脚本 → 选图 → 输出「原名_已配图.md」。

也可手动在 Markdown 中加入标记，例如：

```markdown
<!--IMAGE_1[guilin karst river sunrise]-->

## 一、去桂林前，先理清这三座城

很多初访者容易混淆桂林、阳朔和龙胜的关系……
```

规则：

- 格式：`<!--IMAGE_N[english search keywords]-->`，`N` 为从 1 开始的连续编号。
- 关键词必须为 **英文**，**2–4 个词**，描述可被摄影表现的具体场景/物体（如 `laptop cafe work`、`rice terraces sunrise`），避免长句或堆砌形容词。

### 5. 调用脚本搜索图片

假设已有带标记的 `marked_article.md`：

```bash
python3 scripts/search_images.py output/marked_article.md output/candidates.json
```

脚本行为：

- 解析所有 `<!--IMAGE_N[...]-->` 标记（最多 10 个）。
- 对每个关键词调用 Unsplash `/search/photos`：
  - `orientation=landscape`、`order_by=relevant`、`content_filter=high`
  - 每位置默认 `per_page=5`
- **搜索降级重试**：若某关键词返回 0 结果，自动去掉末尾一词简化后重试，最多重试 2 次；仍无结果则在结果中标记 `"fallback": "remove"`。
- 结果写入 `output/candidates.json`，每条包含 `used_keywords`（实际命中的关键词）、`candidates` 列表，以及可能存在的 `fallback: "remove"`。

之后由 LLM 读取 `candidates.json`，为每个有候选的位置选图，将标记替换为图片 Markdown（含 Unsplash 署名），并删除 `fallback: "remove"` 的标记，生成 **「原始文件名_已配图.md」**。

### 6. 作为项目级 Skill 安装（如 Cursor）

1. 在项目中创建 Skill 目录（如 `.cursor/skills/image-match/`），将本仓库的 `SKILL.md` 与 `scripts/` 拷贝到该目录。
2. 在对话中说「帮我给这篇文章配图」或「使用 image-match 为 @文件 配图」，助手会按 `SKILL.md` 执行完整工作流。

## 图片 API 与扩展

- 当前使用 **Unsplash Search Photos API**：`https://api.unsplash.com/search/photos`。
- 密钥仅通过环境变量 `UNSPLASH_ACCESS_KEY` 传入，便于本地/服务器安全配置，更换 Key 无需改代码。
- 若需更换图源（如 Pexels、Pixabay）：修改 `scripts/search_images.py` 的 `API_URL` 与请求逻辑，保持输出 JSON 结构（含 `candidates`、`used_keywords`、`fallback` 等），LLM 选图与替换逻辑可复用。

## 安全与合规

- 仓库中 **不包含** 任何真实 Unsplash API Key。
- 建议通过环境变量或密钥管理服务（如 GitHub Secrets、1Password 等）注入 `UNSPLASH_ACCESS_KEY`。
- 使用 Unsplash 图片须遵守其 [API 使用条款](https://unsplash.com/documentation)；生成的文章已自动附带 `Photo by [摄影师](链接) on Unsplash` 署名。
