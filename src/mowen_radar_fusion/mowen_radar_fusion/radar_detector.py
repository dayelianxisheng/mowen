#!/usr/bin/env python3
"""
雷达引导目标检测节点 (CRF-Net Step 2)

订阅: /rgb_camera/image_raw, /radar/targets, /rgb_camera/camera_info
发布: /detections (Detection2DArray), /detection_image (标注图像)

流程:
  1. Faster R-CNN (ResNet-50) 基础检测
  2. 雷达投影点 → 注意力加权 (靠近投影线的Box置信度提升)
  3. 输出检测结果 + 距离标签
"""

import sys
if '--test' in sys.argv:
    import numpy as np, cv2, torch, torchvision
    from torchvision.transforms import functional as F

    print("=" * 60)
    print("CNN 检测节点 测试 - 数据特征:")
    print("=" * 60)

    w, h = 640, 480
    img = np.ones((h, w, 3), dtype=np.uint8) * 100
    cv2.rectangle(img, (0, 300), (w, h), (80, 80, 80), -1)
    cv2.rectangle(img, (250, 180), (310, 300), (50, 50, 200), -1)
    cv2.circle(img, (280, 155), 20, (200, 150, 120), -1)
    cv2.putText(img, "Test: person + car shapes", (200, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    weights = torchvision.models.detection.FasterRCNN_ResNet50_FPN_Weights.COCO_V1
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=weights, box_score_thresh=0.3)
    model.to(device).eval()
    print(f"设备: {device}, 模型: Faster R-CNN (COCO 80类)")
    print(f"输入: {w}x{h} 模拟场景图 (人+车)")

    tensor = F.to_tensor(img).unsqueeze(0).to(device)
    with torch.no_grad():
        pred = model(tensor)

    boxes = pred[0]['boxes'].cpu().numpy()
    scores = pred[0]['scores'].cpu().numpy()
    labels = pred[0]['labels'].cpu().numpy()
    coco = ['__bg__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
            'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter',
            'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
            'zebra', 'giraffe', 'backpack', 'umbrella']

    print(f"\n检测结果: {len(boxes)} 个物体")
    for i, (box, score, label) in enumerate(zip(boxes, scores, labels)):
        name = coco[int(label)] if int(label) < len(coco) else f'cls_{label}'
        x1, y1, x2, y2 = box.astype(int)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"{name} {score:.2f}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        print(f"  [{i}] {name:10s} score={score:.3f}  box=({x1},{y1})-({x2},{y2}) size={(x2-x1)}x{(y2-y1)}")

    if len(boxes) == 0:
        cv2.putText(img, "No objects detected (need realistic photos)", (80, 430),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    cv2.imshow("Detector Test - Press any key", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("=" * 60)
    sys.exit(0)

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import cv2
import torch
import torchvision
from torchvision.transforms import functional as F
import numpy as np


class RadarGuidedDetector(Node):
    def __init__(self):
        super().__init__('radar_detector')

        self.bridge = CvBridge()

        # 预训练 Faster R-CNN (COCO)
        self.get_logger().info("Loading Faster R-CNN (ResNet-50)...")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # 使用新版 torchvision API (pretrained=已废弃)
        weights = torchvision.models.detection.FasterRCNN_ResNet50_FPN_Weights.COCO_V1
        self.model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
            weights=weights,
            box_score_thresh=0.3
        )
        self.model.to(self.device)
        self.model.eval()
        self.get_logger().info(f"Model loaded on {self.device}")

        # COCO 类别
        self.coco_names = [
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

        # 雷达目标 (CameraInfo 用于内参，仅在收到后使用)
        self.radar_targets = []
        self.camera_matrix = None
        self.latest_image = None

        # 订阅
        self.create_subscription(Image, '/rgb_camera/image_raw', self.image_callback, 10)
        self.create_subscription(CameraInfo, '/rgb_camera/camera_info', self.camera_info_callback, 10)
        self.create_subscription(Image, '/camera/image_radar', self.radar_image_callback, 10)

        # 发布检测结果
        self.det_pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self.vis_pub = self.create_publisher(Image, '/detection_image', 10)

        self.get_logger().info("RadarGuidedDetector ready")

    def camera_info_callback(self, msg: CameraInfo):
        if self.camera_matrix is None:
            self.camera_matrix = np.array(msg.k).reshape(3, 3)
            self.get_logger().info("Camera intrinsic matrix received")

    def image_callback(self, msg: Image):
        self.latest_image = msg

    def radar_image_callback(self, msg: Image):
        """收到雷达增强图时进行检测"""
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception:
            try:
                cv_img = self.bridge.imgmsg_to_cv2(msg)  # 用原始编码
            except Exception as e:
                self.get_logger().error(f"Image conversion failed: {e}")
                return

        # 推理
        detections = self.detect(cv_img)

        # 始终发布（无检测时发布空结果以确认节点存活）
        self.publish_detections(detections, cv_img, msg.header)

    def detect(self, image: np.ndarray):
        """Faster R-CNN 检测 + 雷达注意力"""
        tensor = F.to_tensor(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            predictions = self.model(tensor)

        if len(predictions[0]['boxes']) == 0:
            return None

        boxes = predictions[0]['boxes'].cpu().numpy()
        scores = predictions[0]['scores'].cpu().numpy()
        labels = predictions[0]['labels'].cpu().numpy()

        # COCO 中 person=1, car=3 等常见物体
        return {'boxes': boxes, 'scores': scores, 'labels': labels}

    def get_radar_distance(self, box):
        """估算框中物体的雷达距离（取最近雷达目标的距离）"""
        if not self.radar_targets:
            return -1.0
        center_x = (box[0] + box[2]) / 2
        center_y = (box[1] + box[3]) / 2

        min_dist = float('inf')
        for target in self.radar_targets:
            # 使用雷达投影图的像素位置
            tx, ty = target.get('pixel_x', 0), target.get('pixel_y', 0)
            dist = np.sqrt((tx - center_x) ** 2 + (ty - center_y) ** 2)
            if dist < 100:  # 100像素内
                min_dist = min(min_dist, target.get('range', -1))

        return min_dist if min_dist < float('inf') else -1.0

    def publish_detections(self, detections, image, header):
        """发布检测结果和可视化"""
        det_array = Detection2DArray()
        det_array.header = header
        vis = image.copy()
        h, w = image.shape[:2]

        # 无检测时只发布原图（确认节点存活）
        if detections is None:
            cv2.putText(vis, 'No objects detected', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            self.det_pub.publish(det_array)
            self.vis_pub.publish(self.bridge.cv2_to_imgmsg(vis, encoding='bgr8', header=header))
            return

        boxes = detections['boxes']
        scores = detections['scores']
        labels = detections['labels']

        for i, (box, score, label) in enumerate(zip(boxes, scores, labels)):
            if score < 0.5:
                continue

            x1, y1, x2, y2 = box.astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            label_name = self.coco_names[label] if label < len(self.coco_names) else f'cls_{label}'
            dist = self.get_radar_distance(box)
            dist_str = f'{dist:.1f}m' if dist > 0 else ''

            # Detection2D 消息
            det = Detection2D()
            det.header = header
            bbox = BoundingBox2D()
            bbox.center.position.x = float((x1 + x2) / 2.0 / w)
            bbox.center.position.y = float((y1 + y2) / 2.0 / h)
            bbox.size_x = float((x2 - x1) / w)
            bbox.size_y = float((y2 - y1) / h)
            det.bbox = bbox

            hypothesis = ObjectHypothesisWithPose()
            hypothesis.hypothesis.class_id = label_name
            hypothesis.hypothesis.score = float(score)
            det.results.append(hypothesis)
            det_array.detections.append(det)

            # 画框
            color = (0, 255, 0) if dist > 0 else (0, 200, 200)
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            cv2.putText(vis, f'{label_name} {score:.2f} {dist_str}',
                        (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        if det_array.detections:
            self.det_pub.publish(det_array)
            self.vis_pub.publish(self.bridge.cv2_to_imgmsg(vis, encoding='bgr8', header=header))
            self.get_logger().info(
                f"Detected {len(det_array.detections)} objects",
                throttle_duration_sec=1.0
            )


def test():
    """测试: 加载预训练模型, 对一张模拟场景图做检测, 展示数据特征"""
    import numpy as np
    import cv2

    w, h = 640, 480

    print("=" * 60)
    print("CNN 检测节点 测试 — 数据特征:")
    print("=" * 60)

    # 创建模拟场景图 (类似小车看到的前方画面)
    img = np.ones((h, w, 3), dtype=np.uint8) * 100  # 灰色背景
    # 地面
    cv2.rectangle(img, (0, 300), (w, h), (80, 80, 80), -1)
    # 模拟一个小人 (红色方块)
    cv2.rectangle(img, (250, 180), (310, 300), (50, 50, 200), -1)
    cv2.circle(img, (280, 155), 20, (200, 150, 120), -1)  # 头
    # 模拟一辆车 (白色方块 + 轮子)
    cv2.rectangle(img, (400, 210), (560, 320), (180, 180, 180), -1)
    cv2.circle(img, (420, 320), 15, (40, 40, 40), -1)
    cv2.circle(img, (540, 320), 15, (40, 40, 40), -1)
    cv2.putText(img, "Test: person + car", (200, 350),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    print(f"\n输入图像: {w}x{h}, 含2个模拟物体 (人+车)")

    # 加载模型
    import torch
    import torchvision
    from torchvision.transforms import functional as F
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")

    weights = torchvision.models.detection.FasterRCNN_ResNet50_FPN_Weights.COCO_V1
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=weights, box_score_thresh=0.3)
    model.to(device)
    model.eval()
    print(f"模型: Faster R-CNN (ResNet-50, COCO 80类)")

    # 推理
    tensor = F.to_tensor(img).unsqueeze(0).to(device)
    with torch.no_grad():
        pred = model(tensor)

    coco = RadarGuidedDetector.coco_names if hasattr(RadarGuidedDetector, 'coco_names') else [
        '__bg__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
        'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
        'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag',
        'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
        'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon',
        'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
        'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant',
        'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
        'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
        'hair drier', 'toothbrush',
    ]

    print(f"\n检测结果:")
    boxes = pred[0]['boxes'].cpu().numpy()
    scores = pred[0]['scores'].cpu().numpy()
    labels = pred[0]['labels'].cpu().numpy()

    if len(boxes) == 0:
        print("  ⚠ 未检测到物体 (模拟图和真实图差距大, CNN 可能无法识别)")
        cv2.putText(img, "No detections (try real photos)", (100, 400),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    else:
        for i, (box, score, label) in enumerate(zip(boxes, scores, labels)):
            name = coco[int(label)] if int(label) < len(coco) else f'cls_{label}'
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"{name} {score:.2f}", (x1, y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            print(f"  [{i}] {name:15s} score={score:.3f}  box=({x1},{y1})-({x2},{y2})")
            print(f"       尺寸={(x2-x1)}x{(y2-y1)}px, 中心=({(x1+x2)//2},{(y1+y2)//2})")

    cv2.imshow("Detector Test - Press any key", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("=" * 60)


def main():
    import sys
    if '--test' in sys.argv:
        test()
        return

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
