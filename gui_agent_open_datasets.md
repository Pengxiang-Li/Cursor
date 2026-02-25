# GUI Agent 开源数据集与 Benchmark 清单

> Last updated: 2026-02-25  
> Source basis: 官方项目页 / 论文页 / 开源仓库 / Hugging Face（与 `gui_agent_open_datasets.csv` 对齐）

## 统计口径说明

- 不同项目对“数据量”的口径可能不同：例如 task 数、episode 数、interaction 数、annotation 数、GUI element 数。
- 表格中的规模字段保留项目常见官方口径；必要时标注 `~` 或 `+` 表示近似/下限。

## 一、核心开源数据集（训练/预训练/监督微调常用）

| Name | Category | Platform | Size / Scale | Data Format | Official Link | Paper / Project |
|---|---|---|---|---|---|---|
| Mind2Web | dataset | web | 2,350 tasks; 137 websites; 31 domains | Natural-language instruction + HTML (raw/clean) + action sequence (CLICK/TYPE/SELECT) | https://huggingface.co/datasets/osunlp/Mind2Web | https://osu-nlp-group.github.io/Mind2Web/ |
| Multimodal-Mind2Web | dataset | web | 14,193 examples (all splits) | Screenshot + HTML + action annotations | https://huggingface.co/datasets/osunlp/Multimodal-Mind2Web | https://github.com/OSU-NLP-Group/Mind2Web |
| WebLINX | dataset | web | 100K interactions; 2,300 expert demonstrations; 150+ websites | Multi-turn dialogue history + screenshot + HTML/DOM + action history | https://huggingface.co/datasets/McGill-NLP/WebLINX | https://mcgill-nlp.github.io/weblinx/ |
| Android in the Wild (AITW) | dataset | mobile-android | 715K episodes; 30K instructions | Android screenshots/trajectories + natural-language goals + actions | https://github.com/google-research/google-research/tree/master/android_in_the_wild | http://crawles.github.io/aitw/ |
| AndroidControl | dataset | mobile-android | 15,283 demonstrations; 833 apps; 14,548 tasks | High-level and step-level instructions + screenshot + accessibility tree + actions | https://proceedings.neurips.cc/paper_files/paper/2024/hash/a79f3ef3b445fd4659f44648f7ea8ffd-Abstract-Datasets_and_Benchmarks_Track.html | https://arxiv.org/abs/2406.03679 |
| RICO | dataset | mobile-android | 66K+ screens; 9.7K apps; ~3M UI elements | UI screenshots + view hierarchy + metadata + traces | https://interactionmining.org/rico | https://dl.acm.org/doi/10.1145/3126594.3126651 |
| RICO-SCA | dataset | mobile-android | ~25,677 screens; ~295,476 command annotations | Screenshot + semantic annotations + bounding boxes + icon/text labels | https://huggingface.co/datasets/rootsautomation/RICO-SCA | https://paperswithcode.com/dataset/ricosca |
| GUI-Odyssey | dataset | mobile-android | 8,334 episodes; 212 apps; 1,357 app combinations | Cross-app task trajectories + action steps + semantic reasoning annotations | https://huggingface.co/datasets/OpenGVLab/GUI-Odyssey | https://github.com/OpenGVLab/GUI-Odyssey |
| ScreenSpot | dataset | cross-platform-web-mobile-desktop | 1,200+ instructions (common citation); HF variant includes 610 rows | Screenshot + grounding instruction + target bbox/point | https://huggingface.co/datasets/benwiesel/ScreenSpot | https://openreview.net/forum?id=KZUH53BnIc |
| ScreenSpot-Pro | dataset | desktop-professional-software | ~1,581 screenshot-instruction pairs; 23 applications; 3 OS | High-resolution screenshots + expert instructions + fine-grained grounding boxes | https://huggingface.co/datasets/likaixin/ScreenSpot-Pro | https://github.com/likaixin2000/ScreenSpot-Pro-GUI-Grounding |
| GroundCUA | dataset | desktop | 3.56M annotations; 56K screenshots; 87 applications | Desktop screenshots + dense JSON annotations (bbox/text/category) | https://huggingface.co/datasets/ServiceNow/GroundCUA | https://groundcua.github.io/ |
| UGround (data release) | dataset | cross-platform-web-mobile-desktop | 10M GUI elements; 1.3M screenshots | Screenshot + referring instruction + grounding box | https://huggingface.co/collections/osunlp/uground-677824fc5823d21267bc9812 | https://osu-nlp-group.github.io/UGround/ |
| OS-Atlas-data | dataset | cross-platform-web-mobile-desktop | 13M+ GUI elements | Screenshot + instruction + normalized bbox across web/mobile/desktop domains | https://huggingface.co/datasets/OS-Copilot/OS-Atlas-data | https://osatlas.github.io/ |
| UI-Vision | dataset-benchmark | desktop | 83 applications; 8.2K+ query-label pairs | Desktop GUI screenshots + UI labels/boxes + action trajectories | https://huggingface.co/datasets/ServiceNow/ui-vision | https://uivision.github.io/ |
| GUI-360 | dataset-benchmark | desktop-windows | 1.2M+ executed action steps; thousands of trajectories | Full-resolution screenshots + accessibility metadata + goals + action/reasoning traces | https://openreview.net/forum?id=JLEneHy8qC | https://arxiv.org/abs/2511.04307 |
| AgentNet (OpenCUA) | dataset | cross-platform-web-mobile-desktop | 3 OS; 200+ applications/websites (officially highlighted coverage) | Human demonstration trajectories + executable action supervision + benchmark tooling | https://github.com/xlang-ai/OpenCUA | https://opencua.xlang.ai/ |

## 二、常用开源 Benchmark（偏评测环境/任务集）

| Name | Category | Platform | Size / Scale | Data Format | Official Link | Paper / Project |
|---|---|---|---|---|---|---|
| WebArena | benchmark | web | 812 tasks | Self-hosted web environments + execution-based task evaluation | https://github.com/web-arena-x/webarena | https://webarena.dev/ |
| VisualWebArena | benchmark | web | 910 tasks | Visual web tasks requiring screenshot understanding + execution-based evaluation | https://github.com/web-arena-x/visualwebarena | http://jykoh.com/vwa |
| OSWorld | benchmark | desktop-cross-os | 369 tasks | Real computer-use tasks in open desktop environments | https://github.com/xlang-ai/OSWorld | http://os-world.github.io/ |
| AndroidWorld | benchmark | mobile-android | 116 tasks across 20 apps | Dynamic Android task generation + autonomous agent evaluation | https://github.com/google-research/android_world | https://google-research.github.io/android_world/ |
| MiniWoB++ | benchmark | web | 100 tasks | Web interaction tasks with programmatic rewards | https://github.com/Farama-Foundation/miniwob-plusplus | https://miniwob.farama.org/ |
