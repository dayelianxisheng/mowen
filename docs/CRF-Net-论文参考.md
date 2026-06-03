# CRF-Net 论文参考

## 论文

**A Deep Learning-based Radar and Camera Sensor Fusion Architecture for Object Detection**

- **作者**: Felix Nobis, Maximilian Geisslinger, Markus Weber, Johannes Betz, Markus Lienkamp (慕尼黑工业大学)
- **发表**: 2019 Sensor Data Fusion (SDF) Conference, IEEE
- **arXiv**: [2005.07431](https://arxiv.org/abs/2005.07431)
- **DOI**: [10.1109/SDF.2019.8916629](https://ieeexplore.ieee.org/abstract/document/8916629/)
- **代码**: [github.com/TUMFTM/CameraRadarFusionNet](https://github.com/TUMFTM/CameraRadarFusionNet)

## 核心思想

基于 RetinaNet (VGG + FPN) 的多级融合架构，将毫米波雷达点投影到图像平面，在网络的多个深度级别将雷达通道与视觉特征拼接融合。

```
相机图像 → VGG Backbone → FPN → 检测头
                                   ↑
雷达点 → 投影到图像平面 → 多级拼接融合
```

## 关键技术

1. **雷达预处理**: 雷达点投影到图像垂直平面，高度扩展至 3m（补偿雷达无俯仰角信息），累积 13 帧历史数据对抗雷达稀疏性
2. **BlackIn 训练策略**: 训练时以概率 0.2 随机丢弃相机输入，迫使网络独立从雷达提取特征
3. **多级融合**: 网络自动学习最优融合层级

## nuScenes 实验结果

| 配置 | mAP 提升 |
|------|---------|
| 原始雷达数据 + BlackIn | +0.35 pp |
| 真值过滤雷达 (去噪) | **+12.96 pp** |
| 无雷达元数据 (距离/RCS) | 显著下降 |

> 关键瓶颈: 雷达噪声/杂波是融合质量的主要限制因素

## 本项目实现

mowen_radar_fusion 在 Gazebo 仿真中复现 CRF-Net 的传感器数据级融合流程:
- 毫米波雷达 (10束, ±40°, 35m) → 投影到相机图像平面
- 雷达距离/VpR 编码为投影线颜色
- 雷达增强图像 → 检测网络 (Faster R-CNN / YOLO)
- 下一步: 训练轻量检测网络 + 恶劣条件测试
