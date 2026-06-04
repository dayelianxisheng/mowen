#!/usr/bin/env python3
"""
雷达引导目标检测节点 (CRF-Net Step 2)

架构:
  DetectionConfig  ─→  ObjectDetector (纯模型, 无ROS2依赖)
                              │
  RadarGuidedDetector (ROS2 Node) ─→ /detections, /detection_image
"""

import sys
if '--test' in sys.argv:
    from radar_detector import test
    test()
    sys.exit(0)

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import cv2
import torch
import torchvision
from torchvision.transforms import functional as TVF
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


# ============================================================
# 1. 配置 (所有超参数集中管理)
# ============================================================

class Backbone(str, Enum):
    RESNET50 = "resnet50"
    MOBILENET = "mobilenet"

@dataclass
class DetectionConfig:
    """检测器配置"""
    # 模型
    backbone: Backbone = Backbone.RESNET50
    score_threshold: float = 0.3
    nms_threshold: float = 0.5
    max_detections: int = 100

    # 预处理
    input_size: Tuple[int, int] = (640, 480)
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406)
    std:  Tuple[float, float, float] = (0.229, 0.224, 0.225)

    # 雷达
    radar_pixel_radius: int = 100       # 雷达关联的像素搜索半径
    radar_min_distance: float = 0.5     # 最小有效雷达距离 (m)
    radar_max_distance: float = 35.0    # 最大有效雷达距离 (m)


# ============================================================
# 2. 类别定义 (COCO 2017)
# ============================================================

COCO_CLASSES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
    'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant',
    'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse',
    'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis',
    'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass',
    'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
    'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
    'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush',
]

@dataclass
class DetectionResult:
    """结构化检测结果"""
    boxes: np.ndarray       # [N, 4]  (x1, y1, x2, y2) 像素坐标
    scores: np.ndarray      # [N]     置信度 [0, 1]
    labels: np.ndarray      # [N]     COCO 类别索引
    radar_distances: np.ndarray  # [N]  雷达距离 (m), -1 表示无关联

    def __len__(self) -> int:
        return len(self.boxes)

    def __getitem__(self, idx: int) -> dict:
        return {
            'box': self.boxes[idx],
            'score': self.scores[idx],
            'label': int(self.labels[idx]),
            'class_name': COCO_CLASSES[int(self.labels[idx])],
            'radar_distance': self.radar_distances[idx],
        }

    @property
    def is_empty(self) -> bool:
        return len(self.boxes) == 0


# ============================================================
# 3. 模型定义 (纯 PyTorch, 无 ROS2 依赖)
# ============================================================

class ObjectDetector:
    """
    目标检测器 (Faster R-CNN + ResNet-50 FPN, COCO 预训练)

    用法:
      detector = ObjectDetector(DetectionConfig())
      result = detector.detect(image_np)      # np.ndarray → DetectionResult
      result = detector.detect_batch(images)  # List[np.ndarray] → List[DetectionResult]
    """

    def __init__(self, config: DetectionConfig = DetectionConfig()):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 加载预训练模型
        weights = torchvision.models.detection.FasterRCNN_ResNet50_FPN_Weights.COCO_V1
        self._model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
            weights=weights,
            box_score_thresh=config.score_threshold,
            box_nms_thresh=config.nms_threshold,
            box_detections_per_img=config.max_detections,
        )
        self._model.to(self.device)
        self._model.eval()

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """预处理: np.ndarray (H,W,3) → Tensor (1,3,H,W) on device"""
        tensor = TVF.to_tensor(image)           # (H,W,3) → (3,H,W), [0,1]
        return tensor.unsqueeze(0).to(self.device)

    def postprocess(self, predictions: List[dict]) -> DetectionResult:
        """后处理: torch.Tensor → DetectionResult"""
        pred = predictions[0]
        boxes = pred['boxes'].detach().cpu().numpy()
        scores = pred['scores'].detach().cpu().numpy()
        labels = pred['labels'].detach().cpu().numpy()

        if len(boxes) == 0:
            return DetectionResult(
                boxes=np.empty((0, 4)), scores=np.empty(0),
                labels=np.empty(0), radar_distances=np.empty(0))

        return DetectionResult(
            boxes=boxes, scores=scores, labels=labels,
            radar_distances=np.full(len(boxes), -1.0))

    def detect(self, image: np.ndarray) -> DetectionResult:
        """单张图像检测"""
        tensor = self.preprocess(image)
        with torch.no_grad():
            predictions = self._model(tensor)
        return self.postprocess(predictions)

    def detect_batch(self, images: List[np.ndarray]) -> List[DetectionResult]:
        """批量检测"""
        tensors = [self.preprocess(img).squeeze(0) for img in images]
        batch = torch.stack(tensors).to(self.device)
        with torch.no_grad():
            predictions = self._model(batch)
        return [self.postprocess([p]) for p in predictions]


# ============================================================
# 4. 雷达关联 (将雷达目标匹配到检测框)
# ============================================================

