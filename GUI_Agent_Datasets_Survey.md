# GUI Agent 开源数据集综合调研

> 调研时间：2026-02-25
> 涵盖范围：Web、Desktop（Windows/macOS/Linux）、Mobile（Android/iOS）、跨平台

---

## 一、Web 相关数据集

### 1. Mind2Web
| 属性 | 详情 |
|------|------|
| **数据量** | 2,000+ 开放式任务，覆盖 137 个网站、31 个领域 |
| **数据形式** | 自然语言指令 + 众包标注的动作序列（点击/输入等），含 HTML 快照 |
| **平台** | Web |
| **发布时间** | 2023 (NeurIPS 2023 Spotlight) |
| **Link** | GitHub: https://github.com/OSU-NLP-Group/Mind2Web / Paper: https://arxiv.org/abs/2306.06070 |

### 2. WebArena
| 属性 | 详情 |
|------|------|
| **数据量** | 812 个长周期任务，基于 4 个自托管真实网站环境（电商、论坛、协作工具、内容管理） |
| **数据形式** | 自然语言指令 + 可交互的真实网站环境 + 功能性评价指标 |
| **平台** | Web |
| **发布时间** | 2023 |
| **Link** | https://webarena.dev/ / GitHub: https://github.com/web-arena-x/webarena |

### 3. VisualWebArena
| 属性 | 详情 |
|------|------|
| **数据量** | 910 个多模态视觉任务，跨 3 个环境（Classifieds、Shopping、Reddit） |
| **数据形式** | 图文混合指令 + 需视觉理解的网页交互任务 |
| **平台** | Web |
| **发布时间** | 2024 |
| **Link** | https://jykoh.com/vwa / GitHub: https://github.com/web-arena-x/visualwebarena |

### 4. WebShop
| 属性 | 详情 |
|------|------|
| **数据量** | 1.18M 真实商品 + 12,087 条众包文本指令 |
| **数据形式** | 模拟电商网站环境，自然语言购物指令 + 搜索/点击动作序列 |
| **平台** | Web |
| **发布时间** | 2022 |
| **Link** | https://webshop-pnlp.github.io/ / GitHub: https://github.com/princeton-nlp/WebShop |

### 5. MiniWoB++
| 属性 | 详情 |
|------|------|
| **数据量** | 100+ 个网页交互小任务（从简单按钮点击到复杂表单填写） |
| **数据形式** | 浏览器中的小型任务环境，支持 Gymnasium API，含程序化奖励信号 |
| **平台** | Web |
| **发布时间** | 2018（持续更新） |
| **Link** | https://miniwob.farama.org/ / Paper: https://paperswithcode.com/dataset/miniwob |

---

## 二、Desktop 相关数据集

### 6. OSWorld
| 属性 | 详情 |
|------|------|
| **数据量** | 369 个真实计算机任务（涵盖 Ubuntu、Windows、macOS） |
| **数据形式** | 可交互的虚拟机环境，含真实 Web 和桌面应用，支持执行级评估 |
| **平台** | Desktop（跨 OS） |
| **发布时间** | 2024 (NeurIPS 2024) |
| **Link** | https://os-world.github.io/ / GitHub: https://github.com/xlang-ai/OSWorld |

### 7. Windows Agent Arena (WAA)
| 属性 | 详情 |
|------|------|
| **数据量** | 154+ 个 Windows 任务（覆盖浏览器、文档编辑器、VS Code、文件管理器等） |
| **数据形式** | Windows 11 虚拟机中的多模态交互任务，截图 + 键鼠操作 |
| **平台** | Windows |
| **发布时间** | 2024 |
| **Link** | https://microsoft.github.io/WindowsAgentArena/ / GitHub: https://github.com/microsoft/WindowsAgentArena |

### 8. AssistGUI
| 属性 | 详情 |
|------|------|
| **数据量** | 100 个精心收集的任务，覆盖 9 个常用桌面软件（After Effects、MS Word 等） |
| **数据形式** | 自然语言任务描述 + 项目文件 + 键鼠操作序列 |
| **平台** | Windows Desktop |
| **发布时间** | 2024 (CVPR 2024) |
| **Link** | Paper: https://arxiv.org/abs/2312.13108 / HuggingFace: https://huggingface.co/papers/2312.13108 |

### 9. OmniACT
| 属性 | 详情 |
|------|------|
| **数据量** | 多样的桌面 + Web 任务，包含屏幕截图和自然语言任务描述 |
| **数据形式** | 屏幕截图 + 自然语言指令 → 可执行 PyAutoGUI 脚本 |
| **平台** | Desktop + Web |
| **发布时间** | 2024 (ECCV 2024) |
| **Link** | Paper: https://arxiv.org/abs/2402.17553 / HuggingFace: https://huggingface.co/papers/2402.17553 |

