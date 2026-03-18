# AI代理指令文档 (AGENTS.md)

| **文档版本** | **修订日期** | **修订人** | **修订说明** |
| :----------- | :----------- | :--------- | :----------- |
| V1.0         | 2026-03-18   | AI架构师   | 初始版本创建 |

## 1. 项目概述

### 1.1 项目背景

**短剧爆款洞察与创意生成平台**是一款面向短视频创作者的"AI决策副驾"。本产品旨在通过AI技术深度解析短视频内容，将抽象的爆款趋势转化为具体的、可复用的创意框架和行动建议，帮助用户告别盲目猜测，实现爆款内容的可复制化生产。

### 1.2 核心价值主张

- **提效**：将用户每周数小时的手动刷视频、找灵感的时间，缩短至分钟级的智能洞察
- **提质**：帮助用户将爆款偶然性转化为方法论，提升内容创作的爆款成功率
- **降噪**：提供"纯净"数据，过滤虚假流量，聚焦于真正有价值的内容信号

### 1.3 技术栈概览

| **层级**     | **技术选型**                                    |
| :----------- | :---------------------------------------------- |
| **前端**     | Vue 3 + Element Plus + ECharts                  |
| **后端**     | Python FastAPI                                  |
| **数据库**   | PostgreSQL 16 + TimescaleDB + Elasticsearch 8.x |
| **消息队列** | RabbitMQ + Celery                               |
| **AI/ML**    | PyTorch 2.5 + Transformers + 智谱AI GLM-4       |
| **多模态**   | 谷歌Gemini Embedding 2 / CLIP                   |
| **部署**     | Docker + Kubernetes                             |
| **监控**     | Prometheus + Grafana + ELK                      |

### 1.4 项目结构

```
short-video-insight-platform/
├── services/                    # 微服务目录
│   ├── user-service/            # 用户服务
│   ├── content-analysis/        # 内容分析服务
│   ├── insight-generator/       # 洞察生成服务
│   ├── data-collector/          # 数据采集服务
│   ├── competitor-monitor/      # 竞品监控服务
│   └── report-service/          # 报表服务
├── frontend/                    # 前端项目
├── common/                      # 公共库
├── deploy/                      # 部署相关
└── docs/                        # 文档
```

## 2. 开发规范

### 2.1 通用规范

#### 2.1.1 版本控制 (Git)

- **分支策略**：采用Git Flow
  - `main`: 生产分支，仅接受来自`release`和`hotfix`的合并
  - `develop`: 开发主分支，功能分支合并至此
  - `feature/*`: 功能分支，从`develop`创建
  - `release/*`: 发布分支，从`develop`创建
  - `hotfix/*`: 紧急修复分支，从`main`创建

- **提交信息格式**：
  ```
  <type>(<scope>): <subject>
  
  <body>
  
  <footer>
  ```
  - type: feat/fix/docs/style/refactor/test/chore
  - scope: 影响范围（如user-service, frontend）
  - subject: 简短描述（50字符以内）
  - body: 详细描述（可选）
  - footer: 关闭issue（如Closes #123）

- **示例**：
  ```
  feat(content-analysis): 添加多模态视频嵌入功能
  
  - 集成Gemini Embedding 2模型
  - 实现视频帧抽取与向量化
  - 添加向量相似度检索接口
  
  Closes #45
  ```

#### 2.1.2 文档规范

- **代码注释**：
  - 所有公共函数/方法必须包含文档字符串
  - 复杂逻辑必须添加行内注释
  - 使用中文注释，便于团队理解

- **API文档**：
  - 使用OpenAPI 3.0规范
  - FastAPI自动生成Swagger UI
  - 所有接口必须包含请求/响应示例

- **README要求**：
  - 每个服务模块必须有独立的README.md
  - 包含：模块说明、启动方式、依赖环境、配置说明

### 2.2 Python后端规范

#### 2.2.1 代码风格

- **遵循PEP 8**：使用Black自动格式化（行宽88字符）
- **类型注解**：所有函数必须包含类型注解
  ```python
  from typing import Optional, List, Dict
  
  def process_video(
      video_url: str,
      platform: str,
      options: Optional[Dict] = None
  ) -> Dict[str, Any]:
      """
      处理视频，提取多模态特征。
      
      Args:
          video_url: 视频URL
          platform: 平台名称（douyin/bilibili/xiaohongshu）
          options: 处理选项配置
          
      Returns:
          包含ASR、OCR、嵌入向量的结果字典
          
      Raises:
          ValueError: 当视频URL无效时
          ProcessingError: 当处理失败时
      """
      pass
  ```

