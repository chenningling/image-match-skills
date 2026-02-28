---
name: image-match
description: Automatically illustrate articles with relevant Unsplash photos. Performs semantic analysis, inserts image markers with search keywords, searches Unsplash, and selects best matching landscape photos. Use when user wants to 配图, 插图, add images to article, illustrate a blog post, or auto-illustrate text content.
---

# Image Match — 文章智能配图

为文章自动匹配高质量 Unsplash 横版配图。

流程：语义分块 → 插入配图标记 → 脚本搜索图片 → 选择最佳匹配 → 输出配图文章。

## 前置准备

- Python 3.9+ 环境
- 安装依赖（需 `full_network` 权限）：

```bash
pip install -r SKILL_DIR/scripts/requirements.txt
```

- 配置自己的 Unsplash API Access Key（本仓库不会包含任何密钥）：

```bash
export UNSPLASH_ACCESS_KEY=你的_U
```

> `SKILL_DIR` 指本 SKILL.md 所在目录，执行时替换为实际绝对路径。  
> 请在 Unsplash 开发者平台 `https://unsplash.com/developers` 创建应用并获取自己的 Access Key，然后通过环境变量 `UNSPLASH_ACCESS_KEY` 传给脚本。

## 工作流

### Step 1: 获取文章

- 用户提供文件路径 → 直接读取文件内容，**记录原始文件名**（不含扩展名），用于最终输出命名
- 用户在对话中粘贴文章 → 保存为工作区的 `input_article.md`，原始文件名视为 `input_article`

### Step 2: 语义分块 & 配图标记

分析文章内容，在适合配图的位置插入标记，同时确保文章具备基本的 Markdown 排版格式，保存为 `marked_article.md`。

#### 2.0 排版格式化

在插入配图标记的同时，对文章进行基本的 Markdown 格式化处理：

1. **标题层级**：文章大标题用 `#`，章节标题用 `##`，子标题用 `###`
2. **段落分隔**：确保段落之间有空行分隔，避免文字堆叠
3. **列表识别**：明显的列举内容转为有序/无序列表
4. **引用标注**：直接引语使用 `>` 引用格式
5. **保持原意**：仅做格式优化，**不得修改、删减或改写任何原文内容**

#### 2.1 分块策略

1. **语义分块**: 按主题/论点将文章切分为语义块（一个完整论述 = 一个块）
2. **配图决策**: 不是每个块都配图，仅在以下场景插入标记：
   - 有具体场景、事物、活动的描述
   - 话题发生切换，需要视觉过渡
   - 抽象论述需要视觉隐喻辅助理解
3. 标记放在段落**之间**，不放在段落内部，标记独占一行

#### 2.2 数量限制

| 文章长度 | 最大配图数 |
|---------|----------|
| < 1000 字 | 2-3 张 |
| 1000-3000 字 | 4-8 张 |
| > 3000 字 | 8-10 张 |

绝对上限：10 张。

#### 2.3 标记格式

```
<!--IMAGE_N[english search keywords]-->
```

- `N` 为从 1 开始的连续序号
- 关键词必须是英文

#### 2.4 关键词规则（核心）

关键词需要适配 Unsplash 等图库的**传统搜索引擎逻辑**——平台通过关键词匹配摄影师上传时填写的标签和描述，而非语义理解。因此关键词必须**短、准、通用**。

**字数要求**：**2-4 个英文单词**，绝对不超过 4 个词。

| ✅ 好的关键词 | ❌ 差的关键词 | 差在哪里 |
|---|---|---|
| laptop cafe work | person working on laptop in bright cafe | 太长，组合过多 |
| ocean sunrise waves | sunrise over calm ocean waves with golden light | 像句子而非搜索词 |
| whiteboard team meeting | team discussing around whiteboard in office | 堆砌修饰语 |
| child reading tree | child reading book under big tree in park | 介词短语太多 |
| fresh vegetables cutting board | fresh vegetables on wooden cutting board with knife | 超过 4 词 |
| autumn forest road | winding road through colorful autumn forest | 形容词泛滥 |

