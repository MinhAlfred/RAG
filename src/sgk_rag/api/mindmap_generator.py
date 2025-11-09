"""Mindmap Generator - Tạo sơ đồ tư duy từ SGK Informatics"""

import json
import time
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..core.rag_pipeline import RAGPipeline
from ..models.dto import (
    MindmapNode, MindmapConnection, MindmapRequest, MindmapResponse,
    NodeType
)


class MindmapGenerator:
    """Class để tạo mindmap từ SGK"""

    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Khởi tạo MindmapGenerator

        Args:
            rag_pipeline: RAG pipeline đã được khởi tạo
        """
        self.rag_pipeline = rag_pipeline

    def generate_mindmap(self, request: MindmapRequest) -> MindmapResponse:
        """
        Tạo mindmap từ topic

        Args:
            request: MindmapRequest chứa thông tin yêu cầu

        Returns:
            MindmapResponse: Cấu trúc mindmap hoàn chỉnh
        """
        start_time = time.time()

        try:
            # 1. Tạo center node
            center_node = self._create_center_node(request.topic)

            # 2. Tạo primary branches (level 1)
            primary_nodes = self._generate_primary_branches(
                request.topic,
                request.max_branches,
                request.grade
            )

            # 3. Tạo connections từ center đến primary
            connections = []
            for node in primary_nodes:
                connections.append(MindmapConnection(
                    source=center_node.id,
                    target=node.id
                ))

            # 4. Tạo secondary và tertiary branches (level 2, 3)
            all_nodes = list(primary_nodes)
            if request.max_depth >= 2:
                secondary_result = self._generate_child_branches(
                    primary_nodes,
                    request.topic,
                    request.grade,
                    level=2,
                    max_depth=request.max_depth,
                    include_examples=request.include_examples
                )
                all_nodes.extend(secondary_result['nodes'])
                connections.extend(secondary_result['connections'])

            # 5. Tính toán độ sâu thực tế
            actual_depth = max((node.level for node in all_nodes), default=1)

            # 6. Thu thập sources
            sources = self._get_sources(request.topic, request.grade)

            processing_time = time.time() - start_time

            return MindmapResponse(
                centerNode=center_node,
                nodes=all_nodes,
                connections=connections,
                topic=request.topic,
                grade=request.grade,
                total_nodes=len(all_nodes) + 1,  # +1 for center
                max_depth=actual_depth,
                status="success",
                processing_time=processing_time,
                sources=sources
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return MindmapResponse(
                centerNode=MindmapNode(id="center", label="ERROR", type=NodeType.CENTER, level=0),
                nodes=[],
                connections=[],
                topic=request.topic,
                grade=request.grade,
                total_nodes=1,
                max_depth=0,
                status="error",
                processing_time=processing_time,
                error=str(e)
            )

    def _create_center_node(self, topic: str) -> MindmapNode:
        """Tạo node trung tâm"""
        # Format topic: uppercase và thêm line break nếu dài
        label = topic.upper()
        if len(label) > 20:
            # Tách thành 2 dòng tại khoảng trắng gần giữa nhất
            words = label.split()
            mid = len(words) // 2
            label = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])

        return MindmapNode(
            id="center",
            label=label,
            type=NodeType.CENTER,
            level=0
        )

    def _generate_primary_branches(
        self,
        topic: str,
        max_branches: int,
        grade: Optional[int]
    ) -> List[MindmapNode]:
        """Tạo các nhánh chính (level 1)"""

        # Tạo prompt để LLM đề xuất các nhánh chính
        prompt = f"""Đưa ra {max_branches} khái niệm hoặc thành phần CHÍNH của chủ đề "{topic}".

QUAN TRỌNG:
- Chỉ liệt kê TÊN của các khái niệm, KHÔNG giải thích
- Mỗi khái niệm trên một dòng
- Chỉ dùng 2-4 từ cho mỗi khái niệm
- Sắp xếp theo thứ tự logic hoặc tầm quan trọng

Ví dụ format:
Khái niệm 1
Khái niệm 2
Khái niệm 3"""

        try:
            response = self.rag_pipeline.query(
                prompt,
                grade_filter=grade,
                return_sources=False
            )

            # Extract answer
            if isinstance(response, dict):
                answer = response.get('answer', '')
            else:
                answer = str(response)

            # Parse branches từ response
            branches = self._parse_branches(answer, max_branches)

            # Tạo nodes
            nodes = []
            for i, branch_name in enumerate(branches[:max_branches], 1):
                node_id = self._create_node_id(branch_name)
                nodes.append(MindmapNode(
                    id=node_id,
                    label=branch_name,
                    type=NodeType.PRIMARY,
                    level=1
                ))

            return nodes

        except Exception as e:
            print(f"Error generating primary branches: {e}")
            # Fallback: tạo các nhánh generic
            return self._create_fallback_primary_branches(topic, max_branches)

    def _generate_child_branches(
        self,
        parent_nodes: List[MindmapNode],
        topic: str,
        grade: Optional[int],
        level: int,
        max_depth: int,
        include_examples: bool
    ) -> Dict[str, List]:
        """
        Tạo các nhánh con cho các parent nodes

        Returns:
            Dict với keys 'nodes' và 'connections'
        """
        all_nodes = []
        all_connections = []

        # Giới hạn số children dựa vào level
        max_children_per_node = {
            2: 3,  # Level 2: tối đa 3 children per parent
            3: 2,  # Level 3: tối đa 2 children per parent
            4: 2,  # Level 4: tối đa 2 children per parent
        }.get(level, 2)

        # Chỉ tạo children cho một số parent nodes (không phải tất cả)
        # Để tránh mindmap quá phức tạp
        num_parents_to_expand = min(len(parent_nodes), max(3, len(parent_nodes) // 2))
        selected_parents = parent_nodes[:num_parents_to_expand]

        for parent in selected_parents:
            # Hỏi LLM về sub-concepts
            prompt = f"""Đưa ra {max_children_per_node} khái niệm con hoặc ví dụ cụ thể của "{parent.label}" trong bối cảnh "{topic}".

