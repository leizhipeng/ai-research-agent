# Research report

Run: `research-03cea026004d` · Outcome: **partial**

**Question:** What methods are described for post-training quantization of vision transformers?

**Scope:** Describe author-reported methods and limitations from abstracts only.

## Search method

Keyword discovery; deduplication by identifiers and conservative title matching. Ranking uses question word overlap (0.8), recency (0.1), and abstract availability (0.1). Citation counts do not establish relevance or truth.

Round 1: vision transformer post-training quantization abstract

- arxiv: 0 records
- openalex: 2 records

Round 2: "vision transformer" "post-training quantization" method abstract

- arxiv: 0 records
- openalex: 2 records

## Findings and direct evidence

Statements below are attributed to retained source text. A support check establishes a bounded textual assessment, not independent experimental validation.

- **ev-a954c2f51a23** — The abstract reports deployment constraints from hardware and environmental restrictions. [A Survey on Efficient Vision Transformers: Algorithms, Techniques, and Performance Benchmarking](https://doi.org/10.1109/tpami.2024.3392941)
  - Basis: abstract; retained text characters 545:723; source `openalex:W4395113676`.
  - Exact quotation: it is challenging to employ these architectures in real-world applications due to many hardware and environmental restrictions, such as processing and computational capabilities.
  - Support assessment: The quote explicitly reports that employing vision transformers in real-world applications is challenging because of hardware and environmental restrictions, including processing and computational capabilities. This directly supports the claimed deployment constraints, although it does not specify post-training quantization methods or limitations specific to quantization.

- **ev-d398f9f7aedb** — The abstract introduces Efficient Error Rate for comparing inference-related model features. [A Survey on Efficient Vision Transformers: Algorithms, Techniques, and Performance Benchmarking](https://doi.org/10.1109/tpami.2024.3392941)
  - Basis: abstract; retained text characters 994:1152; source `openalex:W4395113676`.
  - Exact quotation: a new metric called Efficient Error Rate has been introduced in order to normalize and compare models' features that affect hardware devices at inference time
  - Support assessment: The quote explicitly states that the abstract introduces Efficient Error Rate to normalize and compare model features affecting hardware at inference time. It also identifies the compared features as parameters, bits, FLOPs, and model size. However, the abstract does not establish that this metric is specific to post-training quantization or provide further evaluation settings.

- **ev-6f89e2371570** — The source addresses general neural-network quantization rather than specifically post-training quantization of vision transformers. [A Survey of Quantization Methods for Efficient Neural Network Inference](https://doi.org/10.1201/9781003162810-13)
  - Basis: abstract; retained text characters 0:118; source `openalex:W3137147200`.
  - Exact quotation: This chapter provides approaches to the problem of quantizing the numerical values in deep Neural Network computations
  - Support assessment: The supplied abstract describes quantization of deep neural-network computations generally—“This chapter provides approaches to the problem of quantizing the numerical values in deep Neural Network computations”—and does not mention post-training quantization or vision transformers. Therefore, it supports the claim that the source is general rather than specifically about post-training quantization methods for vision transformers. No such specific methods can be identified from this abstract.

- **ev-e639692ebf7a** — The abstract reports inconsistency in reduction patterns when backbone capacity changes. [Which Tokens to Use? Investigating Token Reduction in Vision Transformers](https://vbn.aau.dk/da/publications/5447fe07-02f2-4462-a537-31ea9c6a88fc)
  - Basis: abstract; retained text characters 745:844; source `openalex:W4390190626`.
  - Exact quotation: the reduction patterns are generally not consistent when varying the capacity of the backbone model
  - Support assessment: The exact quote states that “the reduction patterns are generally not consistent when varying the capacity of the backbone model,” directly supporting the claim. This is an author-reported limitation from the abstract. However, it concerns token-reduction patterns rather than post-training quantization methods, so it does not provide evidence about quantization specifically.

## Comparisons and synthesis

No checked cross-source comparison is available. Differences in tasks, datasets, hardware, and metrics must be resolved before calling results contradictory.

## Coverage, gaps and uncertainty

- Unresolved: What post-training quantization methods for vision transformers are described in the abstracts?
- Unresolved: What quantization components or strategies do the abstracts report, such as weight, activation, layer-wise, or mixed-precision quantization?
- Addressed within the retrieved evidence: What limitations, constraints, or unresolved issues do the abstracts report?
- Addressed within the retrieved evidence: What evaluation settings or metrics are mentioned in the abstracts, without inferring beyond the reported scope?
- No abstract describes a post-training quantization method specifically for vision transformers.
- No abstract reports quantization components or strategies such as weight quantization, activation quantization, layer-wise quantization, calibration, or mixed precision.
- Reported deployment constraints are general hardware and environmental restrictions, not limitations demonstrated to be specific to post-training quantization.
- No datasets, hardware platforms, bit-widths, accuracy results, or other task-specific evaluation settings are reported.
- The Efficient Error Rate is mentioned, but its use for evaluating post-training quantization of vision transformers is not established in the supplied abstracts.

## Limitations and stopping condition

The supplied abstracts do not provide evidence sufficient to identify post-training quantization methods or quantization strategies for vision transformers. They only report general quantization, general vision-transformer deployment constraints, token-reduction limitations, and a hardware-oriented metric. Stopped at configured rounds/papers or no useful new query; unresolved scope is disclosed.

Searches are bounded and do not establish systematic-review completeness. Metadata is not evidence of a result. Abstracts omit experimental detail. Accessible HTML may omit equations/figures and is read through a bounded window. Source statements remain author-reported. Model support judgments can be wrong; inspect exact quotations and scope before relying on the report.

Limits: `{'max_rounds': 2, 'max_papers': 3, 'results_per_query': 2, 'max_queries': 1, 'max_model_calls': 20, 'max_tokens': 180000, 'max_seconds': 150.0, 'max_http_requests': 8, 'max_download_bytes': 12000000, 'concurrency': 2}`

Usage: `{'model_calls': 15, 'tokens': 14141, 'reserved_tokens': 103622, 'http_requests': 4, 'download_bytes': 108359, 'cache_hits': 0}`

## References and reading depth

- [A Survey on Efficient Vision Transformers: Algorithms, Techniques, and Performance Benchmarking](https://doi.org/10.1109/tpami.2024.3392941) (2024), `openalex:W4395113676`; IDs: `{'openalex': 'W4395113676', 'doi': '10.1109/tpami.2024.3392941', 'pmid': 'https://pubmed.ncbi.nlm.nih.gov/38656856', 'arxiv': '2309.02031', 'arxiv_unversioned': '2309.02031'}`; **abstract**. Reconstructed provider abstract; full paper not read. Analysis read characters 0:1550 of 1550; reading window truncated: False.
- [Which Tokens to Use? Investigating Token Reduction in Vision Transformers](https://vbn.aau.dk/da/publications/5447fe07-02f2-4462-a537-31ea9c6a88fc) (2023), `openalex:W4390190626`; IDs: `{'openalex': 'W4390190626', 'doi': '10.1109/iccvw60793.2023.00085'}`; **abstract**. Reconstructed provider abstract; full paper not read. Analysis read characters 0:1197 of 1197; reading window truncated: False.
- [A Survey of Quantization Methods for Efficient Neural Network Inference](https://doi.org/10.1201/9781003162810-13) (2022), `openalex:W3137147200`; IDs: `{'openalex': 'W3137147200', 'doi': '10.1201/9781003162810-13'}`; **abstract**. Reconstructed provider abstract; full paper not read. Analysis read characters 0:878 of 878; reading window truncated: False.
