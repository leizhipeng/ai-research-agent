# Research report

Run: `research-869255844c3b` · Outcome: **partial**

**Question:** How do quantization and pruning affect vision transformer inference on edge GPUs?

**Scope:** No additional scope supplied.

**SYNTHETIC OFFLINE DEMONSTRATION.** Papers and statements are invented teaching data. Deterministic model substitutes exercise the workflow. This is not a real literature review.

## Search method

Keyword discovery; deduplication by identifiers and conservative title matching. Ranking uses question word overlap (0.8), recency (0.1), and abstract availability (0.1). Citation counts do not establish relevance or truth.

Round 1: How do quantization and pruning affect vision transformer inference on edge GPUs?

- synthetic: 2 records

Round 2: vision transformer edge GPU comparable quantization latency setup

- synthetic: 1 records

## Findings and direct evidence

Statements below are attributed to retained source text. A support check establishes a bounded textual assessment, not independent experimental validation.

- **ev-e59ef7c421d8** — This synthetic classroom example evaluates structured channel pruning of a vision transformer on the fictional Edge-A GPU. Removing complete channels reduced model size. Sparse weight pruning alone did not reduce batch-one inference latency on the dense kernel used in this example. Fine-tuning recovered some accuracy. Results apply to the stated kernel and hardware; energy consumption was not measured. [SYNTHETIC: Structured Pruning for Edge Inference](https://example.invalid/synthetic/pruning)
  - Basis: abstract; retained text characters 0:405; source `synthetic:pruning`.
  - Exact quotation: This synthetic classroom example evaluates structured channel pruning of a vision transformer on the fictional Edge-A GPU. Removing complete channels reduced model size. Sparse weight pruning alone did not reduce batch-one inference latency on the dense kernel used in this example. Fine-tuning recovered some accuracy. Results apply to the stated kernel and hardware; energy consumption was not measured.
  - Support assessment: Offline substitute accepts only a claim identical to its retained quotation.

- **ev-428c796bb847** — This synthetic classroom example studies post-training quantization of a vision transformer. On the fictional Edge-A GPU, INT8 quantization reduced batch-one inference latency compared with the FP32 baseline. Representative calibration inputs reduced accuracy loss. The example holds model architecture, image resolution, and batch size fixed. It does not measure energy use or evaluate deployment under distribution shift. [SYNTHETIC: Calibrated Quantization of a Vision Transformer](https://example.invalid/synthetic/quantization)
  - Basis: abstract; retained text characters 0:423; source `synthetic:quantization`.
  - Exact quotation: This synthetic classroom example studies post-training quantization of a vision transformer. On the fictional Edge-A GPU, INT8 quantization reduced batch-one inference latency compared with the FP32 baseline. Representative calibration inputs reduced accuracy loss. The example holds model architecture, image resolution, and batch size fixed. It does not measure energy use or evaluate deployment under distribution shift.
  - Support assessment: Offline substitute accepts only a claim identical to its retained quotation.

- **ev-4ad6c0237525** — This synthetic classroom follow-up evaluates mixed precision on the fictional Desktop-B GPU at batch size thirty-two. FP16 increased throughput compared with FP32 for the same vision transformer. The experiment did not measure batch-one latency on Edge-A, so its result is not directly comparable with the edge quantization example. No energy measurement was reported. Hardware, batch size, and kernel support affect the practical speed benefit. [SYNTHETIC: Precision and Batch Size on a Desktop GPU](https://example.invalid/synthetic/setup)
  - Basis: abstract; retained text characters 0:445; source `synthetic:setup`.
  - Exact quotation: This synthetic classroom follow-up evaluates mixed precision on the fictional Desktop-B GPU at batch size thirty-two. FP16 increased throughput compared with FP32 for the same vision transformer. The experiment did not measure batch-one latency on Edge-A, so its result is not directly comparable with the edge quantization example. No energy measurement was reported. Hardware, batch size, and kernel support affect the practical speed benefit.
  - Support assessment: Offline substitute accepts only a claim identical to its retained quotation.

## Comparisons and synthesis

- **different_setup**: The synthetic Edge-A batch-one latency and Desktop-B batch-size-thirty-two throughput results use different hardware, batch sizes, and metrics; they are not directly comparable. (evidence: ev-428c796bb847, ev-4ad6c0237525)

## Coverage, gaps and uncertainty

- Addressed within the retrieved evidence: Which approaches does the supplied corpus describe?
- Unresolved: Are the reported setups comparable, and what remains unknown?
- The corpus does not establish comparable quantitative performance or deployment applicability.

## Limitations and stopping condition

Synthetic examples demonstrate the workflow; research conclusions remain unresolved. Stopped at configured rounds/papers or no useful new query; unresolved scope is disclosed.

Searches are bounded and do not establish systematic-review completeness. Metadata is not evidence of a result. Abstracts omit experimental detail. Accessible HTML may omit equations/figures and is read through a bounded window. Source statements remain author-reported. Model support judgments can be wrong; inspect exact quotations and scope before relying on the report.

Limits: `{'max_rounds': 2, 'max_papers': 6, 'results_per_query': 4, 'max_queries': 3, 'max_model_calls': 24, 'max_tokens': 100000, 'max_seconds': 300.0, 'max_http_requests': 30, 'max_download_bytes': 12000000, 'concurrency': 2}`

Usage: `{'model_calls': 10, 'tokens': 0, 'reserved_tokens': 0, 'http_requests': 0, 'download_bytes': 0, 'cache_hits': 0}`

## References and reading depth

- [SYNTHETIC: Structured Pruning for Edge Inference](https://example.invalid/synthetic/pruning) (year unknown), `synthetic:pruning`; IDs: `{'synthetic': 'pruning'}`; **abstract**. Synthetic educational excerpt and deterministic model substitute; not real research evidence. Analysis read characters 0:405 of 405; reading window truncated: False.
- [SYNTHETIC: Calibrated Quantization of a Vision Transformer](https://example.invalid/synthetic/quantization) (year unknown), `synthetic:quantization`; IDs: `{'synthetic': 'quantization'}`; **abstract**. Synthetic educational excerpt and deterministic model substitute; not real research evidence. Analysis read characters 0:423 of 423; reading window truncated: False.
- [SYNTHETIC: Precision and Batch Size on a Desktop GPU](https://example.invalid/synthetic/setup) (year unknown), `synthetic:setup`; IDs: `{'synthetic': 'setup'}`; **abstract**. Synthetic educational excerpt and deterministic model substitute; not real research evidence. Analysis read characters 0:445 of 445; reading window truncated: False.