- **导入顺序**：
  1. 标准库
  2. 第三方库
  3. 本地模块
  每组之间空一行

- **命名规范**：
  - 类名：`CamelCase`
  - 函数/变量：`snake_case`
  - 常量：`UPPER_SNAKE_CASE`
  - 私有成员：`_leading_underscore`

#### 2.2.2 项目结构规范（每个服务）

```
service-name/
├── app/
│   ├── api/              # API路由
│   │   ├── v1/           # API版本
│   │   │   ├── endpoints/
│   │   │   └── __init__.py
│   │   └── deps.py       # 依赖注入
│   ├── core/             # 核心配置
│   │   ├── config.py     # 配置管理
│   │   └── security.py   # 安全相关
│   ├── models/           # 数据模型
│   │   ├── domain/       # 领域模型
│   │   └── schemas/      # Pydantic模型
│   ├── services/         # 业务逻辑
│   ├── tasks/            # Celery任务
│   ├── utils/            # 工具函数
│   └── main.py           # 应用入口
├── tests/                # 测试
├── requirements/         # 依赖管理
├── Dockerfile
└── README.md
```

#### 2.2.3 异常处理

- **自定义异常**：继承`Exception`基类
  ```python
  class VideoProcessingError(Exception):
      """视频处理相关异常"""
      def __init__(self, message: str, video_id: Optional[str] = None):
          self.message = message
          self.video_id = video_id
          super().__init__(self.message)
  ```

- **统一异常处理**：在FastAPI中注册全局异常处理器
  ```python
  @app.exception_handler(VideoProcessingError)
  async def video_processing_exception_handler(
      request: Request,
      exc: VideoProcessingError
  ):
      return JSONResponse(
          status_code=400,
          content={
              "code": "VIDEO_PROCESSING_ERROR",
              "message": exc.message,
              "video_id": exc.video_id
          }
      )
  ```

### 2.3 前端规范

#### 2.3.1 Vue 3 规范

- **组合式API**：统一使用Composition API
  ```vue
  <script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  
  interface Props {
    videoId: string
  }
  
  const props = defineProps<Props>()
  const emit = defineEmits<{
    (e: 'analyzed', result: object): void
  }>()
  
  const loading = ref(false)
  const analysisResult = computed(() => {...})
  
  onMounted(() => {
    fetchAnalysis()
  })
  
  const fetchAnalysis = async () => {...}
  </script>
  ```

- **组件命名**：多单词，PascalCase
  - `VideoAnalysisReport.vue`
  - `TrendChart.vue`

- **Props定义**：必须包含类型、默认值、验证
  ```typescript
  interface Props {
    title: string
    items?: Array<{ id: string; name: string }>
    showFooter?: boolean
  }
  
  withDefaults(defineProps<Props>(), {
    items: () => [],
    showFooter: false
  })
  ```

#### 2.3.2 状态管理

- 使用Pinia进行状态管理
- 按模块拆分store
  ```typescript
  // stores/video.ts
  export const useVideoStore = defineStore('video', {
    state: () => ({
      currentVideo: null,
      analysisHistory: []
    }),
    actions: {
      async fetchVideo(id: string) {...}
    },
    getters: {
      hasAnalysis: (state) => !!state.currentVideo?.analysis
    }
  })
  ```

### 2.4 数据库规范

#### 2.4.1 SQL规范

- **表名**：复数形式，小写+下划线（`videos`, `video_insights`）
- **主键**：统一使用`id BIGSERIAL PRIMARY KEY`
- **外键**：`表名_singular_id`（`video_id`, `user_id`）
- **时间字段**：`created_at`/`updated_at`使用`TIMESTAMPTZ`
- **索引命名**：`idx_表名_字段名`

#### 2.4.2 迁移规范

- 所有表结构变更必须通过迁移脚本
- 迁移文件命名：`YYYYMMDD_HHMMSS_description.sql`
- 必须包含回滚脚本（`-- +goose Down`）

## 3. 测试要求

