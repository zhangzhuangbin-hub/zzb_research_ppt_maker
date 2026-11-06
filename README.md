# zzb_research_ppt_maker

面向中文科研汇报、组会、开题、项目评审与答辩的个人 Codex 技能。

## 当前版本的设计约定

- 普通内容页高信息密度、充分使用页面，检查整页与面板内部空洞；有效图文区域包络以可用区90%—95%为制作起点。
- 默认颜色以用户认可截图取样为准，主蓝`#0865CE`、标题深蓝`#071B50`、强调红`#A83837`。浅底`#E9F2FA`/`#EDF4FB`、分割`#DDE7F0`，完整参数见`assets/style-tokens.json`。
- [35套独立方案](references/reference-recipes.md)分别覆盖原33张图和2张修订样例，每套包含用途、区域配置、图文组织、关系、组件、充实方法、变体及实施条件。
- [组件菜单](references/component-options.md)提供独立可组合的页眉、题签、箭头、图组、解释、结论及层次方案。
- [原生公式规范](references/equations.md)覆盖公式编辑器、分式、矩阵、上下标、数学字体、完整显示、源式对照及重开编辑验收。

示例调用可加“选R07主体、H3页眉、A2渐变箭头、F3浅底结论；高密度满幅；公式用原生编辑器”。
根据33张用户提供的科研PPT参考截图，提炼紧凑图文论证、科研配色、关系图形和可编辑排版规范。

## 能做什么

- 根据研究论证选择版式，组织问题、任务、方法、证据和结论。
- 统一字体、字号、颜色、图文比例、标题标识与贯穿内容区的横线。
- 使用梯形题签、圆角标签、渐变透明箭头、虚线框、对话框、浅灰分割与轻阴影。
- 保持图组边界对齐，表格文字和数据水平、垂直居中。
- 提供完整提示词与研究必要性、方法框架、实验结果、计划指标等场景提示词。
- 在现有汇报中追加或修改指定页面，保留原生文本、图形、箭头和表格的编辑能力。
- 对实际PPTX检查字号、图片包络占比、越界、分散文字、透明渐变、阴影和表格对齐线索。

技能提供设计与制作规则。实际生成、编辑和渲染PPT需要当前 Codex 环境具备相应演示文稿工具，图片生成需具备可用的生图工具。

## 安装与部署

将整个仓库放入个人 Codex 技能目录。目标目录应包含 `SKILL.md`，并与 `agents`、`references`、`assets`、`scripts` 同级。

### Windows PowerShell

```powershell
$skillsRoot = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $env:USERPROFILE '.codex\skills'
}
New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
$skillPath = Join-Path $skillsRoot 'zzb_research_ppt_maker'
git clone https://github.com/zhangzhuangbin-hub/zzb_research_ppt_maker.git $skillPath
Test-Path (Join-Path $skillPath 'SKILL.md')
```

最后一条命令应返回 `True`。默认安装位置为 `%USERPROFILE%\.codex\skills\zzb_research_ppt_maker`。

### macOS / Linux

```bash
skills_root="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skills_root"
git clone https://github.com/zhangzhuangbin-hub/zzb_research_ppt_maker.git \
  "$skills_root/zzb_research_ppt_maker"
test -f "$skills_root/zzb_research_ppt_maker/SKILL.md" && echo "Skill files installed"
```

也可以从 GitHub 下载 ZIP，解压后将目录命名为 `zzb_research_ppt_maker`，放入上述 `skills` 目录。确认目录下直接存在 `SKILL.md`，避免额外嵌套一层仓库文件夹。

安装后重新打开 Codex，或在重新加载技能后新建会话，通过技能列表或下方调用语句确认可用。当前 Windows 本机已通过 Codex 技能发现接口验证，名称为 `zzb_research_ppt_maker`，用户级启用。

仓库沿用用户指定的下划线名称。部分技能创建辅助检查器使用连字符命名规则，会报告命名格式问题，可结合实际 Codex 技能发现结果核对兼容性。

