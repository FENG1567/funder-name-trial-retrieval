# 复现包说明

本目录为论文 **Similar Results-Posting Proportions Despite Low Trial Retrieval by Funder Name: A Pancreas-Focused Portfolio and Cross-Funder Analysis** 的分析代码与整理数据。

代码从 `data/curated` 与 `data/aggregate` 的输入重算文中的覆盖度与报告比例，并重绘两张图。

## 运行

Python 3.10 以上，在本目录执行：

```text
python reproduce.py --no-figures
python -m unittest discover -s tests -v
```

重绘图片需在独立虚拟环境安装 `requirements.txt`，执行 `python reproduce.py --no-figures` 后，再执行 `python plot_figures.py --font-path <Arial Bold字体文件路径>`。结果写入 `results`。

图内文字统一为 Arial Bold，子图标号为大写18磅。请使用本机已获许可的 Arial Bold TrueType 字体，例如 Windows 的 `C:/Windows/Fonts/arialbd.ttf`；本包不分发字体文件。若 Matplotlib 能找到已安装的 Arial Bold，可以省略 `--font-path`。缺少字体时脚本明确报错，不会静默更换字体。

## 版本与仓库

拟发布版本：`v1.0.0`  
目标仓库：https://github.com/FENG1567/funder-name-trial-retrieval

## 目录

- `data/curated`：试验、来源行、试验家族与注册链接的整理记录。
- `data/aggregate`：比较所用的计数。
- `expected`：用于对照的稿件表格。
- `reproduce.py`、`plot_figures.py`、`tests`：计算、绘图与检查。
- `docs`：方法、字段说明、数据清单与再使用条款。
- `SHA256SUMS`：打包文件的 SHA-256 校验值。

来源抓取日期为 2026 年 10 月，见方法部分。

## 许可

`LICENSE` 仅适用于项目代码。第三方记录仍受其来源条款约束，见 `docs/data_reuse.md`。
