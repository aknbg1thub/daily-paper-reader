# Workflow failure diagnostics

- event: schedule
- sha: 15326bcc45897a092c388d2c2cf3a67275b35b02
- date: 2026-05-27T22:31:22Z
- exit_status: 1

```text
[2026-05-27 22:30:52] [INFO] Supabase BM25 召回窗口：2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 (time_fields=published)
[2026-05-27 22:30:52] [INFO] Supabase BM25 使用命令行指定的 Top K = 30，source=arxiv，输出文件：arxiv_papers_20260527-20260527.bm25.json
::group::Step 2.1 - supabase bm25 recall (arxiv:arxiv_papers_20260527-20260527.bm25.json)
[2026-05-27 22:30:52] [Supabase BM25] batch=1 tag=QC-GENERAL type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:53] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:53] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=QC-GENERAL
[2026-05-27 22:30:53] [Supabase BM25] batch=2 tag=QC-GENERAL type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:54] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:54] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=QC-GENERAL
[2026-05-27 22:30:54] [Supabase BM25] batch=3 tag=QC-GENERAL type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:54] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:54] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=QC-GENERAL
[2026-05-27 22:30:54] [Supabase BM25] batch=4 tag=QC-GENERAL type=intent_query published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:55] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:55] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=QC-GENERAL
[2026-05-27 22:30:55] [Supabase BM25] batch=5 tag=SC-QUBIT-CHIP type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:56] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:56] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SC-QUBIT-CHIP
[2026-05-27 22:30:56] [Supabase BM25] batch=6 tag=SC-QUBIT-CHIP type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:56] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:56] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SC-QUBIT-CHIP
[2026-05-27 22:30:56] [Supabase BM25] batch=7 tag=SC-QUBIT-CHIP type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:57] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:57] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SC-QUBIT-CHIP
[2026-05-27 22:30:57] [Supabase BM25] batch=8 tag=SC-QUBIT-CHIP type=intent_query published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:58] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:58] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SC-QUBIT-CHIP
[2026-05-27 22:30:58] [Supabase BM25] batch=9 tag=TOPO-LAYOUT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:58] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:58] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=TOPO-LAYOUT
[2026-05-27 22:30:58] [Supabase BM25] batch=10 tag=TOPO-LAYOUT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:58] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:58] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=TOPO-LAYOUT
[2026-05-27 22:30:58] [Supabase BM25] batch=11 tag=TOPO-LAYOUT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:30:59] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:30:59] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=TOPO-LAYOUT
[2026-05-27 22:30:59] [Supabase BM25] batch=12 tag=TOPO-LAYOUT type=intent_query published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:00] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:00] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=TOPO-LAYOUT
[2026-05-27 22:31:00] [Supabase BM25] batch=13 tag=EQ-CIRCUIT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:00] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:00] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=EQ-CIRCUIT
[2026-05-27 22:31:00] [Supabase BM25] batch=14 tag=EQ-CIRCUIT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:00] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:00] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=EQ-CIRCUIT
[2026-05-27 22:31:00] [Supabase BM25] batch=15 tag=EQ-CIRCUIT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:01] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:01] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=EQ-CIRCUIT
[2026-05-27 22:31:01] [Supabase BM25] batch=16 tag=EQ-CIRCUIT type=intent_query published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:01] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:01] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=EQ-CIRCUIT
[2026-05-27 22:31:01] [Supabase BM25] batch=17 tag=SIM-ACCEL type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:02] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:02] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SIM-ACCEL
[2026-05-27 22:31:02] [Supabase BM25] batch=18 tag=SIM-ACCEL type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:02] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:02] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SIM-ACCEL
[2026-05-27 22:31:02] [Supabase BM25] batch=19 tag=SIM-ACCEL type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:02] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:02] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SIM-ACCEL
[2026-05-27 22:31:02] [Supabase BM25] batch=20 tag=SIM-ACCEL type=intent_query published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:03] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:03] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=SIM-ACCEL
[2026-05-27 22:31:03] [Supabase BM25] batch=21 tag=CO-OPT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:03] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:03] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=CO-OPT
[2026-05-27 22:31:03] [Supabase BM25] batch=22 tag=CO-OPT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:04] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:04] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=CO-OPT
[2026-05-27 22:31:04] [Supabase BM25] batch=23 tag=CO-OPT type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:04] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:04] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=CO-OPT
[2026-05-27 22:31:04] [Supabase BM25] batch=24 tag=CO-OPT type=intent_query published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:05] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:05] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=CO-OPT
[2026-05-27 22:31:05] [Supabase BM25] batch=25 tag=AI-SCQC-DESIGN type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:05] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:05] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=AI-SCQC-DESIGN
[2026-05-27 22:31:05] [Supabase BM25] batch=26 tag=AI-SCQC-DESIGN type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:05] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:05] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=AI-SCQC-DESIGN
[2026-05-27 22:31:05] [Supabase BM25] batch=27 tag=AI-SCQC-DESIGN type=keyword published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:06] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:06] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=AI-SCQC-DESIGN
[2026-05-27 22:31:06] [Supabase BM25] batch=28 tag=AI-SCQC-DESIGN type=intent_query published_window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 updated_window=N/A time_fields=published
[2026-05-27 22:31:06] [Supabase BM25] depth=0 window=2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 rpc 查询成功：0 条
[2026-05-27 22:31:06] [Supabase BM25] rpc 分片查询成功：0 条（initial_shards=1 success_windows=1 failed_windows=0） | tag=AI-SCQC-DESIGN
[2026-05-27 22:31:06] [WARN] Supabase BM25 未命中（source=arxiv）。
::endgroup::
[2026-05-27 22:31:06] [INFO] 已将带 tag 的论文和每个查询的 top_k 结果写入：/home/runner/work/daily-paper-reader/daily-paper-reader/archive/20260527-20260527/filtered/arxiv_papers_20260527-20260527.bm25.json
[2026-05-27 22:31:06] [INFO] 其中带 tag 的论文数：0
[INFO] Step 2.2 - Embedding: /opt/hostedtoolcache/Python/3.11.15/x64/bin/python /home/runner/work/daily-paper-reader/daily-paper-reader/src/2.2.retrieval_papers_embedding.py --device cpu --batch-size 8 --top-k 30
[2026-05-27 22:31:06] [INFO] Supabase 向量召回窗口：2026-05-27T00:00:00+00:00 ~ 2026-05-28T00:00:00+00:00 (time_fields=published)
[INFO] 正在初始化远程向量服务：BAAI/bge-small-en-v1.5，device=remote
[INFO] 使用远程 embedding 服务：model=BAAI/bge-small-en-v1.5 endpoint=https://embed.zwwen.online/embed timeout=60s device=remote
[INFO] 远程 embedding：model=BAAI/bge-small-en-v1.5 endpoint=https://embed.zwwen.online/embed total=28 batch=8
[WARN] 远程 embedding 请求失败，将自动回退本地模型：HTTPSConnectionPool(host='embed.zwwen.online', port=443): Max retries exceeded with url: /embed (Caused by SSLError(SSLError(1, '[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1016)')))
[WARN] 远程 embedding 不可用，回退本地模型：BAAI/bge-small-en-v1.5 (device=remote)
[INFO] 尝试加载模型（第 1/3 轮）：BAAI/bge-small-en-v1.5（provider=huggingface，device=remote）
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]Loading weights: 100%|██████████| 199/199 [00:00<00:00, 3560.12it/s]
[WARN] 模型加载失败（provider=huggingface，round=1/3）：Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: remote
[INFO] 尝试加载模型（第 1/3 轮）：BAAI/bge-small-en-v1.5（provider=modelscope，device=remote）
Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]Loading weights: 100%|██████████| 199/199 [00:00<00:00, 3427.62it/s]
[WARN] 模型加载失败（provider=modelscope，round=1/3）：Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: remote
[INFO] 重试间隔：1s
[INFO] 尝试加载模型（第 2/3 轮）：BAAI/bge-small-en-v1.5（provider=huggingface，device=remote）
Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]Loading weights: 100%|██████████| 199/199 [00:00<00:00, 3575.98it/s]
[WARN] 模型加载失败（provider=huggingface，round=2/3）：Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: remote
[INFO] 尝试加载模型（第 2/3 轮）：BAAI/bge-small-en-v1.5（provider=modelscope，device=remote）
Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]Loading weights: 100%|██████████| 199/199 [00:00<00:00, 3547.29it/s]
[WARN] 模型加载失败（provider=modelscope，round=2/3）：Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: remote
[INFO] 重试间隔：1s
[INFO] 尝试加载模型（第 3/3 轮）：BAAI/bge-small-en-v1.5（provider=huggingface，device=remote）
Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]Loading weights: 100%|██████████| 199/199 [00:00<00:00, 3530.77it/s]
[WARN] 模型加载失败（provider=huggingface，round=3/3）：Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: remote
[INFO] 尝试加载模型（第 3/3 轮）：BAAI/bge-small-en-v1.5（provider=modelscope，device=remote）
Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]Loading weights: 100%|██████████| 199/199 [00:00<00:00, 3449.98it/s]
[WARN] 模型加载失败（provider=modelscope，round=3/3）：Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: remote
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/connectionpool.py", line 464, in _make_request
    self._validate_conn(conn)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/connectionpool.py", line 1106, in _validate_conn
    conn.connect()
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/connection.py", line 796, in connect
    sock_and_verified = _ssl_wrap_socket_and_match_hostname(
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/connection.py", line 975, in _ssl_wrap_socket_and_match_hostname
    ssl_sock = ssl_wrap_socket(
               ^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/util/ssl_.py", line 433, in ssl_wrap_socket
    ssl_sock = _ssl_wrap_socket_impl(sock, context, tls_in_tls, server_hostname)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/util/ssl_.py", line 477, in _ssl_wrap_socket_impl
    return ssl_context.wrap_socket(sock, server_hostname=server_hostname)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/ssl.py", line 517, in wrap_socket
    return self.sslsocket_class._create(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/ssl.py", line 1104, in _create
    self.do_handshake()
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/ssl.py", line 1382, in do_handshake
    self._sslobj.do_handshake()
ssl.SSLError: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1016)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/connectionpool.py", line 788, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/connectionpool.py", line 488, in _make_request
    raise new_e
urllib3.exceptions.SSLError: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1016)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/requests/adapters.py", line 645, in send
    resp = conn.urlopen(
           ^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/connectionpool.py", line 842, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/urllib3/util/retry.py", line 543, in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='embed.zwwen.online', port=443): Max retries exceeded with url: /embed (Caused by SSLError(SSLError(1, '[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1016)')))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/model_loader.py", line 174, in encode
    response = requests.post(
               ^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/requests/api.py", line 115, in post
    return request("post", url, data=data, json=json, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/requests/sessions.py", line 592, in request
    resp = self.send(prep, **send_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/requests/sessions.py", line 706, in send
    r = adapter.send(request, **kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/requests/adapters.py", line 676, in send
    raise SSLError(e, request=request)
requests.exceptions.SSLError: HTTPSConnectionPool(host='embed.zwwen.online', port=443): Max retries exceeded with url: /embed (Caused by SSLError(SSLError(1, '[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1016)')))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/2.2.retrieval_papers_embedding.py", line 1543, in <module>
    main()
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/2.2.retrieval_papers_embedding.py", line 1242, in main
    cache_stats = hydrate_query_embeddings_from_config(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/2.2.retrieval_papers_embedding.py", line 399, in hydrate_query_embeddings_from_config
    miss_vectors = encode_queries(
                   ^^^^^^^^^^^^^^^
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/filter.py", line 128, in encode_queries
    return model.encode(
           ^^^^^^^^^^^^^
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/model_loader.py", line 221, in encode
    return self._encode_via_local(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/model_loader.py", line 120, in _encode_via_local
    local_model = self._get_local_model()
                  ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/model_loader.py", line 92, in _get_local_model
    self._local_model = _load_local_sentence_transformer(
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/model_loader.py", line 434, in _load_local_sentence_transformer
    raise last_err
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/model_loader.py", line 417, in _load_local_sentence_transformer
    return SentenceTransformer(model_name, device=device)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/sentence_transformers/util/decorators.py", line 41, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/sentence_transformers/sentence_transformer/model.py", line 184, in __init__
    super().__init__(
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/sentence_transformers/base/model.py", line 236, in __init__
    self.to(device)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/torch/nn/modules/module.py", line 1340, in to
    device, dtype, non_blocking, convert_to_format = torch._C._nn._parse_to(
                                                     ^^^^^^^^^^^^^^^^^^^^^^^
RuntimeError: Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: remote
Traceback (most recent call last):
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/main.py", line 946, in <module>
    main()
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/main.py", line 859, in main
    run_step(
  File "/home/runner/work/daily-paper-reader/daily-paper-reader/src/main.py", line 35, in run_step
    subprocess.run(args, check=True, env=env)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/opt/hostedtoolcache/Python/3.11.15/x64/bin/python', '/home/runner/work/daily-paper-reader/daily-paper-reader/src/2.2.retrieval_papers_embedding.py', '--device', 'cpu', '--batch-size', '8', '--top-k', '30']' returned non-zero exit status 1.
```
