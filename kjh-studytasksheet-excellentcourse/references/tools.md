# 工具参数

使用当前环境提供的Python（需要lxml），PowerShell脚本需要Windows与本机Office。下列参数由Codex整理，不让用户编写配置。所有报告路径须是新路径，禁止覆盖源文件。

```text
python scripts/package_tools.py inspect 输入文件 --report work/inventory.json
python scripts/package_tools.py patch 输入文件 输出副本 --changes work/changes.json --report work/patch.json
python scripts/package_tools.py compare 输入文件 输出副本 --report work/compare.json
```

changes.json是数组，每项含old和new完整段落，可选part和index定位。必须唯一匹配；重复、无变化、复杂域或链接、已有输出均拒绝。先inspect再制定修改，禁止按旧课索引盲替。此工具保护非文字结构，不负责混合格式语义或视觉适配。compare仅适用于文字替换的严格保真检查，新增图表或动画须另按授权对象比对。

```text
powershell -File scripts/export_word.ps1 -InputFile 成稿.docx -OutputDir work/render_r1
```

导出PDF后使用可用PDF渲染器生成每页PNG并实际查看。脚本返回实际页数，visualReview仍为NOT_RUN，不能直接写全项通过。