### 3.1 测试覆盖率要求

| **层级**       | **覆盖率要求** | **关键测试点**                    |
| :------------- | :------------- | :-------------------------------- |
| **单元测试**   | ≥85%           | 工具函数、服务层逻辑、数据模型    |
| **集成测试**   | ≥70%           | API接口、数据库交互、外部服务调用 |
| **端到端测试** | 核心流程       | 用户注册、视频分析、报告生成      |

### 3.2 Python测试规范

#### 3.2.1 测试框架

- 使用`pytest`作为测试框架
- 使用`pytest-asyncio`测试异步代码
- 使用`pytest-cov`统计覆盖率

#### 3.2.2 测试文件结构

```
tests/
├── conftest.py           # 共享fixtures
├── unit/                 # 单元测试
│   ├── test_utils.py
│   └── test_models.py
├── integration/          # 集成测试
│   ├── test_api/
│   └── test_db/
└── fixtures/            # 测试数据
    ├── video_data.json
    └── mock_responses/
```

#### 3.2.3 测试示例

```python
# tests/unit/test_video_processor.py
import pytest
from unittest.mock import Mock, patch
from app.services.video_processor import VideoProcessor

class TestVideoProcessor:
    @pytest.fixture
    def processor(self):
        return VideoProcessor()
    
    @pytest.mark.asyncio
    async def test_extract_keyframes_success(self, processor, sample_video):
        """测试关键帧抽取功能"""
        # Arrange
        video_url = "https://example.com/video.mp4"
        
        # Act
        frames = await processor.extract_keyframes(video_url)
        
        # Assert
        assert len(frames) > 0
        assert all(frame.endswith('.jpg') for frame in frames)
    
    @pytest.mark.asyncio
    async def test_extract_keyframes_invalid_url(self, processor):
        """测试无效URL处理"""
        with pytest.raises(ValueError, match="无效的视频URL"):
            await processor.extract_keyframes("invalid_url")
```

### 3.3 前端测试规范

#### 3.3.1 测试工具

- Vitest + Vue Test Utils
- Cypress for E2E测试

#### 3.3.2 测试示例

```typescript
// tests/unit/VideoCard.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import VideoCard from '@/components/VideoCard.vue'

describe('VideoCard', () => {
  it('正确渲染视频信息', () => {
    const wrapper = mount(VideoCard, {
      props: {
        video: {
          id: '123',
          title: '测试视频',
          playCount: 10000
        }
      }
    })
    
    expect(wrapper.find('.title').text()).toBe('测试视频')
    expect(wrapper.find('.play-count').text()).toBe('1万')
  })
  
  it('点击触发analyze事件', async () => {
    const wrapper = mount(VideoCard, {
      props: {
        video: { id: '123', title: '测试' }
      }
    })
    
    await wrapper.find('.analyze-btn').trigger('click')
    expect(wrapper.emitted('analyze')).toBeTruthy()
    expect(wrapper.emitted('analyze')[0]).toEqual(['123'])
  })
})
```

### 3.4 性能测试要求

- **API响应时间**：95%的请求<500ms
- **并发支持**：支持1000用户同时在线
- **数据更新延迟**：核心数据<30分钟，预警数据<5分钟
- **使用工具**：Locust进行压力测试，每分钟记录性能指标

## 4. 代码风格

### 4.1 Python代码风格（详细）

#### 4.1.1 命名规范速查表

| **类型**  | **规范**                   | **示例**             |
| :-------- | :------------------------- | :------------------- |
| 包名      | 小写，短横线分隔（项目级） | `content-analysis`   |
| 模块名    | 小写，下划线分隔           | `video_processor.py` |
| 类名      | PascalCase                 | `VideoProcessor`     |
| 函数/方法 | snake_case                 | `process_video()`    |
| 变量      | snake_case                 | `video_url`          |
| 常量      | UPPER_SNAKE_CASE           | `MAX_RETRY_COUNT`    |
| 私有成员  | _leading_underscore        | `_internal_cache`    |

#### 4.1.2 代码格式示例