### 10. GUI-360°
| 属性 | 详情 |
|------|------|
| **数据量** | 1.2M+ 执行动作步骤，数千条完整轨迹 |
| **数据形式** | 全分辨率截图 + 可访问性元数据 + 实例化目标 + 推理 trace + 成功/失败轨迹，支持 GUI grounding、屏幕解析、动作预测 |
| **平台** | Windows 办公应用 |
| **发布时间** | 2025 |
| **Link** | Paper: https://arxiv.org/abs/2511.04307 / HuggingFace 数据可用 |

### 11. UI-Vision
| 属性 | 详情 |
|------|------|
| **数据量** | 覆盖 83 个桌面软件应用，含密集标注 |
| **数据形式** | 截图 + 边界框 + UI 标签 + 动作轨迹（点击/拖拽/键盘输入），支持元素定位、布局定位、动作预测 |
| **平台** | Desktop |
| **发布时间** | 2025 |
| **Link** | Paper: https://arxiv.org/abs/2503.15661 |

---

## 三、Mobile 相关数据集

### 12. AITW (Android in the Wild)
| 属性 | 详情 |
|------|------|
| **数据量** | 715,000 个 episode，30,000 条唯一指令，覆盖 4 个 Android 版本（v10-13）、8 种设备 |
| **数据形式** | 人工演示的设备交互：截图 + 动作（手势/点击/滑动）+ 自然语言指令 |
| **平台** | Android |
| **发布时间** | 2023 (NeurIPS 2023) |
| **Link** | https://research.google/pubs/android-in-the-wild-a-large-scale-dataset-for-android-device-control/ / GitHub: https://github.com/google-research/google-research/tree/master/android_in_the_wild |

### 13. Rico
| 属性 | 详情 |
|------|------|
| **数据量** | 9,300+ 个 Android 应用（27 个类别），66,000+ 个唯一 UI 界面，3M+ UI 元素 |
| **数据形式** | UI 截图 + 视图层级（View Hierarchy）+ 交互 trace + 布局向量 |
| **平台** | Android |
| **发布时间** | 2017（经典数据集，持续被引用） |
| **Link** | https://interactionmining.org/rico |

### 14. AMEX (Android Multi-annotation Expo)
| 属性 | 详情 |
|------|------|
| **数据量** | 104,000+ 张高分辨率截图，覆盖 110 个流行移动应用 |
| **数据形式** | 三层标注：GUI 交互元素定位 + 界面/元素功能描述 + 复杂自然语言指令（平均 13 步/指令）+ 逐步 GUI-动作链 |
| **平台** | Android |
| **发布时间** | 2024 |
| **Link** | Paper: https://arxiv.org/abs/2407.17490 |

### 15. GUIOdyssey (GUI-Odyssey)
| 属性 | 详情 |
|------|------|
| **数据量** | 8,334 个 episode（平均 15.3 步/episode），覆盖 6 种移动设备、212 个应用、1,357 个应用组合 |
| **数据形式** | 跨应用 GUI 导航轨迹 + 每步语义推理标注 |
| **平台** | Mobile |
| **发布时间** | 2024 |
| **Link** | GitHub: https://github.com/OpenGVLab/GUI-Odyssey / Paper: https://arxiv.org/abs/2406.08451 |

### 16. AndroidControl
| 属性 | 详情 |
|------|------|
| **数据量** | 15,283 条演示，14,548 个唯一任务，覆盖 833 个 Android 应用 |
| **数据形式** | 每条任务含高层级 + 低层级的人工指令，支持多维度泛化测试（未见应用/任务/类别） |
| **平台** | Android |
| **发布时间** | 2024 (NeurIPS 2024) |
| **Link** | Paper: https://arxiv.org/abs/2406.03679 |

### 17. AndroidWorld
| 属性 | 详情 |
|------|------|
| **数据量** | 116 个任务，覆盖 20 个真实 Android 应用，支持动态实例化产生数百万种任务变体 |
| **数据形式** | 可交互的 Android 环境 + 动态任务生成 + 基于系统状态的持久奖励信号 |
| **平台** | Android |
| **发布时间** | 2024 (ICLR 2025) |
| **Link** | https://google-research.github.io/android_world/ |

### 18. LlamaTouch
| 属性 | 详情 |
|------|------|
| **数据量** | 移动 UI 自动化任务测试集 |
| **数据形式** | 真实移动环境中的 UI 自动化评估框架，支持可扩展评估 |
| **平台** | Mobile |
| **发布时间** | 2024 |
| **Link** | GitHub: https://github.com/LlamaTouch/LlamaTouch |

---

## 四、GUI Grounding / 视觉定位专用数据集

