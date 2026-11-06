"""Build portable positive-slide crops and an annotated index from 33 screenshots."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

# Bounds refer to the 949 x 2048 displayed screenshot. Originals may be larger.
CASES = [
    (1,'制备与器件集成','paired',(29,958,920,1461),'中心主图＋双侧过程链','中央主机制最大，窄侧栏放制备过程，局部验证贴近相关图。'),
    (2,'材料定制与应用路线','paired',(29,958,920,1461),'上下双层路线','长渐变箭头串联上层路径，下层以模块和结构图展开。'),
    (3,'成果与机制证据','paired',(29,958,920,1461),'中心成果＋侧证据','非等宽分区，曲线、结构和机理图各有图旁解释。'),
    (4,'研究背景与地学分类','paired',(43,948,905,1426),'分类示意＋中间缺口','上方核心句，左分类，右侧已知技术与灾害事实共同提出缺口。'),
    (5,'地幔动力学模拟','different-topic',(43,948,905,1426),'模型证据拼图＋任务索引','优秀页与上半页预期成果主题不同，只提取优秀页结构。'),
    (6,'多尺度融合机制','paired',(53,972,899,1450),'总框架＋机制展开','通栏问题句，下方总流程、模块作用和侧边输出相互对应。'),
    (7,'几何先验引导优化','paired',(53,972,899,1450),'左流程＋右双层证据','虚线框限定子过程，括号表达约束，右侧分提取和验证。'),
    (8,'事件流感知与决策算法','layout-placeholder',(65,977,887,1437),'双技术模块＋共同落点','上半是两块占位图示意，下半两种技术按标题、图证、贡献组织。'),
    (9,'SNN感算一体架构','layout-placeholder',(65,977,887,1437),'对角图文交错','两图对角分布，说明填在互补位置，箭头标签定义处理单元。'),
    (10,'事件驱动视觉传感器','layout-placeholder',(65,977,887,1437),'并列机制对照','每半页为标题、结构图、解释、下推贡献，再用通栏结论收束。'),
    (11,'光电能源系统成果','single',(121,709,804,1091),'需求—系统—应用','单张编辑器截图，中部系统主图，两侧需求与成果，以紫色建立层级。'),
    (12,'项目考核指标','paired',(69,991,880,1447),'目标图示＋原生指标表','上方核心要求，中部图文目标，下方居中表格，深蓝表头与浅分隔。'),
    (13,'团队主要研究成果','different-topic',(69,991,880,1447),'主证据＋侧边应用','下半主题与上半考核指标不同，机制图为主区，侧栏放应用及照片。'),
    (14,'研究思路与技术路线','paired',(69,991,880,1447),'主科学问题＋双应用区','顶部战略关联句，左侧科学问题及机制，右侧应用按上下图文组织。'),
    (15,'拟解决的关键问题','paired',(69,991,880,1447),'需求与方法双区','左侧场景和问题，右侧两条机制路径，中间带字箭头明确关系。'),
    (16,'经费预算与项目说明','layout-placeholder',(65,977,887,1437),'两层多图＋资源窄栏','按背景、目标和设备资源分组，图片数量十张也有主次和图注。'),
    (17,'研究基础与工作条件','layout-placeholder',(65,977,887,1437),'组织与保障双区','两区再分管理、制度、资源层级，深色标题签和浅线框统一。'),
    (18,'研究计划与预期成果','layout-placeholder',(65,977,887,1437),'分阶段证据＋底部时间线','按年度组织图证，底部时间箭头与阶段对应，保持日期和成果一致。'),
    (19,'研究内容与创新总结','layout-placeholder',(65,977,887,1437),'三主题＋贯穿对比区','上层三项创新各有证据，下层与已有项目区别单独成区。'),
    (20,'多模态协同利用','paired',(52,984,898,1462),'阶段箭头＋三组证据','原版已有结构，改版统一图框、文字行高、边界和底部结论距离。'),
    (21,'成像物理补偿','paired-with-content-caution',(52,984,898,1462),'物理场景＋模型误差双层','场景在左，模型及误差在右，顶部任务句、下方定量目标分层；截图部分文本跨题。'),
    (22,'物理特征融合','paired',(52,984,898,1462),'主网络图＋三项机制说明','改版主要整理对齐与行距，左流程图、右编号说明、底部结果句。'),
    (23,'SAR背景与挑战','paired',(52,984,898,1462),'场景需求＋挑战矩阵','左场景与传统能力，右挑战及方法对应，红色意义条独立收束。'),
    (24,'未来工作计划','paired',(69,974,879,1426),'近期／远期双区','固定蓝色页眉，短长期标签，关键技术句用浅红底，底部红色总结条。'),
    (25,'拟开展的研究工作','paired',(69,974,879,1426),'三问题＋双证据簇','上层三关键问题，下面两大系统图组，层次比机械三等分更重要。'),
    (26,'代表性科研成果','paired',(69,974,879,1426),'技术—算法—性能＋成果带','上层三类证据，下层论文专利和双向关联图，关键数字就近强调。'),
    (27,'PEEM时空显微成像','paired',(57,973,893,1443),'方法窄栏＋中部原理＋右结果','紫色页眉，黄字短标签，左三方法，中部原理图，右时序结果。'),
    (28,'研究思路与子课题','paired',(57,973,893,1443),'问题—研究内容—预期成果','紫色问题标签，中央三行课题流程较宽，左右问题和目标较窄。'),
    (29,'国家重大需求','paired',(57,973,893,1443),'政策句＋三类支撑材料','上方需求与来源，下方人物、设备和期刊各有说明，紫色为同套模板主题。'),
    (30,'家禽疫苗研究背景','layout-placeholder',(35,980,915,1477),'背景要点＋证据双区','上方问题要点，左现状、右瓶颈与攻关内容，底部落点。'),
    (31,'研究目标与课题分解','layout-placeholder',(35,980,915,1477),'目标—技术—课题—落地','三张源图扩展为四个语义区，标签和梯形题签强调研究分解关系。'),
    (32,'国内外研究现状','layout-placeholder',(35,980,915,1477),'现状对照＋差距＋底部路径','左概念与证据，右国内外区别与短板，底部递进链说明阶段。'),
    (33,'试剂与疾病净化研究','layout-placeholder',(35,980,915,1477),'双证据＋中心循环关系','两张源图分两侧，中部循环箭头和圆形节点解释过程，底部全链条。'),
]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--catalog-markdown',type=Path)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    for index,title,kind,bounds,layout,observation in CASES:
        source=args.source_dir/f'参考图{index:02d}.jpg'
        with Image.open(source) as image:
            converted=tuple(round(value*image.size[axis%2]/(949 if axis%2==0 else 2048)) for axis,value in enumerate(bounds))
            crop=image.crop(converted)
            name=f'reference-{index:02d}-positive.png'
            crop.save(args.output_dir/name)
            records.append(dict(id=index,title=title,reference_type=kind,layout=layout,observation=observation,
                                source_filename=source.name,source_size=list(image.size),
                                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                positive_file=name,positive_bbox_original=list(converted)))
    (args.output_dir/'catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    if args.catalog_markdown:
        labels={'paired':'前后对照','layout-placeholder':'上方为布局占位示意',
                'single':'单页编辑器截图','different-topic':'前后主题不同',
                'paired-with-content-caution':'前后对照，科研文字需另核对'}
        lines=['# 33张科研PPT参考图索引','',
               '本索引分析用户提供的33张参考图。多数下方为优秀版本。部分上方只是图数量或位置占位示意，第11张为单页截图，第05、13张前后主题不同。截图的科研主题、机构和数值只用于辨认样例，实际课题应使用真实资料。','',
               '先按任务选择2—3个近似版式，打开相应优秀区域图。所有裁剪保留来源文件名、原始尺寸、SHA-256和裁剪边界，见`../assets/reference-atlas/catalog.json`。','',
               '| 编号 | 主题与优秀区域 | 类型 | 版式 |','| --- | --- | --- | --- |']
        for record in records:
            link=f"[{record['title']}](../assets/reference-atlas/{record['positive_file']})"
            lines.append(f"| {record['id']:02d} | {link} | {labels[record['reference_type']]} | {record['layout']} |")
        lines+=['','## 逐图观察','']
        for record in records:
            lines.append(f"- **{record['id']:02d} {record['title']}**。{record['observation']}")
        lines+=['','## 跨样例的共同规则','',
                '- 标题前固定小图形、贯穿内容宽度的细线和统一页眉建立全套身份。',
                '- 顶部核心句、主体图证、局部解释和归纳带形成读图层次。',
                '- 梯形题签、圆角短标签、淡色矩形、虚线范围、对话框和轻阴影表达归属。',
                '- 渐变透明大箭头用于跨区转换，细连接符说明局部依赖；带字箭头写操作名。',
                '- 主辅不必等宽，图量变化时通过语义分组适配；同级图组的外框与图注对齐。',
                '- 蓝白最常见，紫白在11、27—29中形成完整体系，暗红和少量暖黄用于重点。',
                '- 原生表格、时间线、编号、勾选和方框为指标与计划提供可读结构。','',
                '截图的小字、第三方标识、界面水印、浮动宣传语与跨题科研文字需按实际交付重新处理。具体制作参数见视觉系统和组件规范。','']
        args.catalog_markdown.parent.mkdir(parents=True,exist_ok=True)
        args.catalog_markdown.write_text('\n'.join(lines),encoding='utf-8')
    for start in range(0,len(records),6):
        subset=records[start:start+6]
        sheet=Image.new('RGB',(1440,3*435),'#E9EEF2')
        draw=ImageDraw.Draw(sheet)
        for offset,record in enumerate(subset):
            x=(offset%2)*720
            y=(offset//2)*435
            draw.text((x+14,y+10),f"REFERENCE {record['id']:02d} / POSITIVE",fill='#15456B')
            with Image.open(args.output_dir/record['positive_file']) as image:
                image.thumbnail((694,393))
                sheet.paste(image,(x+13,y+33))
        sheet.save(args.output_dir/f'contact-{start+1:02d}-{start+len(subset):02d}.jpg',quality=94)
    print(f'Prepared {len(records)} positive references and 6 contact sheets.')

if __name__=='__main__':
    main()
