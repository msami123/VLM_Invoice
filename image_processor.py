"""
Image preprocessing and document extraction module for invoice data extraction
"""

from PIL import Image, ImageEnhance
from ultralytics import YOLO
import numpy as np
import cv2
from typing import List, Tuple, Optional


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve data extraction quality

    Args:
        image: PIL Image object

    Returns:
        Preprocessed PIL Image
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Upscale image if it's too small
    width, height = image.size
    if width < 1000 or height < 1000:
        scale = max(1000 / width, 1000 / height)
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)

    # Slightly enhance brightness
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)

    return image


def crop_document_with_mask(image: Image.Image, mask: Optional[np.ndarray], box: np.ndarray) -> Image.Image:
    """
    Crop document using segmentation mask and bounding box

    Args:
        image: PIL Image object
        mask: Segmentation mask (numpy array) or None
        box: Bounding box coordinates [x1, y1, x2, y2]

    Returns:
        Cropped document as PIL Image with white background
    """
    # Convert image to numpy array
    img_array = np.array(image)

    # Get bounding box coordinates
    x1, y1, x2, y2 = map(int, box)

    # Crop the region
    cropped = img_array[y1:y2, x1:x2].copy()

    # Apply mask if available
    if mask is not None:
        # Resize mask to original image size
        mask_resized = cv2.resize(mask, (img_array.shape[1], img_array.shape[0]))

        # Crop mask to same region
        mask_cropped = mask_resized[y1:y2, x1:x2]

        # Create white background
        white_bg = np.ones_like(cropped) * 255

        # Merge document with white background using mask
        mask_3channel = np.stack([mask_cropped] * 3, axis=-1)
        result = np.where(mask_3channel > 0.5, cropped, white_bg)

        return Image.fromarray(result.astype('uint8'))

    return Image.fromarray(cropped)


def filter_overlapping_detections(boxes: np.ndarray, confs: np.ndarray, iou_threshold: float = 0.3) -> List[int]:
    """
    Filter overlapping detections, keeping only the highest confidence ones

    Args:
        boxes: Bounding boxes array (N, 4) [x1, y1, x2, y2]
        confs: Confidence scores array (N,)
        iou_threshold: IOU threshold for considering boxes as overlapping

    Returns:
        List of indices to keep
    """
    if len(boxes) <= 1:
        return list(range(len(boxes)))

    # Sort by confidence (descending)
    sorted_indices = np.argsort(confs)[::-1]

    keep_indices = [sorted_indices[0]]

    for idx in sorted_indices[1:]:
        should_keep = True

        for kept_idx in keep_indices:
            # Calculate IOU
            box1 = boxes[idx]
            box2 = boxes[kept_idx]

            x1 = max(box1[0], box2[0])
            y1 = max(box1[1], box2[1])
            x2 = min(box1[2], box2[2])
            y2 = min(box1[3], box2[3])

            if x2 > x1 and y2 > y1:
                inter = (x2 - x1) * (y2 - y1)
                area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
                area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
                union = area1 + area2 - inter
                iou = inter / union if union > 0 else 0

                if iou > iou_threshold:
                    should_keep = False
                    break

        if should_keep:
            keep_indices.append(idx)

    return keep_indices


def extract_documents(
    image: Image.Image,
    model_path: str,
    confidence: float = 0.5,
    iou: float = 0.6,
    preprocess: bool = True,
    min_area_ratio: float = 0.02,
    max_area_ratio: float = 0.8
) -> List[Tuple[Image.Image, float, Tuple[int, int, int, int]]]:
    """
    Extract documents from image using YOLO segmentation model

    Args:
        image: PIL Image object
        model_path: Path to YOLO model file
        confidence: Confidence threshold (0-1)
        iou: IOU threshold for NMS (0-1)
        preprocess: Whether to preprocess the image
        min_area_ratio: Minimum area ratio (relative to image size)
        max_area_ratio: Maximum area ratio (relative to image size)

    Returns:
        List of tuples: (cropped_document, confidence, bounding_box)
        bounding_box format: (x1, y1, x2, y2)
    """
    # Preprocess image if requested
    if preprocess:
        image = preprocess_image(image)

    # Load model
    model = YOLO('invoice-extractor-final/best (1).pt')

    # Run prediction
    results = model.predict(
        source=image,
        conf=confidence,
        iou=iou,
        verbose=False
    )

    if len(results[0].boxes) == 0:
        return []

    # Filter by area ratio
    img_area = image.size[0] * image.size[1]
    boxes = results[0].boxes.xyxy.cpu().numpy()
    confs = results[0].boxes.conf.cpu().numpy()

    valid_indices = []
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        area = (x2 - x1) * (y2 - y1)
        ratio = area / img_area

        if min_area_ratio < ratio < max_area_ratio:
            valid_indices.append(i)

    if not valid_indices:
        return []

    # Filter boxes and masks
    filtered_boxes = boxes[valid_indices]
    filtered_confs = confs[valid_indices]

    # Get masks if available
    masks = None
    if results[0].masks is not None:
        masks = results[0].masks.data.cpu().numpy()[valid_indices]

    # Filter overlapping detections
    keep_indices = filter_overlapping_detections(filtered_boxes, filtered_confs)

    # Extract documents
    documents = []
    for i in keep_indices:
        box = filtered_boxes[i]
        conf = filtered_confs[i]
        mask = masks[i] if masks is not None else None

        # Crop document
        cropped_doc = crop_document_with_mask(image, mask, box)

        # Store result
        documents.append((
            cropped_doc,
            float(conf),
            tuple(map(int, box))
        ))

    # Sort by confidence (highest first)
    documents.sort(key=lambda x: x[1], reverse=True)

    return documents


def extract_single_document(
    image: Image.Image,
    model_path: str,
    confidence: float = 0.5,
    iou: float = 0.6,
    preprocess: bool = True
) -> Optional[Tuple[Image.Image, float]]:
    """
    Extract the highest confidence document from image

    Args:
        image: PIL Image object
        model_path: Path to YOLO model file
        confidence: Confidence threshold (0-1)
        iou: IOU threshold for NMS (0-1)
        preprocess: Whether to preprocess the image

    Returns:
        Tuple of (cropped_document, confidence) or None if no document found
    """
    documents = extract_documents(image, model_path, confidence, iou, preprocess)

    if documents:
        doc, conf, _ = documents[0]
        return doc, conf

    return None