### 19. ScreenSpot
| 属性 | 详情 |
|------|------|
| **数据量** | 1,200+ 条指令，610 行数据（597 MB） |
| **数据形式** | GUI 截图 + 自然语言指令 + 元素边界框标注（区分文本元素和图标/控件），覆盖 iOS、Android、macOS、Windows、Web |
| **平台** | 跨平台 |
| **发布时间** | 2024 |
| **Link** | HuggingFace: https://huggingface.co/datasets/benwiesel/ScreenSpot / Paper: https://arxiv.org/abs/2401.10935 |

### 20. ScreenSpot-Pro
| 属性 | 详情 |
|------|------|
| **数据量** | 1,590 条数据，23 个专业应用，跨 5 个行业、3 个操作系统 |
| **数据形式** | 高分辨率截图（最高 3840x2160）+ 专家标注（5 年+经验的专业用户） |
| **平台** | Desktop（跨 OS） |
| **发布时间** | 2025 |
| **Link** | HuggingFace: https://huggingface.co/datasets/likaixin/ScreenSpot-Pro / Paper: https://arxiv.org/abs/2504.07981 |

### 21. OS-ATLAS
| 属性 | 详情 |
|------|------|
| **数据量** | 13M+ GUI 元素（迄今最大的开源跨平台 GUI grounding 语料库） |
| **数据形式** | 跨平台 GUI 元素标注，含截图 + 元素坐标 + 功能描述，覆盖 Windows、Linux、macOS、Android、Web |
| **平台** | 跨平台 |
| **发布时间** | 2024 |
| **Link** | https://osatlas.github.io/ / Paper: https://arxiv.org/abs/2410.23218 |

### 22. GroundCUA
| 属性 | 详情 |
|------|------|
| **数据量** | 3.56M 条人工验证标注，56K 张截图，87 个应用 |
| **数据形式** | 密集标注的截图 + 元素级标注，用于训练 GUI grounding 模型 |
| **平台** | 跨平台 |
| **发布时间** | 2025 |
| **Link** | https://groundcua.github.io/ |

### 23. Jedi Dataset
| 属性 | 详情 |
|------|------|
| **数据量** | 4M 条合成样本 |
| **数据形式** | 通过多视角任务解耦合成的 grounding 数据，提升 ScreenSpot-v2/Pro 等评测表现 |
| **平台** | 跨平台 |
| **发布时间** | 2025 |
| **Link** | https://osworld-grounding.github.io/ |

---

## 五、GUI Agent 轨迹数据集

### 24. AgentTrek
| 属性 | 详情 |
|------|------|
| **数据量** | 大规模多模态轨迹数据集（具体量级需参考论文） |
| **数据形式** | 视觉轨迹（截图+动作序列）+ 文本轨迹（HTML 观测+步骤指令），基于网络教程自动合成 |
| **平台** | Web |
| **发布时间** | 2025 (ICLR 2025 Spotlight) |
| **Link** | https://agenttrek.github.io/ / GitHub: https://github.com/xlang-ai/AgentTrek |

### 25. NatureGAIA
| 属性 | 详情 |
|------|------|
| **数据量** | 高质量人工验证轨迹数据集（含多样交互模式和自纠正行为） |
| **数据形式** | 因果路径结构化的复杂任务 + 程序化可验证的原子步骤 + 轨迹数据 |
| **平台** | 跨平台 |
| **发布时间** | 2025 |
| **Link** | Paper: https://arxiv.org/abs/2508.01330 |

### 26. ScaleCUA
| 属性 | 详情 |
|------|------|
| **数据量** | 大规模跨平台数据集，覆盖 6 个操作系统、3 个任务领域 |
| **数据形式** | 跨平台计算机使用轨迹数据 |
| **平台** | 跨平台（6 OS） |
| **发布时间** | 2025 |
| **Link** | GitHub: https://github.com/OpenGVLab/ScaleCUA |

---

## 六、GUI 理解 / QA 数据集

### 27. ScreenQA
| 属性 | 详情 |
|------|------|
| **数据量** | ~86,000 个问答对，~35,000 张截图（基于 Rico 数据集） |
| **数据形式** | 截图 + 问答对，评估屏幕阅读理解能力 |
| **平台** | Mobile (Android) |
| **发布时间** | 2022 |
| **Link** | GitHub: https://github.com/google-research-datasets/screen_qa |

### 28. GUI-Xplore
| 属性 | 详情 |
|------|------|
| **数据量** | 312 个应用，33 个子类别，32,569 个问答对 |
| **数据形式** | 跨应用、跨任务的 QA 对，采用"先探索后推理"的范式 |
| **平台** | Mobile |
| **发布时间** | 2025 (CVPR 2025) |
| **Link** | GitHub: https://github.com/921112343/GUI-Xplore |

