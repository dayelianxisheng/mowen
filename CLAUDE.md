# CLAUDE.md

## SDF/URDF 修改规则

**任何对 SDF 或 URDF 文件的修改，必须通过 Python 脚本精准完成，禁止手动编辑 XML。**

原因：
- `model.sdf` 由 `gz sdf -p` 自动生成，结构复杂，手动编辑容易引入 XML 格式错误（缩进不一致、标签未闭合、属性格式错误等）
- 惯性参数必须用子元素格式（`<inertia><ixx>value</ixx></inertia>`）而非属性格式
- 多处重复结构（如4个轮子碰撞体）需保持一致

要求：
1. 脚本放在 `scripts/` 目录下，命名清晰（如 `fix_sdf_mass.py`, `fix_wheel_collision.py`）
2. 脚本使用 `xml.etree.ElementTree` 或精确的正则替换
3. 修改前先备份或通过 git 确认当前状态
4. 脚本执行后打印修改摘要（改了什么、改了多少处）
