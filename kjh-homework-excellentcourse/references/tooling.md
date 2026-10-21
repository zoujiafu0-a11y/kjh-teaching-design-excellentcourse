# 内置工具

工具由Codex运行。Python需要lxml，页面PNG可用pymupdf；从当前工作区依赖工具定位Python与库。Windows导出脚本需要Microsoft Word和COM能力，未具备时改用可用可靠渲染并报告方式，不能声称已实际打开。

先用`python scripts/select_template.py --output 新副本.docx --report 新报告.json`复制默认模板；当次指定模板时增加`--template 路径`。选择报告记录来源和哈希，不代表视觉通过。

`python scripts/fill_cells.py --input 副本.docx --output 新成品.docx --plan 计划.json --report 新报告.json`仅填写计划指定的单元格。计划由Codex检查当前文档后制作，为数组：`[{"table":0,"row":1,"cell":1,"expected":"原单元格全文","paragraphs":[{"text":"新内容","prototype":0}]}]`。坐标对应输入XML中表格、行与实体单元格，从0计；不是Word合并后的视觉列号。工具预先固定表格定位，重复文本由坐标和expected共同消歧，重复坐标拒绝。

段落复制指定单元格原有段落的段落属性，清除提示字灰色和斜体并设正文黑色宋体/TNR。默认无显式字号时采用五号；当次模板不是此字号须先确定实际有效样式，调整实现后测试或改用定点编辑。只支持普通段落单元格，不自动改嵌套表格、图片或控件丰富内容。

新嵌套表可作为paragraphs中的块：`{"widths":[5000,2800],"rows":[["评价标准","核对"],["可核对文字","填写内容"]]}`。宽度单位twip，各行列数一致，宽度必须小于内容单元格内宽；表尾自动加Word必需段落。新增表本身用固定列宽、灰色表头、黑色五号，固定外表不变。

若有精确授权删除的外部填写备注，在计划同名`.notes.json`写字符串数组。仅删除正文顶层完全匹配且唯一的段落。

输入、计划、输出、报告路径需互异；输出和报告须是新路径。expected不匹配、重复坐标、非法表宽、非矩形表、损坏ZIP均拒绝，不生成貌似成功的成品。工具不承担课程语义判断；成功报告仍标CREATED_NOT_REVIEWED。

`powershell -File scripts/export_word.ps1 -InputFile 成品.docx -OutputDir 新渲染目录`只读打开并导出PDF及哈希、页数。每次使用新目录。把PDF所有页转PNG，再实际查看；render.json中的NOT_RUN必须由真实查看记录补充，不能脚本预设PASS。旧导出失败目录保留，重试用新目录。