def associate_radar(
    result: DetectionResult,
    radar_targets: List[dict],
    radius: int = 100
) -> DetectionResult:
    """将雷达距离关联到检测框"""
    if not radar_targets:
        return result

    distances = np.full(len(result), -1.0)
    for i in range(len(result)):
        box = result.boxes[i]
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2

        best_dist = float('inf')
        for t in radar_targets:
            tx = t.get('pixel_x', -999)
            ty = t.get('pixel_y', -999)
            d = np.sqrt((tx - cx) ** 2 + (ty - cy) ** 2)
            if d < radius:
                best_dist = min(best_dist, t.get('range', float('inf')))

        if best_dist < float('inf'):
            distances[i] = best_dist

    result.radar_distances = distances
    return result


# ============================================================
# 5. ROS2 节点 (串联 ObjectDetector + ROS2 话题)
# ============================================================

class RadarGuidedDetector(Node):
    """ROS2 节点: 订阅图像 + 雷达, 发布检测结果"""

    def __init__(self, config: DetectionConfig = None):
        super().__init__('radar_detector')
        self.bridge = CvBridge()
        self.config = config or DetectionConfig()

        # 模型
        self.get_logger().info(f"Loading {self.config.backbone.value} on {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}...")
        self.detector = ObjectDetector(self.config)
        self.get_logger().info("Model loaded")

        # 状态
        self._camera_matrix: Optional[np.ndarray] = None
        self._latest_raw: Optional[Image] = None

        # ROS2 接口
        self.create_subscription(Image, '/rgb_camera/image_raw', self._on_raw_image, 10)
        self.create_subscription(CameraInfo, '/rgb_camera/camera_info', self._on_camera_info, 10)
        self.create_subscription(Image, '/camera/image_radar', self._on_radar_image, 10)

        self._det_pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self._vis_pub = self.create_publisher(Image, '/detection_image', 10)
        self.get_logger().info("RadarGuidedDetector ready")

    # ---- ROS2 回调 ----
    def _on_camera_info(self, msg: CameraInfo):
        if self._camera_matrix is None:
            self._camera_matrix = np.array(msg.k).reshape(3, 3)

    def _on_raw_image(self, msg: Image):
        self._latest_raw = msg

    def _on_radar_image(self, msg: Image):
        """雷达增强图到达 → 触发检测"""
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception:
            cv_img = self.bridge.imgmsg_to_cv2(msg)

        result = self.detector.detect(cv_img)
        self._publish(result, cv_img, msg.header)

    # ---- 发布 ----
    def _publish(self, result: DetectionResult, image: np.ndarray, header):
        det_array = Detection2DArray(header=header)
        vis = image.copy()
        h, w = image.shape[:2]

        if result.is_empty:
            cv2.putText(vis, 'No objects detected', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            for i in range(len(result)):
                item = result[i]
                x1, y1 = max(0, int(item['box'][0])), max(0, int(item['box'][1]))
                x2, y2 = min(w, int(item['box'][2])), min(h, int(item['box'][3]))

                # Detection2D 消息
                det = Detection2D(header=header)
                bbox = BoundingBox2D()
                bbox.center.position.x = float((x1 + x2) / 2.0 / w)
                bbox.center.position.y = float((y1 + y2) / 2.0 / h)
                bbox.size_x = float((x2 - x1) / w)
                bbox.size_y = float((y2 - y1) / h)
                det.bbox = bbox
                hyp = ObjectHypothesisWithPose()
                hyp.hypothesis.class_id = item['class_name']
                hyp.hypothesis.score = float(item['score'])
                det.results.append(hyp)
                det_array.detections.append(det)

                # 可视化
                dist = item['radar_distance']
                color = (0, 255, 0) if dist > 0 else (0, 200, 200)
                label = f"{item['class_name']} {item['score']:.2f}"
                if dist > 0:
                    label += f" {dist:.1f}m"
                cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
                cv2.putText(vis, label, (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)

        self._det_pub.publish(det_array)
        self._vis_pub.publish(self.bridge.cv2_to_imgmsg(vis, 'bgr8', header))

        if det_array.detections:
            self.get_logger().info(
                f"Detected {len(det_array.detections)} objects",
                throttle_duration_sec=1.0)


# ============================================================
# 6. 测试入口 (--test)
# ============================================================

def test():
    """独立测试: 不依赖 ROS2, 验证模型推理"""
    import numpy as np
    import cv2

    print("=" * 60)
    print("ObjectDetector 独立测试")
    print("=" * 60)

    config = DetectionConfig(score_threshold=0.3)
    detector = ObjectDetector(config)

    # 模拟图像
    w, h = 640, 480
    img = np.ones((h, w, 3), dtype=np.uint8) * 120
    cv2.rectangle(img, (0, 300), (w, h), (60, 60, 60), -1)
    cv2.putText(img, "Test image", (w//2-40, h//2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    print(f"\n输入: {w}x{h}, 设备: {detector.device}")
    result = detector.detect(img)
    print(f"检测到 {len(result)} 个物体")

    if not result.is_empty:
        for i in range(len(result)):
            r = result[i]
            x1, y1, x2, y2 = r['box'].astype(int)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            print(f"  [{i}] {r['class_name']:10s} score={r['score']:.3f} "
                  f"box=({x1},{y1})-({x2},{y2}) size={(x2-x1)}x{(y2-y1)}")
    else:
        cv2.putText(img, "No objects (simulated image, expected)",
                    (50, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

    cv2.imshow("Detector Test", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("=" * 60)


def main():
    rclpy.init()
    node = RadarGuidedDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
