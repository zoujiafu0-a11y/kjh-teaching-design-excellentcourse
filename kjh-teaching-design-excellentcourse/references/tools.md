# 辅助程序

这些脚本供Codex执行，用户不需要填写配置或运行命令。Python使用当前文档环境提供的运行时。脚本所需lxml、python-docx等在使用前检查；不可用时使用当前环境允许的等效方法，不假称已运行。

## 初始化

Codex把已理解的自然语言写为任务外暂存配置，再运行：

```text
python scripts/init_task.py --workspace <已获准工作区> --task <英文任务标识> --config <JSON路径>
```

配置支持：
- lesson_title、subject、grade、volume、textbook_version等课程字段。
- classroom：live或no_students，兼容有生、无生；默认no_students，明确要求有生时用live。
- ai_enabled：布尔值，默认true；用户明确不做时设为false。
- ai_style：开启时可为digital_human、scenario_animation、auto或用户要求的具体形式；默认auto，Codex根据教学内容作最后选择。关闭时不应填AI形式。
- template：指定模板绝对路径；缺省用包内模板。
- textbook_photos：教材照片绝对路径列表；缺省标记search_revised，由Codex实时检索。
- materials：其他材料路径列表；可含教参和旧稿。
- 其他用户参数保留在intake.json，不自动将身份写入正文。
- school_stage：小学、初中、高中或中学；school_stage_source为对应通知、教材或用户说明的位置。
- duration_purpose：明确为普通课堂、比赛展示或其他实际用途。
- duration_requirement：包含min_minutes、max_minutes、source；固定时长上下限相同，只有上限时下限为0。source必须指向真实通知或用户说明。
- target_minutes：范围内大于0的具体目标分钟数，不接受字符串占位符、布尔值或非有限数。
- timing_plan：由name和minutes组成的环节列表，合计等于target_minutes；媒体、思考及转换计入所属环节，不能重复计时。

上述字段由Codex从自然语言整理，缺项不猜填。初始化可以先保护资料，同时保存intake_review中的待补项与lesson_image_policy；这不代表已经可以定稿。参数变更后重新运行检查，不能依赖初始化时的旧结果。

```text
python scripts/check_intake.py --config <任务内work/intake.json>
```

该只读命令输出parameters_ready、timing_ready、合计及问题清单，intake_ready为false时退出码为1。来源文本存在不等于来源真实性通过，须实际核对原通知；参数检查通过不等于实际试讲通过。

程序只在workspace/output/<task>新建，已存在即停止以保护原任务。生成input/template.docx、按课程类型选定的案例、材料复制件、来源manifest.json、intake.json及progress.md。进度明确“待实际查看”，不会因复制成功写成已验收。

## Word机器检查

```text
python scripts/audit_docx.py --task <任务目录> --docx <成稿路径> --template <实际模板路径>
```

结果写入work/machine_audit.json。发现结构差异不自动修复或豁免；根据用户明确授权区分必要变更与缺陷。自定义模板的变化需对应实际要求记录。语言扫描仅给复核候选，不能代替上下文阅读。

审查会重新计算学段和时长参数、环节合计，并检查work/image_sources.md是否存在；记录缺失或时间不合格时machine_checks_pass为false。图片来源文件存在只代表有记录，程序不能判定图片就是教材原图；必须逐图对照原页与最终Word，包括页眉页脚、浮动对象以及自绘形状。零图也需来源记录说明教学上无需图。

`delivery_defaults_review`补充检测教学时间括注/说明、教材页码定位语、Unicode伪上下标、西文双引号、中文引号数量、教科书三字段缺失/多余元信息，以及默认文件名，并统计原生上下标run数。它独立于结构检查结果：`machine_checks_pass=true`不能代表这些候选已处理。逐项修复或记录用户当次明确例外；扫描时间单位时保留学科原文与例题数据，代码/英寸中的双引号也需按语义判断。原生公式结构、裸写却应该设为上下标的字符，以及引号嵌套关系还须人工核验，不以零候选冒充全部通过。

## 本机Word导出

```text
powershell -File scripts/export_word.ps1 -TaskRoot <任务目录> -InputDocx <任务内DOCX> -OutputPdf <任务内PDF>
```

必须在有Word的Windows环境实际运行。导出不会改写DOCX；每次换一个render_vN目录。脚本限制输入和输出在任务内，只读打开并导出自己的文档。随后由Codex使用可用PDF工具渲染逐页PNG并全部查看。若沙箱阻止COM，按工具权限机制申请该只读导出操作，不自行绕过。

## 人工智能教育配置与兼容

course_type支持subject、ai_education，省略时保留subject。ai_education须提供非空`ai_case_ids`列表，范围ai_01至ai_12；由Codex先作教学判断后填入，脚本不按年级自动猜。初始化只复制选中AI案例全部原图并校验SHA256，写case_policy和case_selection；不夹带学科八图。非法ID、路径穿越和类型错误在创建目录前拒绝。

`check_intake.py`同时返回course_review、course_ready和intake_ready；timing_ready仅表示原时长检查，intake_ready要求时长和分流均通过，命令以intake_ready决定退出码。`audit_docx.py`重新验证课程分流并追加AI教育人工审查项目。原配置缺省course_type继续subject。缺时长可以初始化保护材料，不能通过定稿验收。
