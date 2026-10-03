# Research report

Run: `research-a69dd6e553e2` · Outcome: **completed**

**Question:** What is the PTF component proposed by FQ-ViT?

**Scope:** Explain PTF from the author-reported abstract only. Do not assess experiments, alternatives, or LIS.

## Search method

Keyword discovery; deduplication by identifiers and conservative title matching. Ranking uses question word overlap (0.8), recency (0.1), and abstract availability (0.1). Citation counts do not establish relevance or truth.

Round 1: FQ-ViT

- arxiv: 1 records
- openalex: 1 records

## Findings and direct evidence

Statements below are attributed to retained source text. A support check establishes a bounded textual assessment, not independent experimental validation.

- **ev-ac2c4dd9fda1** — PTF addresses performance degradation and inference complexity in fully quantized vision transformers. [FQ-ViT: Post-Training Quantization for Fully Quantized Vision Transformer](https://arxiv.org/abs/2111.13824v4)
  - Basis: abstract; retained text characters 461:610; source `arxiv:2111.13824`.
  - Exact quotation: Power-of-Two Factor (PTF), a systematic method to reduce the performance degradation and inference complexity of fully quantized vision transformers.
  - Support assessment: The abstract identifies PTF as the “Power-of-Two Factor (PTF), a systematic method” and states that it is proposed to reduce “the performance degradation and inference complexity of fully quantized vision transformers.” Thus, it supports the claim within the abstract-only scope, but does not provide further implementation details.

- **ev-5d758ebd933c** — The abstract attributes the difficulties to inter-channel variation in LayerNorm inputs. [FQ-ViT: Post-Training Quantization for Fully Quantized Vision Transformer](https://arxiv.org/abs/2111.13824v4)
  - Basis: abstract; retained text characters 351:446; source `arxiv:2111.13824`.
  - Exact quotation: many of these difficulties arise because of serious inter-channel variation in LayerNorm inputs
  - Support assessment: The abstract explicitly states that “many of these difficulties arise because of serious inter-channel variation in LayerNorm inputs,” directly supporting the claim that this variation is identified as the source of the difficulties.

## Comparisons and synthesis

No checked cross-source comparison is available. Differences in tasks, datasets, hardware, and metrics must be resolved before calling results contradictory.

## Coverage, gaps and uncertainty

- Addressed within the retrieved evidence: What is PTF and what problem is it proposed to address?
- The abstract does not provide implementation details explaining how PTF reduces performance degradation or inference complexity.

## Limitations and stopping condition

The author-reported abstract identifies PTF as the Power-of-Two Factor, describes it as a systematic method, and states that it addresses performance degradation and inference complexity in fully quantized vision transformers. It also attributes relevant difficulties to serious inter-channel variation in LayerNorm inputs.

Searches are bounded and do not establish systematic-review completeness. Metadata is not evidence of a result. Abstracts omit experimental detail. Accessible HTML may omit equations/figures and is read through a bounded window. Source statements remain author-reported. Model support judgments can be wrong; inspect exact quotations and scope before relying on the report.

Limits: `{'max_rounds': 1, 'max_papers': 1, 'results_per_query': 1, 'max_queries': 1, 'max_model_calls': 8, 'max_tokens': 90000, 'max_seconds': 90.0, 'max_http_requests': 4, 'max_download_bytes': 12000000, 'concurrency': 2}`

Usage: `{'model_calls': 5, 'tokens': 4277, 'reserved_tokens': 32987, 'http_requests': 0, 'download_bytes': 0, 'cache_hits': 2}`

## References and reading depth

- [FQ-ViT: Post-Training Quantization for Fully Quantized Vision Transformer](https://arxiv.org/abs/2111.13824v4) (2021), `arxiv:2111.13824`; IDs: `{'arxiv': '2111.13824v4', 'arxiv_unversioned': '2111.13824', 'openalex': 'W4285601701', 'doi': '10.24963/ijcai.2022/164'}`; **abstract**. Provider-supplied abstract; the full paper has not been read. Analysis read characters 0:1349 of 1349; reading window truncated: False.
