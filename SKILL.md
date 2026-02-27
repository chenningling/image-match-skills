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

- 用户提供文件路径 → 直接读取文件内容
- 用户在对话中粘贴文章 → 保存为工作区的 `input_article.md`

### Step 2: 语义分块 & 配图标记

分析文章内容，在适合配图的位置插入标记，保存为 `marked_article.md`。

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

关键词必须描述**具体的、可被摄影表现的场景或物体**，3-6 个英文单词。

| ✅ 好的关键词 | ❌ 差的关键词 |
|---|---|
| person working on laptop in cafe | remote work |
| sunrise over calm ocean waves | beauty |
| team discussing around whiteboard | collaboration |
| child reading book under tree | education |
| fresh vegetables on wooden cutting board | healthy eating |
| winding road through autumn forest | journey |

规则：
- 用「场景描述」代替「概念词」
- 包含主体 + 环境/动作，形成画面感
- 抽象主题（哲学、金融等）需转化为视觉隐喻

#### 2.5 标记示例

```markdown
远程工作已成为现代职场的重要趋势。越来越多企业开始拥抱这种灵活的办公方式。

<!--IMAGE_1[person working on laptop in bright home office]-->

## 效率与自由的平衡

研究表明，远程工作者的生产力并不低于办公室员工。关键在于找到效率与自由之间的平衡点。

<!--IMAGE_2[focused woman typing on computer with coffee cup]-->

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
- 每个位置返回 5 个候选图片
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

生成 `output_article.md`，将每个配图标记替换为实际图片：

```markdown
![图片描述](url_regular)

*Photo by [摄影师名](photographer_url) on [Unsplash](https://unsplash.com)*
```

替换规则：
- 图片描述优先用 `alt_description`，为空则用 `description`，都为空则用搜索关键词
- 必须保留 Unsplash 归属信息（摄影师署名 + Unsplash 链接）
- 被跳过的位置（Step 4 兜底情况）直接删除标记，不留空白

完成后向用户报告：
- 总配图数量
- 每张图的关键词和选择原因（简要）
- 输出文件路径
