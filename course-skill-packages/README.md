> 2026-09-28：教学设计技能包已更新为 v1.1.0，与仓库源码同步；其他六个ZIP保持原样。请以本目录教学设计ZIP获取最新版，历史Release不代表本次版本。

# 精品课课程制作技能包

本目录提供7个可单独使用的Codex技能完整包。每个ZIP内保留技能文件夹、SKILL.md、界面配置、参考规则、脚本及该技能自带的模板和案例。归档日期：2026-09-27；逐字稿技能包于2026-09-28更新。

## 技能与调用

|规范调用|默认成果|下载|
|---|---|---|
|`$kjh-teaching-design-excellentcourse`|教学设计.docx|[kjh-teaching-design-excellentcourse.zip](kjh-teaching-design-excellentcourse.zip)|
|`$kjh-preclassexploration-excellentcourse`|课前探秘人物.docx|[kjh-preclassexploration-excellentcourse.zip](kjh-preclassexploration-excellentcourse.zip)|
|`$kjh-inclasspractice-excellentcourse`|课时同步练习.docx|[kjh-inclasspractice-excellentcourse.zip](kjh-inclasspractice-excellentcourse.zip)|
|`$kjh-studytasksheet-excellentcourse`|学习任务单.docx|[kjh-studytasksheet-excellentcourse.zip](kjh-studytasksheet-excellentcourse.zip)|
|`$kjh-ppt-excellentcourse`|课件.pptx|[kjh-ppt-excellentcourse.zip](kjh-ppt-excellentcourse.zip)|
|`$kjh-transcripts-excellentcourse`|逐字稿.docx|[kjh-transcripts-excellentcourse.zip](kjh-transcripts-excellentcourse.zip)|
|`$kjh-homework-excellentcourse`|作业练习.docx|[kjh-homework-excellentcourse.zip](kjh-homework-excellentcourse.zip)|

## 逐字稿技能包更新

本次逐字稿包默认按无生课堂编写，只写教师口播与真实PPT播放提示；用户明确要求有生课堂时才加入学生互动。制作Word时逐项对照用户指定的参考稿字体、字号、标题样式和段落格式。包内新增`references/tutorial.md`，提供可直接用于Codex的执行指令与验收条件。

## 安装

下载所需ZIP并解压，将其中完整技能文件夹放到目标项目的`.agents/skills/`。保留原文件夹名称和内部目录，不要只复制SKILL.md。例如：

```text
你的项目/
  .agents/
    skills/
      kjh-homework-excellentcourse/
        SKILL.md
        agents/
        assets/
        references/
        scripts/
```

在该项目中调用对应技能，并提供课程材料。使用已安装同名技能时，应先保留旧版，再更新完整文件夹。

## 使用示例

```text
使用 $kjh-homework-excellentcourse。
依据我提供的定稿教学设计制作《作业练习.docx》。
没有另给模板时使用内置模板副本，保留固定格式。
教材出版年月没有可靠信息时留空，学生使用纸笔，不依赖个人设备或操作AI。
只制作这份作业练习，不修改主教案。
请完成独立答案或评价审核、排版、逐页检查和返修后交付。
```

课后作业、课时同步练习和学习任务单各有分工，按目标文件选择，单文件请求不会默认重做整套课程。课件技能保护当次固定模板，尤其封面，并要求原生动画实际放映检查。PPT包中的氮循环课件用于学习内容设计，不代替当次固定模板。

## 环境与验证

需要具备本地文件操作、图像查看与文档处理能力的Codex环境。Python脚本按各包工具说明使用lxml等依赖；Windows Office辅助程序需要已安装的Word或PowerPoint。其他环境应采用实际可用的可靠渲染方式，不能在未查看页面或放映时声称验收通过。

这些技能不自带账号、密钥或付费媒体服务。实际可生成的媒体取决于当前工具及用户要求。未知教材信息不编造，未来课程仍须逐课核验。

所有ZIP均核对包完整性与解压后文件哈希，并通过技能结构校验。该发布检查不代替新课程的教学审核。校验值见SHA256SUMS.txt。

模板和案例随技能保留，未新增开源授权；可下载不代表对第三方素材授予额外使用许可。教学设计技能目录与本目录ZIP同步更新，历史发行版保留。
