# 辅助程序

这些脚本供Codex执行，用户不需要填写配置或运行命令。Python使用当前文档环境提供的运行时。脚本所需lxml、python-docx等在使用前检查；不可用时使用当前环境允许的等效方法，不假称已运行。

## 初始化

Codex把已理解的自然语言写为任务外暂存配置，再运行：

```text
python scripts/init_task.py --workspace <已获准工作区> --task <英文任务标识> --config <JSON路径>
```

配置支持：
- lesson_title、subject、grade、volume、textbook_version等课程字段。
- classroom：live或no_students，兼容有生、无生；默认live。
- ai_enabled：布尔值，默认true；用户明确不做时设为false。
- ai_style：开启时可为digital_human、scenario_animation、auto或用户要求的具体形式；默认auto，Codex根据教学内容作最后选择。关闭时不应填AI形式。
- template：指定模板绝对路径；缺省用包内模板。
- textbook_photos：教材照片绝对路径列表；缺省标记search_revised，由Codex实时检索。
- materials：其他材料路径列表；可含教参和旧稿。
- 其他用户参数保留在intake.json，不自动将身份写入正文。

程序只在workspace/output/<task>新建，已存在即停止以保护原任务。生成input/template.docx、八张案例、材料复制件、来源manifest.json、intake.json及progress.md。进度明确“待实际查看”，不会因复制成功写成已验收。

## Word机器检查

```text
python scripts/audit_docx.py --task <任务目录> --docx <成稿路径> --template <实际模板路径>
```

结果写入work/machine_audit.json。发现结构差异不自动修复或豁免；根据用户明确授权区分必要变更与缺陷。自定义模板的变化需对应实际要求记录。语言扫描仅给复核候选，不能代替上下文阅读。

`delivery_defaults_review`补充检测教学时间括注/说明、Unicode伪上下标、西文双引号、中文引号数量、教科书三字段缺失/多余元信息，以及默认文件名，并统计原生上下标run数。它独立于结构检查结果：`machine_checks_pass=true`不能代表这些候选已处理。逐项修复或记录用户当次明确例外；扫描时间单位时保留学科原文与例题数据，代码/英寸中的双引号也需按语义判断。原生公式结构、裸写却应该设为上下标的字符，以及引号嵌套关系还须人工核验，不以零候选冒充全部通过。

## 本机Word导出

```text
powershell -File scripts/export_word.ps1 -TaskRoot <任务目录> -InputDocx <任务内DOCX> -OutputPdf <任务内PDF>
```

必须在有Word的Windows环境实际运行。导出不会改写DOCX；每次换一个render_vN目录。脚本限制输入和输出在任务内，只读打开并导出自己的文档。随后由Codex使用可用PDF工具渲染逐页PNG并全部查看。若沙箱阻止COM，按工具权限机制申请该只读导出操作，不自行绕过。
