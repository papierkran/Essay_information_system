import logging

logger = logging.getLogger(__name__)

_MIN_ANGLE = 1.0    # 低于该角度(度)不做旋转
_MAX_ANGLE = 20.0   # 超过该角度(度)不旋转，避免方向误判


def _decode(img_data: bytes):
    import cv2
    import numpy as np
    buf = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def _encode(img, fmt=".png"):
    import cv2
    ok, buf = cv2.imencode(fmt, img)
    if not ok:
        return None
    return buf.tobytes()


def _detect_fix_angle(img) -> float:
    """基于文本区域轮廓估算需要旋转的修正角度（度）。"""
    import cv2
    import numpy as np

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    inv = cv2.bitwise_not(gray)
    _, thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    h, w = thresh.shape[:2]
    img_area = float(w * h)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pts = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < img_area * 0.00005:
            continue
        x, y, cw, ch = cv2.boundingRect(cnt)
        if ch <= 0:
            continue
        aspect = cw / float(ch)
        if aspect < 0.1 or aspect > 12:
            continue
        pts.extend((p[1], p[0]) for p in cnt.reshape(-1, 2).tolist())

    if len(pts) < 30:
        return 0.0

    rect = cv2.minAreaRect(np.array(pts, np.float32))
    angle = rect[2]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if angle > _MAX_ANGLE:
        angle = 0.0
    return angle


def _rotate_image(img, angle_deg, border_value=255):
    import cv2
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    m = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    cos = abs(m[0, 0])
    sin = abs(m[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    m[0, 2] += (new_w / 2.0) - center[0]
    m[1, 2] += (new_h / 2.0) - center[1]
    return cv2.warpAffine(
        img, m, (new_w, new_h), flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=border_value,
    )


def correct_document_image(img_data: bytes):
    """OCR 前对图片做临时去倾斜矫正。

    返回 (矫正后的图片 bytes, 旋转角度或 None)；无法矫正/无需矫正时返回 (原 bytes, None)。

    - 未安装 opencv 时原样返回
    - 无法解码、无法判定偏斜时原样返回
    - 仅在检测到可信的小角度偏斜时旋转，其余情况保持原图
    仅在内存中处理，不修改磁盘或数据库中的原文件。
    """
    try:
        import cv2  # noqa: F401
    except ImportError:
        logger.debug("opencv-python-headless 未安装，跳过图片矫正")
        return img_data, None

    try:
        img = _decode(img_data)
        if img is None:
            return img_data, None

        angle = _detect_fix_angle(img)
        if abs(angle) < _MIN_ANGLE:
            return img_data, None

        corrected = _rotate_image(img, angle)
        out = _encode(corrected)
        if out is None:
            return img_data, None
        logger.info("OCR 前图片矫正完成 (旋转 %.2f°)", angle)
        return out, angle
    except Exception as e:
        logger.warning("图片矫正失败，使用原图: %s", e)
        return img_data, None