```python
"""
视频处理模块，提供视频下载、帧抽取、特征提取等功能。
"""

from typing import Optional, List, Dict, Any
import asyncio
from pathlib import Path

import aiohttp
from loguru import logger

from app.core.config import settings
from app.models.schemas import VideoFrame
from app.utils.exceptions import VideoDownloadError


class VideoProcessor:
    """
    视频处理器，负责视频的下载、关键帧抽取和多模态特征提取。
    
    Attributes:
        temp_dir: 临时文件存储目录
        max_frames: 最大抽取帧数
    """
    
    def __init__(
        self,
        temp_dir: Path = Path("/tmp/videos"),
        max_frames: int = 30
    ):
        """
        初始化视频处理器。
        
        Args:
            temp_dir: 临时文件存储目录
            max_frames: 最大抽取帧数，默认30帧
        """
        self.temp_dir = temp_dir
        self.max_frames = max_frames
        self._session: Optional[aiohttp.ClientSession] = None
        
        # 确保临时目录存在
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._session:
            await self._session.close()
    
    async def download_video(self, url: str) -> Path:
        """
        下载视频到临时目录。
        
        Args:
            url: 视频URL
            
        Returns:
            下载后的视频文件路径
            
        Raises:
            VideoDownloadError: 下载失败时抛出
        """
        logger.info(f"开始下载视频: {url}")
        
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        try:
            async with self._session.get(url) as response:
                if response.status != 200:
                    raise VideoDownloadError(
                        f"下载失败，HTTP状态码: {response.status}",
                        url=url
                    )
                
                # 生成临时文件名
                video_path = self.temp_dir / f"video_{hash(url)}.mp4"
                
                # 写入文件
                with open(video_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                logger.success(f"视频下载完成: {video_path}")
                return video_path
                
        except aiohttp.ClientError as e:
            raise VideoDownloadError(
                f"网络请求异常: {str(e)}",
                url=url
            ) from e
    
    async def extract_keyframes(
        self,
        video_path: Path,
        interval: float = 1.0
    ) -> List[VideoFrame]:
        """
        从视频中抽取关键帧。
        
        Args:
            video_path: 视频文件路径
            interval: 抽取间隔（秒）
            
        Returns:
            关键帧列表，每个帧包含时间戳和图片路径
        """
        # 使用FFmpeg抽取帧
        # 实际实现会调用subprocess执行FFmpeg命令
        frames = []
        
        # TODO: 实现帧抽取逻辑
        
        return frames
```

### 4.2 TypeScript/Vue代码风格

#### 4.2.1 命名规范

| **类型**    | **规范**       | **示例**                  |
| :---------- | :------------- | :------------------------ |
| 组件名      | PascalCase     | `VideoAnalysisReport.vue` |
| 组合式函数  | useCamelCase   | `useVideoAnalysis()`      |
| Pinia store | useCamelCase   | `useVideoStore()`         |
| 接口        | IPascalCase    | `IVideoAnalysis`          |
| 类型        | TPascalCase    | `TAnalysisResult`         |
| 枚举        | EnumPascalCase | `VideoPlatform`           |

#### 4.2.2 代码格式示例

```typescript
// types/video.types.ts
/**
 * 视频平台枚举
 */
export enum VideoPlatform {
  DOUYIN = 'douyin',
  BILIBILI = 'bilibili',
  XIAOHONGSHU = 'xiaohongshu'
}

/**
 * 视频分析结果接口
 */
export interface IVideoAnalysis {
  /** 视频ID */
  videoId: string;
  /** 黄金3秒文案 */
  hook3s: string;
  /** 脚本结构类型 */
  structureType: 'challenge-solution' | 'what-why-how' | 'story';
  /** 核心关键词 */
  keywords: string[];
  /** 情感得分 (-1 到 1) */
  sentimentScore: number;
}

/**
 * 视频分析状态
 */
export type TAnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed';

// composables/useVideoAnalysis.ts
import { ref, computed } from 'vue'
import { useVideoStore } from '@/stores/video'
import type { IVideoAnalysis, TAnalysisStatus } from '@/types/video.types'

/**
 * 视频分析组合式函数
 * @param videoId - 视频ID
 * @returns 分析状态和方法
 */
export function useVideoAnalysis(videoId: string) {
  const store = useVideoStore()
  
  // 响应式状态
  const analysis = ref<IVideoAnalysis | null>(null)
  const status = ref<TAnalysisStatus>('pending')
  const error = ref<Error | null>(null)
  
  // 计算属性
  const isLoading = computed(() => status.value === 'processing')
  const hasError = computed(() => error.value !== null)
  
  /**
   * 获取视频分析结果
   */
  const fetchAnalysis = async () => {
    status.value = 'processing'
    error.value = null
    
    try {
      analysis.value = await store.fetchAnalysis(videoId)
      status.value = 'completed'
    } catch (e) {
      error.value = e as Error
      status.value = 'failed'
      console.error('分析失败:', e)
    }
  }
  
  /**
   * 重置分析状态
   */
  const reset = () => {
    analysis.value = null
    status.value = 'pending'
    error.value = null
  }
  
  return {
    // 状态
    analysis,
    status,
    error,
    isLoading,
    hasError,
    // 方法
    fetchAnalysis,
    reset
  }
}
```

