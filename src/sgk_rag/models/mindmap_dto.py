"""Mindmap Models - Request/Response models for mindmap generation"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class NodeType(str, Enum):
    """Loại node trong mindmap"""
    CENTER = "center"       # Node trung tâm
    PRIMARY = "primary"     # Branch chính (level 1)
    SECONDARY = "secondary" # Branch phụ (level 2)
    TERTIARY = "tertiary"   # Branch chi tiết (level 3)
    LEAF = "leaf"          # Node lá (level 4+)


class MindmapNode(BaseModel):
    """Node trong mindmap"""
    id: str = Field(..., description="ID duy nhất của node")
    label: str = Field(..., description="Nhãn hiển thị của node")
    type: NodeType = Field(..., description="Loại node (center/primary/secondary/tertiary/leaf)")
    level: int = Field(..., description="Cấp độ trong cây (0=center, 1=primary, ...)", ge=0, le=5)


class MindmapConnection(BaseModel):
    """Kết nối giữa các node trong mindmap"""
    source: str = Field(..., description="ID của node nguồn")
    target: str = Field(..., description="ID của node đích")


class MindmapRequest(BaseModel):
    """Request model cho tạo mindmap"""
    topic: str = Field(..., description="Chủ đề chính của mindmap", min_length=1)
    grade: Optional[int] = Field(None, description="Lớp học (3-12)", ge=3, le=12)
    maxDepth: int = Field(default=3, description="Độ sâu tối đa của cây (1-5)", ge=1, le=5)
    maxBranches: int = Field(default=6, description="Số nhánh chính tối đa", ge=3, le=10)
    includeExamples: bool = Field(default=False, description="Có bao gồm ví dụ cụ thể không")
    collectionName: Optional[str] = Field(None, description="Tên collection trong Qdrant")

class MindmapResponse(BaseModel):
    """Response model cho tạo mindmap"""
    centerNode: MindmapNode = Field(..., description="Node trung tâm")
    nodes: List[MindmapNode] = Field(..., description="Danh sách tất cả nodes (không bao gồm center)")
    connections: List[MindmapConnection] = Field(..., description="Danh sách kết nối giữa các nodes")
    topic: str = Field(..., description="Chủ đề mindmap")
    grade: Optional[int] = Field(None, description="Lớp học")
    totalNodes: int = Field(..., description="Tổng số nodes (bao gồm center)")
    maxDepth: int = Field(..., description="Độ sâu thực tế của cây")
    status: str = Field(default="success", description="Trạng thái (success/error)")
    processingTime: Optional[float] = Field(None, description="Thời gian xử lý (giây)")
    error: Optional[str] = Field(None, description="Thông báo lỗi nếu có")
    sources: Optional[List[str]] = Field(None, description="Nguồn tham khảo")


# Example data for API documentation
EXAMPLE_MINDMAP_REQUEST = {
    "topic": "Cấu trúc dữ liệu",
    "grade": 10,
    "max_depth": 3,
    "max_branches": 6,
    "include_examples": True,
    "collection_name": "sgk_tin_kntt"
}

EXAMPLE_MINDMAP_RESPONSE = {
    "centerNode": {
        "id": "center",
        "label": "CẤU TRÚC\nDỮ LIỆU",
        "type": "center",
        "level": 0
    },
    "nodes": [
        {"id": "array", "label": "Mảng", "type": "primary", "level": 1},
        {"id": "list", "label": "Danh sách", "type": "primary", "level": 1},
        {"id": "stack", "label": "Ngăn xếp", "type": "primary", "level": 1},
        {"id": "queue", "label": "Hàng đợi", "type": "primary", "level": 1},
        {"id": "tree", "label": "Cây", "type": "primary", "level": 1},
        {"id": "graph", "label": "Đồ thị", "type": "primary", "level": 1},
        {"id": "array_1d", "label": "Mảng 1 chiều", "type": "secondary", "level": 2},
        {"id": "array_2d", "label": "Mảng 2 chiều", "type": "secondary", "level": 2},
        {"id": "linked_list", "label": "Danh sách liên kết", "type": "secondary", "level": 2},
        {"id": "dynamic_array", "label": "Mảng động", "type": "secondary", "level": 2},
        {"id": "lifo", "label": "LIFO", "type": "secondary", "level": 2},
        {"id": "fifo", "label": "FIFO", "type": "secondary", "level": 2},
        {"id": "binary_tree", "label": "Cây nhị phân", "type": "secondary", "level": 2},
        {"id": "directed", "label": "Có hướng", "type": "secondary", "level": 2},
        {"id": "undirected", "label": "Vô hướng", "type": "secondary", "level": 2},
        {"id": "push_pop", "label": "Push/Pop", "type": "tertiary", "level": 3},
        {"id": "enqueue_dequeue", "label": "Enqueue/Dequeue", "type": "tertiary", "level": 3}
    ],
    "connections": [
        {"source": "center", "target": "array"},
        {"source": "center", "target": "list"},
        {"source": "center", "target": "stack"},
        {"source": "center", "target": "queue"},
        {"source": "center", "target": "tree"},
        {"source": "center", "target": "graph"},
        {"source": "array", "target": "array_1d"},
        {"source": "array", "target": "array_2d"},
        {"source": "list", "target": "linked_list"},
        {"source": "list", "target": "dynamic_array"},
        {"source": "stack", "target": "lifo"},
        {"source": "stack", "target": "push_pop"},
        {"source": "queue", "target": "fifo"},
        {"source": "queue", "target": "enqueue_dequeue"},
        {"source": "tree", "target": "binary_tree"},
        {"source": "graph", "target": "directed"},
        {"source": "graph", "target": "undirected"}
    ],
    "topic": "Cấu trúc dữ liệu",
    "grade": 10,
    "total_nodes": 24,
    "max_depth": 3,
    "status": "success",
    "processing_time": 2.3,
    "sources": ["SGK Tin học 10", "Chương 3: Cấu trúc dữ liệu"]
}