**规则**：

1. **只保留核心名词**：提取 1-2 个主体名词 + 0-1 个场景/修饰词，去掉介词、冠词、形容词堆砌
2. **用摄影师会打的标签思考**：想象摄影师上传这张照片时会填什么 tag，而不是描述一幅完整画面
3. **优先使用高频通用词**：避免生僻地名、专有名词；如果必须用地名，地名单独算一个词（如 `guilin river landscape`）
4. **抽象主题转为具象物体**：哲学 → `book candle desk`；金融 → `stock chart screen`；团队协作 → `team meeting whiteboard`

#### 2.5 标记示例

```markdown
远程工作已成为现代职场的重要趋势。越来越多企业开始拥抱这种灵活的办公方式。

<!--IMAGE_1[laptop home office work]-->

## 效率与自由的平衡

研究表明，远程工作者的生产力并不低于办公室员工。关键在于找到效率与自由之间的平衡点。

<!--IMAGE_2[woman typing coffee desk]-->

## 团队协作的新方式

视频会议和在线协作工具让远程团队保持紧密联系，甚至催生了新的协作文化。
```

### Step 3: 搜索图片

运行搜索脚本（需 `full_network` 权限）：

```bash
python SKILL_DIR/scripts/search_images.py marked_article.md candidates.json
```

脚本自动：
- 提取所有 `<!--IMAGE_N[...]-->` 标记
- 为每个关键词调用 Unsplash API 搜索横版（landscape）图片
- **搜索降级重试**：若某关键词返回 0 结果，脚本会自动去掉末尾词简化关键词并重试，最多重试 2 次（如 `guilin karst river` → `guilin karst` → `guilin`）
- 重试后仍无结果的位置，在结果中标记 `"fallback": "remove"`
- 每个有结果的位置返回 5 个候选图片，结果中包含 `used_keywords` 字段记录实际命中的关键词
- 结果保存到 `candidates.json`

### Step 4: 选择最佳配图

读取 `candidates.json`，为每个配图位置从候选中选择最优图片。

选择标准（按优先级）：
1. **语义匹配**: `description` 和 `alt_description` 与文章上下文的相关程度
2. **画面质量**: 优先选择有明确主体、构图清晰的图片
3. **情感一致**: 图片情感基调应与所在段落一致
4. **多样性**: 各位置图片应视觉风格多样，避免雷同
5. **兜底**: 如果某位置所有候选都不理想（描述全为空或明显不相关），跳过该位置不配图

对每个位置，记录选中的 `url_regular`、`alt_description`（或 `description`）、`photographer`、`photographer_url`。

### Step 5: 输出配图文章

#### 5.1 输出文件命名

输出文件名基于 Step 1 记录的原始文件名，添加 `_已配图` 后缀：

- 原始文件为 `AI趋势分析.md` → 输出 `AI趋势分析_已配图.md`
- 原始文件为 `my_article.txt` → 输出 `my_article_已配图.md`
- 用户粘贴文本（无文件名）→ 输出 `input_article_已配图.md`

输出目录与原始文件相同（用户提供了路径时），或保存在工作区根目录。

#### 5.2 图片替换

将每个配图标记替换为实际图片：

```markdown
![图片描述](url_regular)

*Photo by [摄影师名](photographer_url) on [Unsplash](https://unsplash.com)*
```

替换规则：
- 图片描述优先用 `alt_description`，为空则用 `description`，都为空则用搜索关键词
- 必须保留 Unsplash 归属信息（摄影师署名 + Unsplash 链接）
- `candidates.json` 中标记了 `"fallback": "remove"` 的位置，以及 Step 4 判定为不理想的位置，直接删除对应配图标记，不留空白

#### 5.3 排版检查

输出前确认文章排版格式完整：
- 标题层级正确（`#` / `##` / `###`）
- 段落之间有空行
- 图片前后各有一个空行，确保渲染正常
- 无多余空行（连续空行不超过 1 行）

完成后向用户报告：
- 总配图数量
- 每张图的关键词和选择原因（简要）
- 输出文件路径