### 4.3 日志规范

#### 4.3.1 日志级别定义

| **级别**     | **使用场景**           | **示例**                      |
| :----------- | :--------------------- | :---------------------------- |
| **DEBUG**    | 开发调试信息           | "抽取到15个关键帧，耗时2.3秒" |
| **INFO**     | 正常业务流程           | "用户[123]开始分析视频[456]"  |
| **WARNING**  | 潜在问题，不影响运行   | "视频下载重试第2次，URL: xxx" |
| **ERROR**    | 错误，但服务可继续     | "视频处理失败，video_id: 456" |
| **CRITICAL** | 严重错误，服务可能中断 | "数据库连接丢失"              |

#### 4.3.2 日志格式

```
[时间] [级别] [模块] [请求ID] - 消息

示例：
[2026-03-18 10:30:25] [INFO] [content-analysis] [req-abc123] - 开始分析视频: 123456
```

## 5. 注意事项

### 5.1 数据合规与安全

#### 5.1.1 数据采集红线
- ❌ **严禁**爬取需要登录才能访问的内容
- ❌ **严禁**使用模拟登录、破解验证码等技术手段
- ❌ **严禁**存储用户隐私信息（手机号、身份证等）
- ❌ **严禁**超过平台API限频要求
- ✅ **必须**遵守各平台Robots协议
- ✅ **必须**对采集数据进行脱敏处理

#### 5.1.2 数据存储安全
- 用户密码必须使用bcrypt加盐哈希存储
- 敏感配置信息（API密钥、数据库密码）必须使用环境变量或K8s Secrets
- 所有个人可识别信息（PII）必须加密存储
- 数据库备份必须加密

#### 5.1.3 API安全规范
```python
# 每个API必须包含：
- JWT认证（除登录/注册外）
- 速率限制（防止滥用）
- 输入验证（防止注入）
- 输出过滤（防止数据泄露）
- CORS配置（仅允许白名单域名）

# 示例：速率限制装饰器
@router.get("/videos/{video_id}")
@limiter.limit("100/minute")  # 每分钟最多100次
async def get_video(
    video_id: str,
    current_user: User = Depends(get_current_user)  # JWT认证
):
    # 输入验证
    if not video_id.isalnum():
        raise HTTPException(status_code=400, detail="无效的视频ID")
    
    # 业务逻辑
    video = await video_service.get_video(video_id)
    
    # 输出过滤（不返回内部字段）
    return VideoResponse.from_orm(video)
```

### 5.2 AI模型使用注意事项

#### 5.2.1 大模型调用规范
- 所有AI调用必须**异步执行**，避免阻塞主线程
- 设置合理的**超时时间**（默认30秒）
- 实现**降级策略**（AI服务不可用时返回基础分析）
- 缓存重复请求结果（相同视频24小时内不重复分析）

```python
async def get_ai_insights(video_id: str) -> Dict:
    """带缓存和降级的AI分析"""
    
    # 1. 检查缓存
    cached = await redis.get(f"ai_insights:{video_id}")
    if cached:
        return json.loads(cached)
    
    try:
        # 2. 调用AI服务（带超时）
        async with timeout(30):
            result = await ai_service.analyze(video_id)
        
        # 3. 缓存结果
        await redis.setex(
            f"ai_insights:{video_id}",
            86400,  # 缓存24小时
            json.dumps(result)
        )
        return result
        
    except asyncio.TimeoutError:
        # 4. 降级：返回基础分析
        logger.warning(f"AI分析超时，使用降级方案: {video_id}")
        return await get_basic_analysis(video_id)
    
    except Exception as e:
        # 5. 错误处理
        logger.error(f"AI分析失败: {e}")
        raise AIServiceUnavailableError("AI服务暂时不可用")
```

