"""Performance profiling for Readable app."""

import time
import psutil
import os
from readable.chunker import TextChunker
from readable.tts_client import KokoroTTSClient


class PerformanceProfiler:
    """Profile performance metrics for optimization."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.metrics = {}

    def profile_chunker(self):
        """Profile text chunking performance."""
        print("\n=== Chunking Performance ===")

        chunker = TextChunker(max_chars=750)

        test_texts = {
            "small": "Hello world. " * 10,
            "medium": "This is a test sentence. " * 50,
            "large": "This is a test sentence. " * 200,
        }

        results = {}

        for name, text in test_texts.items():
            start_time = time.perf_counter()
            start_mem = self.process.memory_info().rss / 1024 / 1024

            chunks = chunker.chunk(text)

            end_time = time.perf_counter()
            end_mem = self.process.memory_info().rss / 1024 / 1024

            duration = end_time - start_time
            mem_delta = end_mem - start_mem

            results[name] = {
                "text_length": len(text),
                "chunks": len(chunks),
                "duration_ms": duration * 1000,
                "memory_mb": mem_delta
            }

            print(f"\n{name.upper()} ({len(text)} chars):")
            print(f"  Time: {duration * 1000:.2f}ms")
            print(f"  Chunks: {len(chunks)}")
            print(f"  Memory: {mem_delta:.2f}MB")

        self.metrics["chunker"] = results
        return results

    def profile_tts_generation(self):
        """Profile TTS API performance."""
        print("\n=== TTS Generation Performance ===")

        client = KokoroTTSClient()

        test_cases = [
            ("short", "Hello world!"),
            ("medium", "This is a longer test to see performance. " * 5),
            ("long", "This is a test sentence. " * 30),
        ]

        results = {}

        for name, text in test_cases:
            start_time = time.perf_counter()
            start_mem = self.process.memory_info().rss / 1024 / 1024

            audio_bytes = client.synthesize(text)

            end_time = time.perf_counter()
            end_mem = self.process.memory_info().rss / 1024 / 1024

            duration = end_time - start_time
            mem_delta = end_mem - start_mem
            audio_size = len(audio_bytes) if audio_bytes else 0

            results[name] = {
                "text_length": len(text),
                "duration_ms": duration * 1000,
                "audio_size_kb": audio_size / 1024,
                "memory_mb": mem_delta,
                "throughput_chars_per_sec": len(text) / duration if duration > 0 else 0
            }

            print(f"\n{name.upper()} ({len(text)} chars):")
            print(f"  API Time: {duration * 1000:.2f}ms")
            print(f"  Audio Size: {audio_size / 1024:.1f}KB")
            print(f"  Throughput: {len(text) / duration:.0f} chars/sec")

        self.metrics["tts"] = results
        return results

    def identify_bottlenecks(self):
        """Analyze metrics and identify optimization opportunities."""
        print("\n" + "=" * 60)
        print("BOTTLENECK ANALYSIS")
        print("=" * 60)

        bottlenecks = []

        if "tts" in self.metrics:
            for name, data in self.metrics["tts"].items():
                if data["duration_ms"] > 500:
                    bottlenecks.append({
                        "component": "TTS Generation",
                        "severity": "HIGH",
                        "issue": f"{name} text takes {data['duration_ms']:.0f}ms",
                        "recommendation": "Implement caching and parallel processing"
                    })

        if "chunker" in self.metrics:
            for name, data in self.metrics["chunker"].items():
                if data["duration_ms"] > 10:
                    bottlenecks.append({
                        "component": "Text Chunking",
                        "severity": "MEDIUM",
                        "issue": f"{name} text takes {data['duration_ms']:.2f}ms",
                        "recommendation": "Optimize regex patterns or use faster parsing"
                    })

        print("\nIdentified Bottlenecks:")
        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"\n{i}. [{bottleneck['severity']}] {bottleneck['component']}")
            print(f"   Issue: {bottleneck['issue']}")
            print(f"   → {bottleneck['recommendation']}")

        if not bottlenecks:
            print("\n✓ No significant bottlenecks detected!")

        print("\n" + "=" * 60)
        print("OPTIMIZATION OPPORTUNITIES")
        print("=" * 60)

        opportunities = [
            {
                "area": "Caching",
                "impact": "HIGH",
                "description": "Cache TTS results to avoid re-generating same text",
                "estimated_gain": "50-90% latency reduction for repeated texts"
            },
            {
                "area": "Parallel Processing",
                "impact": "HIGH",
                "description": "Generate multiple chunks in parallel",
                "estimated_gain": "2-4x faster for multi-chunk texts"
            },
            {
                "area": "Background Threading",
                "impact": "MEDIUM",
                "description": "Move TTS generation off main thread",
                "estimated_gain": "Non-blocking UI, better UX"
            },
            {
                "area": "Audio Compression",
                "impact": "MEDIUM",
                "description": "Compress audio files in memory",
                "estimated_gain": "30-50% memory reduction"
            },
            {
                "area": "Prefetching",
                "impact": "LOW",
                "description": "Pre-generate next chunk during playback",
                "estimated_gain": "Seamless chunk transitions"
            }
        ]

        for opp in opportunities:
            print(f"\n[{opp['impact']}] {opp['area']}")
            print(f"  {opp['description']}")
            print(f"  Estimated gain: {opp['estimated_gain']}")

        return bottlenecks, opportunities


def main():
    """Run performance profiling."""
    print("=" * 60)
    print("READABLE PERFORMANCE PROFILING")
    print("=" * 60)

    profiler = PerformanceProfiler()

    profiler.profile_chunker()
    profiler.profile_tts_generation()
    profiler.identify_bottlenecks()

    print("\n" + "=" * 60)
    print("Profile complete! Ready for optimization.")
    print("=" * 60)


if __name__ == "__main__":
    main()