### 更新

进入已安装的技能目录后执行以下命令。

```bash
git pull --ff-only
```

如果安装目录中有自己的修改，先查看 `git status` 并保存修改，再更新。通过 ZIP 安装时，下载新版并更新对应文件。

## 怎么使用

在 Codex 会话中显式调用 `$zzb_research_ppt_maker`，同时提供课题内容、图证、目标文件与操作范围。

### 在现有汇报中新增页面

```text
使用 $zzb_research_ppt_maker，根据我提供的资料，在“课题汇报.pptx”末尾新增2页。
第1页说明拆解任务中的产线仿真、序列规划和机器人作业对几何信息的需求，
由这些需求引出获得CAD模型的必要性。
第2页说明未知电池CAD缺失的问题，以及点云重建CAD的研究切入点。
参考技能中的优秀页面选择版式，保留可编辑文本、图形和关系箭头，
完成后渲染检查，并核对原有页面。
```

### 先生成提示词

```text
使用 $zzb_research_ppt_maker，先为研究必要性页生成完整提示词。
主题为退役动力电池机器人智能拆解。
请明确版式、完整文案、图片位置、配色、字体层级和渐变透明箭头参数。
当前先交付提示词。
```

### 调整指定页面

```text
使用 $zzb_research_ppt_maker，修改现有汇报第2页。
保留已确认的研究逻辑，参考第07、22张样例，调整图文层级和关系表达。
统一页眉、题签、浅灰分割、渐变箭头和图组边界，文字与图形可编辑。
```

### 检查PPTX

在本仓库目录运行以下命令。检查脚本仅使用 Python 标准库。

```bash
python scripts/audit_pptx.py "/path/to/report.pptx" --output "/path/to/audit.json"
python scripts/audit_pptx.py "/path/to/report.pptx" --slides 2 3
```

自动报告用于筛选需要人工复核的对象。实际文字换行、图像完整性、逻辑方向、主题继承以及渐变效果仍需结合渲染检查。

## 设计规范与完整提示词

| 文件 | 内容 |
| --- | --- |
| [SKILL.md](SKILL.md) | 技能入口、工作流与核心约定 |
| [完整提示词库](references/prompt-library.md) | 跨会话调用、完整创作、提示词先行及各类页面提示词 |
| [视觉系统](references/visual-system.md) | 字体、字号、蓝白与紫白配色、透明度、网格与图文比例 |
| [组件规范](references/components.md) | 标题、题签、渐变箭头、虚线框、对话框、阴影、标识与表格 |
| [版式库](references/layout-patterns.md) | 按论证关系选择主体结构 |
| [33图索引](references/reference-catalog.md) | 每张样例的优秀区域与布局观察 |
| [制作约定](references/production.md) | 现有文件编辑、原生对象、图源与兼容处理 |
| [质量检查](references/qa.md) | 交付前逐项核对与修正 |

建议先查看最相关的2—3张优秀页面，再阅读对应规范。字号、色值、透明度、阴影和面积比例均为可调整的制作起点。

## 目录结构

```text
zzb_research_ppt_maker/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── references/
├── assets/
│   ├── reference-atlas/       # 33张优秀区域、联系表与来源记录
│   └── reference-cases/       # 前7组对照材料
└── scripts/
    ├── audit_pptx.py
    ├── build_reference_atlas.py
    └── extract_reference_cases.py
```

图集已包含在仓库中，正常使用无需重新裁图。重建图集需提供原始33张截图并安装 Pillow，可先运行 `python scripts/build_reference_atlas.py --help` 查看参数。

## 参考材料与内容边界

参考截图用于学习版式与样式。部分上方为布局占位示意，第11张为单页编辑器截图，第05、13张前后主题不同，索引已分别记录。

制作新汇报时，应依据实际项目材料和可追溯数据，标明实测、估算、预测及示意状态。截图中的机构、人物、标识、政策和科研结论需要按实际课题重新核对。参考图保留原有第三方内容，使用和再分发时应尊重相应权利。