### 29. GUI-World
| 属性 | 详情 |
|------|------|
| **数据量** | 12,000+ 个视频，8 种 GUI 导向问题类型 |
| **数据形式** | GUI 操作视频 + 多模态问答（3 种格式），覆盖桌面/移动/XR 共 6 种 GUI 场景，含人工-MLLM 联合标注 |
| **平台** | 跨平台（Desktop + Mobile + XR） |
| **发布时间** | 2024 |
| **Link** | https://gui-world.github.io/ / GitHub: https://github.com/Dongping-Chen/GUI-World |

### 30. MMBench-GUI
| 属性 | 详情 |
|------|------|
| **数据量** | 层次化评估基准，覆盖 Windows、macOS、Linux、iOS、Android、Web |
| **数据形式** | 四层级评估：GUI 内容理解 → 元素定位 → 任务自动化 → 任务协作，引入效率-质量面积（EQA）指标 |
| **平台** | 跨平台 |
| **发布时间** | 2025 |
| **Link** | Paper: https://arxiv.org/abs/2507.19478 |

---

## 七、GUI Agent 训练数据集

### 31. GUIAct
| 属性 | 详情 |
|------|------|
| **数据量** | 约 127,000 行（16.4 GB）/ 另一版本约 1.26M 行（232 GB） |
| **数据形式** | GUI 交互截图 + 动作标注，用于训练 GUI agent 模型 |
| **平台** | Web |
| **发布时间** | 2024 |
| **Link** | HuggingFace: https://huggingface.co/datasets/yongle18297/GUIAct |

### 32. GUICourse
| 属性 | 详情 |
|------|------|
| **数据量** | 多阶段 GUI 训练课程数据 |
| **数据形式** | 分阶段的 GUI 理解和操作训练数据，包含 OCR、grounding 和指令跟随 |
| **平台** | 跨平台 |
| **发布时间** | 2024 |
| **Link** | GitHub: https://github.com/RUCBM/GUICourse |

### 33. GUI-Robust
| 属性 | 详情 |
|------|------|
| **数据量** | 包含 7 类常见异常情况的 GUI 交互数据 |
| **数据形式** | 半自动化构建的异常 GUI 场景数据（比人工标注快 19 倍），测试 agent 鲁棒性 |
| **平台** | 跨平台 |
| **发布时间** | 2025 |
| **Link** | Paper: https://arxiv.org/abs/2506.14477 |

---

## 八、相关综述论文

| 综述 | Link |
|------|------|
| **GUI Agents with Foundation Models: A Comprehensive Survey** | https://arxiv.org/abs/2411.04890 |
| **GUI Agents: A Survey** (ACL Findings 2025) | https://arxiv.org/abs/2412.13501 |

---

## 数据集规模速览表

| 数据集 | 数据规模 | 平台 | 类型 |
|--------|---------|------|------|
| Mind2Web | 2,000+ tasks, 137 websites | Web | Benchmark |
| WebArena | 812 tasks | Web | Benchmark |
| VisualWebArena | 910 tasks | Web | Benchmark |
| WebShop | 1.18M products, 12K instructions | Web | Training+Eval |
| MiniWoB++ | 100+ tasks | Web | Benchmark |
| OSWorld | 369 tasks | Desktop (3 OS) | Benchmark |
| Windows Agent Arena | 154+ tasks | Windows | Benchmark |
| AssistGUI | 100 tasks, 9 apps | Windows | Benchmark |
| OmniACT | Multi-task | Desktop+Web | Benchmark |
| GUI-360° | 1.2M+ action steps | Windows | Training+Eval |
| UI-Vision | 83 apps | Desktop | Benchmark |
| AITW | 715K episodes, 30K instructions | Android | Training+Eval |
| Rico | 9.3K apps, 66K screens, 3M elements | Android | Training+Eval |
| AMEX | 104K+ screenshots, 110 apps | Android | Training+Eval |
| GUIOdyssey | 8,334 episodes, 212 apps | Mobile | Training+Eval |
| AndroidControl | 15,283 demos, 833 apps | Android | Training+Eval |
| AndroidWorld | 116 tasks, 20 apps | Android | Benchmark |
| ScreenSpot | 1,200+ instructions | 跨平台 | Benchmark |
| ScreenSpot-Pro | 1,590 samples, 23 apps | Desktop | Benchmark |
| OS-ATLAS | 13M+ GUI elements | 跨平台 | Training |
| GroundCUA | 3.56M annotations, 56K screenshots | 跨平台 | Training |
| Jedi | 4M samples | 跨平台 | Training |
| AgentTrek | Large-scale trajectories | Web | Training |
| ScaleCUA | Large-scale, 6 OS | 跨平台 | Training+Eval |
| ScreenQA | 86K QA pairs | Mobile | Benchmark |
| GUI-Xplore | 32,569 QA pairs, 312 apps | Mobile | Benchmark |
| GUI-World | 12K+ videos | 跨平台 | Benchmark |
| GUIAct | 127K~1.26M rows | Web | Training |
