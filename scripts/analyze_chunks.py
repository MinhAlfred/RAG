#!/usr/bin/env python3
"""
Analyze chunks to optimize chunking parameters
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class ChunkAnalyzer:
    """
    Analyze chunks to understand distribution and optimize parameters
    """
    
    def __init__(self, processed_dir: str = "data/processed"):
        self.processed_dir = Path(processed_dir)
        self.chunk_data = {}
        
    def load_all_chunks(self) -> Dict:
        """
        Load all chunk files and analyze them
        """
        chunk_files = list(self.processed_dir.glob("*_chunks.json"))
        
        for file_path in chunk_files:
            grade = self._extract_grade(file_path.name)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            self.chunk_data[grade] = {
                'file': file_path.name,
                'chunks': chunks,
                'count': len(chunks),
                'token_counts': [chunk['token_count'] for chunk in chunks],
                'avg_tokens': statistics.mean([chunk['token_count'] for chunk in chunks]),
                'median_tokens': statistics.median([chunk['token_count'] for chunk in chunks]),
                'std_tokens': statistics.stdev([chunk['token_count'] for chunk in chunks]) if len(chunks) > 1 else 0
            }
        
        return self.chunk_data
    
    def _extract_grade(self, filename: str) -> int:
        """Extract grade number from filename"""
        return int(filename.split('_')[3])
    
    def analyze_by_grade(self) -> Dict:
        """
        Analyze chunks by grade level
        """
        analysis = {}
        
        for grade, data in self.chunk_data.items():
            token_counts = data['token_counts']
            
            analysis[grade] = {
                'total_chunks': data['count'],
                'avg_tokens': round(data['avg_tokens'], 2),
                'median_tokens': data['median_tokens'],
                'std_tokens': round(data['std_tokens'], 2),
                'min_tokens': min(token_counts),
                'max_tokens': max(token_counts),
                'q25': round(statistics.quantiles(token_counts, n=4)[0], 2) if len(token_counts) > 3 else 0,
                'q75': round(statistics.quantiles(token_counts, n=4)[2], 2) if len(token_counts) > 3 else 0,
                'efficiency': self._calculate_efficiency(token_counts)
            }
        
        return analysis
    
    def _calculate_efficiency(self, token_counts: List[int]) -> float:
        """
        Calculate chunking efficiency (how close chunks are to target size)
        """
        target_size = 1000  # Current target
        deviations = [abs(count - target_size) / target_size for count in token_counts]
        efficiency = 1 - statistics.mean(deviations)
        return round(max(0, efficiency), 3)
    
    def suggest_optimal_params(self) -> Dict:
        """
        Suggest optimal chunking parameters for different grade levels
        """
        suggestions = {}
        
        for grade, data in self.chunk_data.items():
            token_counts = data['token_counts']
            avg_tokens = data['avg_tokens']
            
            # Categorize by education level
            if grade <= 5:
                level = "Tiểu học"
                suggested_chunk_size = 800  # Smaller for elementary
                suggested_overlap = 150
            elif grade <= 9:
                level = "THCS"
                suggested_chunk_size = 1000  # Standard
                suggested_overlap = 200
            else:
                level = "THPT"
                suggested_chunk_size = 1200  # Larger for high school
                suggested_overlap = 250
            
            suggestions[grade] = {
                'education_level': level,
                'current_avg': round(avg_tokens, 2),
                'suggested_chunk_size': suggested_chunk_size,
                'suggested_overlap': suggested_overlap,
                'reason': self._get_suggestion_reason(grade, avg_tokens, suggested_chunk_size)
            }
        
        return suggestions
    
    def _get_suggestion_reason(self, grade: int, current_avg: float, suggested: int) -> str:
        """Get reason for parameter suggestion"""
        if grade <= 5:
            return f"Tiểu học: Nội dung đơn giản hơn, chunk nhỏ hơn ({suggested} tokens) để tăng độ chính xác retrieval"
        elif grade <= 9:
            return f"THCS: Nội dung cân bằng, chunk size tiêu chuẩn ({suggested} tokens)"
        else:
            return f"THPT: Nội dung phức tạp hơn, chunk lớn hơn ({suggested} tokens) để giữ ngữ cảnh"
    
    def generate_report(self) -> str:
        """
        Generate comprehensive analysis report
        """
        if not self.chunk_data:
            self.load_all_chunks()
        
        analysis = self.analyze_by_grade()
        suggestions = self.suggest_optimal_params()
        
        report = []
        report.append("=" * 80)
        report.append("📊 CHUNK ANALYSIS REPORT")
        report.append("=" * 80)
        
        # Overall statistics
        total_chunks = sum(data['count'] for data in self.chunk_data.values())
        total_tokens = sum(sum(data['token_counts']) for data in self.chunk_data.values())
        avg_tokens_overall = total_tokens / total_chunks if total_chunks > 0 else 0
        
        report.append(f"\n🎯 Overall Statistics:")
        report.append(f"   Total chunks: {total_chunks:,}")
        report.append(f"   Total tokens: {total_tokens:,}")
        report.append(f"   Average tokens per chunk: {avg_tokens_overall:.2f}")
        
        # By grade analysis
        report.append(f"\n📚 Analysis by Grade:")
        report.append(f"{'Grade':<6} {'Chunks':<8} {'Avg':<8} {'Med':<8} {'Std':<8} {'Min':<6} {'Max':<6} {'Eff':<6}")
        report.append("-" * 60)
        
        for grade in sorted(analysis.keys()):
            data = analysis[grade]
            report.append(f"{grade:<6} {data['total_chunks']:<8} {data['avg_tokens']:<8} "
                         f"{data['median_tokens']:<8} {data['std_tokens']:<8} {data['min_tokens']:<6} "
                         f"{data['max_tokens']:<6} {data['efficiency']:<6}")
        
        # Optimization suggestions
        report.append(f"\n🎯 Optimization Suggestions:")
        for grade in sorted(suggestions.keys()):
            sugg = suggestions[grade]
            report.append(f"\n   Grade {grade} ({sugg['education_level']}):")
            report.append(f"      Current avg: {sugg['current_avg']} tokens")
            report.append(f"      Suggested chunk_size: {sugg['suggested_chunk_size']}")
            report.append(f"      Suggested overlap: {sugg['suggested_overlap']}")
            report.append(f"      Reason: {sugg['reason']}")
        
        # Recommendations
        report.append(f"\n💡 Recommendations:")
        report.append(f"   1. Sử dụng chunk size khác nhau cho từng cấp học")
        report.append(f"   2. Tiểu học (3-5): 800 tokens, overlap 150")
        report.append(f"   3. THCS (6-9): 1000 tokens, overlap 200")
        report.append(f"   4. THPT (10-12): 1200 tokens, overlap 250")
        report.append(f"   5. Điều chỉnh dựa trên độ phức tạp nội dung")
        
        return "\n".join(report)
    
    def save_analysis(self, output_file: str = "chunk_analysis_report.txt"):
        """Save analysis to file"""
        report = self.generate_report()
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 Analysis report saved to: {output_path}")
        return output_path

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze chunks for optimization")
    parser.add_argument("--processed-dir", default="data/processed", help="Processed chunks directory")
    parser.add_argument("--output", default="chunk_analysis_report.txt", help="Output report file")
    
    args = parser.parse_args()
    
    analyzer = ChunkAnalyzer(args.processed_dir)
    analyzer.load_all_chunks()
    
    # Print report to console
    print(analyzer.generate_report())
    
    # Save to file
    analyzer.save_analysis(args.output)

if __name__ == "__main__":
    main()