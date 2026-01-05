#!/usr/bin/env python3
"""Benchmark the full test_text.md document workflow."""

import time
from pathlib import Path
from readable.chunker import TextChunker
from readable.tts_client import KokoroTTSClient
from readable.parallel_tts import ParallelTTSGenerator

def main():
    print("=" * 70)
    print("READABLE TTS - Full Document Benchmark")
    print("=" * 70)
    
    # Read test document
    test_file = Path("test_text.md")
    if not test_file.exists():
        print("❌ test_text.md not found!")
        return
    
    text = test_file.read_text()
    
    print(f"\n📄 Document Stats:")
    print(f"   File: {test_file.name}")
    print(f"   Size: {len(text):,} characters ({len(text) / 1024:.1f} KB)")
    print(f"   Words: {len(text.split()):,}")
    print(f"   Lines: {len(text.splitlines()):,}")
    
    # Step 1: Chunking
    print(f"\n📦 Step 1: Chunking")
    start_time = time.time()
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(text)
    chunk_time = time.time() - start_time
    
    print(f"   ✅ Created {len(chunks)} chunks in {chunk_time:.3f}s")
    print(f"   Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.0f} chars")
    print(f"   Largest chunk: {max(len(c) for c in chunks)} chars")
    print(f"   Smallest chunk: {min(len(c) for c in chunks)} chars")
    
    # Step 2: TTS Generation (first 5 chunks for testing)
    print(f"\n🎵 Step 2: TTS Generation (testing with first 5 chunks)")
    
    parallel_gen = ParallelTTSGenerator(max_workers=4)
    
    print(f"\n   First run (populating cache):")
    start_time = time.time()
    audio_chunks = parallel_gen.generate_batch(
        chunks[:5],
        voice="af_bella",
        speed=1.0,
        progress_callback=lambda c, t: print(f"      Generated {c}/{t} chunks...", end='\r')
    )
    first_run_time = time.time() - start_time
    
    print(f"\n   ✅ Generated 5 chunks in {first_run_time:.2f}s")
    print(f"   Average per chunk: {first_run_time / 5:.2f}s")
    
    # Second run from cache
    print(f"\n   Second run (from cache):")
    start_time = time.time()
    audio_chunks_cached = parallel_gen.generate_batch(
        chunks[:5],
        voice="af_bella",
        speed=1.0,
        progress_callback=lambda c, t: print(f"      Retrieved {c}/{t} from cache...", end='\r')
    )
    cache_run_time = time.time() - start_time
    
    print(f"\n   ✅ Retrieved 5 chunks from cache in {cache_run_time:.3f}s")
    print(f"   Speedup: {first_run_time / cache_run_time:.1f}x faster")
    
    # Calculate audio stats
    total_audio_size = sum(len(chunk) for chunk in audio_chunks if chunk)
    print(f"\n   Audio Stats:")
    print(f"   Total size: {total_audio_size / 1024 / 1024:.1f} MB (for 5 chunks)")
    print(f"   Average per chunk: {total_audio_size / 5 / 1024:.0f} KB")
    
    # Step 3: Projections for full document
    print(f"\n📊 Step 3: Full Document Projections")
    
    # Calculate time estimates
    chunks_per_second = 5 / first_run_time
    estimated_generation_time = len(chunks) / chunks_per_second
    
    # Calculate size estimates
    avg_chunk_audio_size = total_audio_size / 5
    estimated_total_size = avg_chunk_audio_size * len(chunks)
    
    # Calculate playback time (at ~11.8 chars/second speech rate)
    estimated_playback_time = len(text) / 11.8
    
    print(f"\n   Generation (parallel, 4 workers, first time):")
    print(f"   ⏱️  Estimated time: {estimated_generation_time / 60:.1f} minutes")
    print(f"   💾 Estimated cache size: {estimated_total_size / 1024 / 1024:.0f} MB")
    
    print(f"\n   Playback:")
    print(f"   ⏱️  Total duration: {estimated_playback_time / 60:.0f} minutes")
    print(f"   📦 Total chunks: {len(chunks)}")
    
    # Cache efficiency
    if parallel_gen.client.cache:
        cache_stats = parallel_gen.client.cache.get_stats()
        print(f"\n   Cache Performance:")
        print(f"   Entries: {cache_stats['entries']}")
        print(f"   Hit rate: {cache_stats['hit_rate']:.1f} avg hits/entry")
        print(f"   Total hits: {cache_stats['total_hits']}")
        print(f"   Cache size: {cache_stats['total_size_mb']:.1f} MB")
    
    print(f"\n{'=' * 70}")
    print("✅ Benchmark Complete!")
    print(f"{'=' * 70}")
    
    # Summary
    print(f"\n📝 Summary for {test_file.name}:")
    print(f"   • {len(chunks)} chunks @ ~{sum(len(c) for c in chunks) / len(chunks):.0f} chars each")
    print(f"   • ~{estimated_generation_time / 60:.0f} min to generate (first time)")
    print(f"   • ~{cache_run_time * len(chunks) / 5:.0f}s to load from cache (subsequent)")
    print(f"   • ~{estimated_playback_time / 60:.0f} min to listen")
    print(f"   • ~{estimated_total_size / 1024 / 1024:.0f} MB cache storage")
    print(f"   • {first_run_time / cache_run_time:.0f}x speedup with caching")
    
    print(f"\n🎯 Ready to test in app!")
    print(f"   1. Launch: uv run readable")
    print(f"   2. Copy text: cat test_text.md | pbcopy")
    print(f"   3. Click 􀈕 Read Clipboard (⌘R)")
    print(f"   4. Watch SF Symbols animate: 􀆺→􀍟→􀊄→􀁣")

if __name__ == "__main__":
    main()