#### 5.2.2 提示词管理
- 所有提示词模板必须存储在独立文件
- 提示词需要版本控制
- 生产环境提示词必须经过A/B测试

```
services/insight-generator/prompt_templates/
├── v1/
│   ├── hook_analysis.txt      # 黄金3秒分析
│   ├── structure_analysis.txt # 脚本结构分析
│   └── trend_summary.txt      # 趋势总结
├── v2/
│   └── ... (优化版本)
└── prompts_config.yaml        # 提示词配置
```

### 5.3 性能优化要点

#### 5.3.1 数据库优化
- 所有查询必须走索引（定期检查慢查询日志）
- 大批量数据操作使用批处理
- 复杂统计查询使用物化视图或预计算表

```python
# 错误示范：N+1查询
videos = await db.query(Video).all()
for video in videos:
    insights = await db.query(Insights).filter(video_id=video.id).first()

# 正确示范：使用连接查询或预加载
videos = await db.query(Video).options(
    joinedload(Video.insights)
).all()
```

#### 5.3.2 缓存策略
- **一级缓存**（本地内存）：热点数据，过期时间<5分钟
- **二级缓存**（Redis）：业务数据，过期时间5分钟-24小时
- **三级缓存**（数据库）：持久化存储

| **数据类型** | **缓存位置** | **过期时间** | **更新策略** |
| :----------- | :----------- | :----------- | :----------- |
| 用户会话     | Redis        | 30分钟       | 每次访问刷新 |
| 视频基础信息 | Redis        | 1小时        | 写入时更新   |
| AI分析结果   | Redis        | 24小时       | 固定过期     |
| 趋势报告     | Redis        | 1小时        | 定时生成     |
| 热门榜单     | 本地内存     | 5分钟        | 定时刷新     |

### 5.4 错误处理与监控

#### 5.4.1 错误码规范
```
# 错误码格式：A-BB-CCC
# A: 错误级别 (1-系统级, 2-业务级, 3-外部服务)
# BB: 模块编码
# CCC: 具体错误

示例：
1001 - 数据库连接失败
2001 - 用户认证失败
3001 - 视频下载失败
```

#### 5.4.2 必须监控的指标
- **业务指标**：日活用户、分析请求量、爆款预测准确率
- **性能指标**：API响应时间、AI处理耗时、数据库连接数
- **资源指标**：CPU/内存使用率、磁盘IO、网络带宽
- **错误指标**：各接口错误率、AI服务可用性、数据采集成功率

#### 5.4.3 告警阈值
```
- P0（立即处理）：服务宕机、大量500错误、数据库连接失败
- P1（工作时间处理）：错误率>5%、响应时间>2秒、AI服务超时率>10%
- P2（观察处理）：错误率>1%、缓存命中率<80%
```

### 5.5 部署与发布注意事项

#### 5.5.1 环境隔离
- **开发环境**（dev）：开发人员自用，可随时重启
- **测试环境**（staging）：与生产环境配置相同，用于测试
- **生产环境**（prod）：正式环境，严格权限控制

#### 5.5.2 发布流程
1. **代码审查**：至少1人Review，核心模块2人
2. **自动化测试**：所有测试通过
3. **构建镜像**：版本号必须遵循语义化版本
4. **灰度发布**：先1%流量，逐步扩大到100%
5. **回滚预案**：发布失败能在5分钟内回滚

#### 5.5.3 配置管理
- 所有配置必须环境隔离
- 敏感信息使用K8s Secrets
- 配置变更必须记录审计日志

```yaml
# config.yaml 示例
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  username: ${DB_USER}
  password: ${DB_PASSWORD}  # 使用环境变量注入

redis:
  hosts: 
    - ${REDIS_HOST_1}
    - ${REDIS_HOST_2}
  
ai_services:
  glm4:
    api_key: ${GLM4_API_KEY}  # 敏感信息
    timeout: 30
```

**最后更新**：2026-03-18  
**文档维护者**：AI架构团队  

*本文档将随着项目进展持续更新，请定期查看变更记录。*