QUAN TRỌNG:
- Chỉ liệt kê TÊN ngắn gọn, KHÔNG giải thích
- Mỗi khái niệm trên một dòng
- Tối đa 2-3 từ cho mỗi khái niệm
- Nếu đây là level cuối, đưa ra ví dụ CỤ THỂ thay vì khái niệm chung chung

Format:
Khái niệm con 1
Khái niệm con 2"""

            try:
                response = self.rag_pipeline.query(
                    prompt,
                    grade_filter=grade,
                    return_sources=False
                )

                if isinstance(response, dict):
                    answer = response.get('answer', '')
                else:
                    answer = str(response)

                # Parse children
                children = self._parse_branches(answer, max_children_per_node)

                # Determine node type based on level
                node_type = {
                    2: NodeType.SECONDARY,
                    3: NodeType.TERTIARY,
                    4: NodeType.LEAF
                }.get(level, NodeType.LEAF)

                # Tạo child nodes
                for child_name in children[:max_children_per_node]:
                    child_id = self._create_node_id(child_name, parent.id)
                    child_node = MindmapNode(
                        id=child_id,
                        label=child_name,
                        type=node_type,
                        level=level
                    )
                    all_nodes.append(child_node)

                    # Tạo connection
                    all_connections.append(MindmapConnection(
                        source=parent.id,
                        target=child_id
                    ))

            except Exception as e:
                print(f"Error generating children for {parent.label}: {e}")
                continue

        # Recursive call nếu chưa đạt max_depth
        if level < max_depth and all_nodes:
            deeper_result = self._generate_child_branches(
                all_nodes,
                topic,
                grade,
                level + 1,
                max_depth,
                include_examples
            )
            all_nodes.extend(deeper_result['nodes'])
            all_connections.extend(deeper_result['connections'])

        return {
            'nodes': all_nodes,
            'connections': all_connections
        }

    def _parse_branches(self, text: str, max_items: int) -> List[str]:
        """Parse các nhánh từ text response của LLM"""
        branches = []

        # Remove markdown formatting
        text = re.sub(r'[*_#`]', '', text)

        # Split by lines
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines, headers, introductory text
            if not line or len(line) < 3:
                continue
            if line.lower().startswith(('đây là', 'dưới đây', 'các', 'bao gồm', 'gồm có')):
                continue
            if line.endswith(':'):
                continue

            # Remove numbering (1., 2., -, *, etc.)
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            line = re.sub(r'^[-*•]\s*', '', line)

            # Remove explanations (text after - or : or ())
            line = re.split(r'\s*[-:]\s*', line)[0]
            line = re.sub(r'\s*\([^)]+\)\s*', '', line)

            line = line.strip()

            # Validate length (should be short - 2-4 words ideally)
            word_count = len(line.split())
            if word_count > 6:  # Skip if too long (likely explanation)
                continue

            if line and line not in branches:
                branches.append(line)

                if len(branches) >= max_items:
                    break

        return branches

    def _create_node_id(self, label: str, parent_id: str = None) -> str:
        """Tạo ID cho node từ label"""
        # Convert to lowercase and remove special chars
        node_id = label.lower()
        node_id = re.sub(r'[^a-z0-9\s]', '', node_id)
        node_id = re.sub(r'\s+', '_', node_id.strip())

        # Truncate if too long
        if len(node_id) > 30:
            node_id = node_id[:30]

        # Add parent prefix if provided (to ensure uniqueness)
        if parent_id and parent_id != "center":
            node_id = f"{parent_id[:10]}_{node_id}"

        return node_id or "node"

    def _create_fallback_primary_branches(
        self,
        topic: str,
        max_branches: int
    ) -> List[MindmapNode]:
        """Tạo các nhánh fallback khi LLM không hoạt động"""
        # Generic branches
        generic_branches = [
            "Khái niệm", "Đặc điểm", "Phân loại",
            "Chức năng", "Ứng dụng", "Ví dụ"
        ]

        nodes = []
        for i, branch_name in enumerate(generic_branches[:max_branches], 1):
            node_id = self._create_node_id(branch_name)
            nodes.append(MindmapNode(
                id=node_id,
                label=branch_name,
                type=NodeType.PRIMARY,
                level=1
            ))

        return nodes

    def _get_sources(self, topic: str, grade: Optional[int]) -> List[str]:
        """Lấy thông tin sources từ retrieval"""
        try:
            response = self.rag_pipeline.query(
                topic,
                grade_filter=grade,
                return_sources=True
            )

            if isinstance(response, dict) and response.get('sources'):
                sources = []
                for source in response['sources'][:3]:  # Top 3 sources
                    if isinstance(source, dict):
                        lesson = source.get('lesson_title', '')
                        grade = source.get('grade', '')
                        if lesson:
                            sources.append(f"SGK Tin học {grade} - {lesson}")
                return sources
        except:
            pass

        return ["SGK Tin học"]
