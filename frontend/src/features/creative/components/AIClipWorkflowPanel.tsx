import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Collapse,
  Descriptions,
  Empty,
  Flex,
  Grid,
  Input,
  List,
  Progress,
  Row,
  Slider,
  Space,
  Steps,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  AudioOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  PictureOutlined,
  PlayCircleOutlined,
  ScissorOutlined,
  SyncOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons'

import type {
  ClipResultResponse,
  CreativeAiClipWorkflowResponse,
  VideoInfoResponse,
} from '@/api'
import {
  useAddAudio,
  useAddCover,
  useDetectHighlights,
  useFullPipeline,
  useSmartClip,
  useVideoInfo,
} from '@/hooks'

import { useSubmitAiClipWorkflow } from '../hooks/useCreativeWorkflow'

const { Paragraph, Text, Title } = Typography
const { useBreakpoint } = Grid

interface HighlightSegment {
  start: number
  end: number
  reason: string
}

interface CreativeWorkflowContext {
  creativeId: number
  creativeTitle?: string | null
  sourceVersionId?: number | null
  sourceVersionLabel?: string
  onSubmitted?: (response: CreativeAiClipWorkflowResponse | undefined) => void
}

interface AIClipWorkflowPanelProps {
  creativeContext?: CreativeWorkflowContext | null
}

const operationLabelMap: Record<string, string> = {
  smart_clip: '智能剪辑',
  add_audio: '添加背景音',
  add_cover: '添加封面',
  full_pipeline: '完整流程',
}

const formatTime = (seconds?: number | null): string => {
  if (!seconds || Number.isNaN(seconds) || seconds < 0) {
    return '00:00'
  }

  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatSize = (bytes?: number | null): string => {
  if (!bytes || bytes <= 0) {
    return '-'
  }

  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / (1024 ** index)).toFixed(index === 0 ? 0 : 2)} ${units[index]}`
}

const buildOutputPath = (videoPath: string, outputDir: string, suffix: string) => {
  const timestamp = Date.now()
  const trimmedVideoPath = videoPath.trim()
  const trimmedOutputDir = outputDir.trim().replace(/[\\/]+$/, '')

  if (trimmedOutputDir) {
    return `${trimmedOutputDir}/${suffix}_${timestamp}.mp4`
  }

  if (/\.[^.]+$/.test(trimmedVideoPath)) {
    return trimmedVideoPath.replace(/\.[^.]+$/, `_${suffix}_${timestamp}.mp4`)
  }

  return `${trimmedVideoPath}_${suffix}_${timestamp}.mp4`
}

const normalizeSegments = (value: unknown): HighlightSegment[] => {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null
      }

      const candidate = item as Record<string, unknown>
      const start = Number(candidate.start)
      const end = Number(candidate.end)
      const reason = typeof candidate.reason === 'string' ? candidate.reason : '未标注原因'

      if (Number.isNaN(start) || Number.isNaN(end)) {
        return null
      }

      return { start, end, reason }
    })
    .filter((item): item is HighlightSegment => item !== null)
}

export default function AIClipWorkflowPanel({ creativeContext }: AIClipWorkflowPanelProps) {
  const screens = useBreakpoint()
  const [videoPath, setVideoPath] = useState('')
  const [videoInfo, setVideoInfo] = useState<VideoInfoResponse | null>(null)
  const [segments, setSegments] = useState<HighlightSegment[]>([])
  const [targetDuration, setTargetDuration] = useState(60)
  const [audioPath, setAudioPath] = useState('')
  const [audioVolume, setAudioVolume] = useState(0.3)
  const [coverPath, setCoverPath] = useState('')
  const [outputDir, setOutputDir] = useState('')
  const [outputPath, setOutputPath] = useState('')
  const [progress, setProgress] = useState(0)
  const [workflowTitle, setWorkflowTitle] = useState('')
  const [lastOperation, setLastOperation] = useState<string | null>(null)

  const videoInfoMutation = useVideoInfo()
  const detectHighlightsMutation = useDetectHighlights()
  const smartClipMutation = useSmartClip()
  const addAudioMutation = useAddAudio()
  const addCoverMutation = useAddCover()
  const fullPipelineMutation = useFullPipeline()
  const submitWorkflowMutation = useSubmitAiClipWorkflow(creativeContext?.creativeId)

  const loadingInfo = videoInfoMutation.isPending || detectHighlightsMutation.isPending
  const processing = smartClipMutation.isPending || addAudioMutation.isPending || addCoverMutation.isPending || fullPipelineMutation.isPending
  const canSubmitWorkflow = Boolean(creativeContext?.sourceVersionId && outputPath.trim())
  const hasOptionalEnhancements = Boolean(audioPath.trim() || coverPath.trim())
  const hasAdvancedOverrides = Boolean(outputDir.trim() || outputPath.trim())

  const totalSegmentDuration = useMemo(
    () => segments.reduce((total, segment) => total + Math.max(segment.end - segment.start, 0), 0),
    [segments],
  )

  const currentStep = useMemo(() => {
    if (outputPath.trim()) {
      return 3
    }

    if (segments.length > 0 || hasOptionalEnhancements || hasAdvancedOverrides || targetDuration !== 60) {
      return 2
    }

    if (videoPath.trim()) {
      return 1
    }

    return 0
  }, [hasAdvancedOverrides, hasOptionalEnhancements, outputPath, segments.length, targetDuration, videoPath])

  useEffect(() => {
    if (!creativeContext) {
      return
    }

    setWorkflowTitle(
      creativeContext.creativeTitle?.trim()
        ? `${creativeContext.creativeTitle} AIClip 版本`
        : 'AIClip 再创作版本',
    )
  }, [creativeContext?.creativeId, creativeContext?.creativeTitle])

  const ensureVideoPath = () => {
    if (!videoPath.trim()) {
      message.warning('请先填写源视频路径')
      return false
    }

    return true
  }

  const resolveOutputPath = (suffix: string) => outputPath.trim() || buildOutputPath(videoPath, outputDir, suffix)

  const applyClipResult = (
    response: ClipResultResponse | null | undefined,
    nextOutputPath: string,
    operation: string,
    successMessage: string,
  ) => {
    if (response?.success) {
      setOutputPath(response.output_path?.trim() || nextOutputPath)
      setLastOperation(operation)
      message.success(successMessage)
      return
    }

    message.error(response?.error || '处理失败')
  }

  const handleGetVideoInfo = async () => {
    if (!ensureVideoPath()) {
      return
    }

    try {
      const response = await videoInfoMutation.mutateAsync({ video_path: videoPath.trim() })
      setVideoInfo(response)
      message.success('已获取视频信息')
    } catch {
      setVideoInfo(null)
      message.error('获取视频信息失败')
    }
  }

  const handleDetectHighlights = async () => {
    if (!ensureVideoPath()) {
      return
    }

    try {
      const response = await detectHighlightsMutation.mutateAsync({ video_path: videoPath.trim() })
      const nextSegments = normalizeSegments(response.segments)
      setSegments(nextSegments)
      message.success(`已识别 ${nextSegments.length} 个高光片段`)
    } catch {
      message.error('高光识别失败')
    }
  }

  const handleSmartClip = async () => {
    if (!ensureVideoPath()) {
      return
    }

    if (segments.length === 0) {
      message.warning('请先识别高光片段')
      return
    }

    const nextOutputPath = resolveOutputPath('smart_clip')

    try {
      setProgress(20)
      const response = await smartClipMutation.mutateAsync({
        video_path: videoPath.trim(),
        segments,
        output_path: nextOutputPath,
        target_duration: targetDuration,
      })
      setProgress(100)
      applyClipResult(response as ClipResultResponse, nextOutputPath, 'smart_clip', '智能剪辑完成')
    } catch {
      message.error('智能剪辑失败')
    } finally {
      setProgress(0)
    }
  }

  const handleAddAudio = async () => {
    if (!ensureVideoPath()) {
      return
    }

    if (!audioPath.trim()) {
      message.warning('请填写背景音频路径')
      return
    }

    const nextOutputPath = resolveOutputPath('audio_mix')

    try {
      setProgress(25)
      const response = await addAudioMutation.mutateAsync({
        video_path: videoPath.trim(),
        audio_path: audioPath.trim(),
        output_path: nextOutputPath,
        volume: audioVolume,
      })
      setProgress(100)
      applyClipResult(response as ClipResultResponse, nextOutputPath, 'add_audio', '背景音已加入')
    } catch {
      message.error('添加背景音失败')
    } finally {
      setProgress(0)
    }
  }

  const handleAddCover = async () => {
    if (!ensureVideoPath()) {
      return
    }

    if (!coverPath.trim()) {
      message.warning('请填写封面路径')
      return
    }

    const nextOutputPath = resolveOutputPath('cover_mix')

    try {
      setProgress(25)
      const response = await addCoverMutation.mutateAsync({
        video_path: videoPath.trim(),
        cover_path: coverPath.trim(),
        output_path: nextOutputPath,
      })
      setProgress(100)
      applyClipResult(response as ClipResultResponse, nextOutputPath, 'add_cover', '封面已加入')
    } catch {
      message.error('添加封面失败')
    } finally {
      setProgress(0)
    }
  }

  const handleFullPipeline = async () => {
    if (!ensureVideoPath()) {
      return
    }

    try {
      setProgress(15)
      const response = await fullPipelineMutation.mutateAsync({
        video_path: videoPath.trim(),
        audio_path: audioPath.trim() || undefined,
        cover_path: coverPath.trim() || undefined,
        target_duration: targetDuration,
        output_dir: outputDir.trim() || undefined,
      })
      setProgress(100)
      applyClipResult(
        response as ClipResultResponse,
        response?.output_path?.trim() || outputPath,
        'full_pipeline',
        'AIClip 完整流程已完成',
      )
    } catch {
      message.error('AIClip 完整流程失败')
    } finally {
      setProgress(0)
    }
  }

  const handleSubmitWorkflow = async () => {
    if (!creativeContext?.creativeId || !creativeContext.sourceVersionId) {
      message.error('当前作品缺少可提交的版本上下文')
      return
    }

    if (!outputPath.trim()) {
      message.warning('请先生成可提交的输出文件')
      return
    }

    const derivedTitle = workflowTitle.trim()
      || `${creativeContext.creativeTitle || 'AIClip'} ${operationLabelMap[lastOperation ?? ''] || '新版本'}`

    try {
      const response = await submitWorkflowMutation.mutateAsync({
        source_version_id: creativeContext.sourceVersionId,
        output_path: outputPath.trim(),
        title: derivedTitle,
        workflow_type: 'ai_clip',
        metadata: {
          tool_surface: 'creative',
          last_operation: lastOperation,
          source_video_path: videoPath.trim() || null,
          audio_path: audioPath.trim() || null,
          cover_path: coverPath.trim() || null,
          highlight_segment_count: segments.length,
        },
      })

      message.success(
        response?.version?.version_no
          ? `已提交为 V${response.version.version_no}，进入待审核`
          : '已提交为新版本，进入待审核',
      )
      creativeContext.onSubmitted?.(response)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '提交工作流失败')
    }
  }

  const panelSummaryItems = [
    {
      key: 'optional-assets',
      label: '可选增强素材',
      children: (
        <Space direction="vertical" size={12} style={{ display: 'flex' }}>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            背景音和封面会参与完整流程；如果你只想快速产出，可以先留空，后续再补充。
          </Paragraph>
          <Input
            value={audioPath}
            onChange={(event) => setAudioPath(event.target.value)}
            placeholder="可选：背景音频路径"
            addonBefore="音频路径"
          />
          <Space direction="vertical" size={4} style={{ display: 'flex' }}>
            <Flex justify="space-between">
              <Text type="secondary">音量</Text>
              <Text>{Math.round(audioVolume * 100)}%</Text>
            </Flex>
            <Slider min={0} max={1} step={0.1} value={audioVolume} onChange={setAudioVolume} />
          </Space>
          <Input
            value={coverPath}
            onChange={(event) => setCoverPath(event.target.value)}
            placeholder="可选：封面图片路径"
            addonBefore="封面路径"
          />
        </Space>
      ),
    },
    {
      key: 'advanced-settings',
      label: '高级处理与输出',
      children: (
        <Space direction="vertical" size={12} style={{ display: 'flex' }}>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            仅在需要复用已有素材或覆盖默认输出位置时，再展开这些参数。
          </Paragraph>
          <Input
            value={outputDir}
            onChange={(event) => setOutputDir(event.target.value)}
            placeholder="可选：输出目录"
            addonBefore="输出目录"
          />
          <Input
            value={outputPath}
            onChange={(event) => setOutputPath(event.target.value)}
            placeholder="处理完成后会自动回填，也可手工调整"
            addonBefore="输出文件"
          />
          <Space wrap>
            <Button
              icon={<ScissorOutlined />}
              onClick={handleSmartClip}
              loading={processing}
              disabled={segments.length === 0}
            >
              仅生成智能剪辑
            </Button>
            <Button
              icon={<AudioOutlined />}
              onClick={handleAddAudio}
              loading={processing}
              disabled={!audioPath.trim()}
            >
              仅添加背景音
            </Button>
            <Button
              icon={<PictureOutlined />}
              onClick={handleAddCover}
              loading={processing}
              disabled={!coverPath.trim()}
            >
              仅添加封面
            </Button>
          </Space>
        </Space>
      ),
    },
  ]

  return (
    <div data-testid={creativeContext ? 'creative-ai-clip-panel' : 'ai-clip-panel'}>
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Alert
          type={creativeContext ? 'success' : 'info'}
          showIcon
          message={creativeContext ? '在当前作品内生成 AIClip 版本' : '独立完成一次 AIClip 处理流程'}
          description={creativeContext
            ? '建议按“选择素材 → 配置 → 执行 → 提交”的顺序完成，本次产物会作为新的 CreativeVersion 进入既有审核链。'
            : '这个页面保留为独立入口，适合先试跑 AIClip 流程；如果需要进入正式版本链路，请回到作品详情页提交。'}
        />

        <Card styles={{ body: { padding: screens.md ? 24 : 16 } }}>
          <Space direction="vertical" size={16} style={{ display: 'flex' }}>
            <div>
              <Title level={4} style={{ marginBottom: 8 }}>
                {creativeContext ? 'AIClip 版本工作流' : 'AIClip 独立工作流'}
              </Title>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                把主流程聚焦在素材选择、剪辑配置、执行产出和结果提交；高级参数仍可展开，但不再干扰主要操作链路。
              </Paragraph>
            </div>
            <Steps
              current={currentStep}
              size={screens.md ? 'default' : 'small'}
              responsive
              items={[
                { title: '选择素材', description: '确认源视频' },
                { title: '配置', description: '高光与增强素材' },
                { title: '执行', description: '生成 AIClip 产物' },
                { title: creativeContext ? '预览 / 提交' : '预览 / 导出', description: '确认输出结果' },
              ]}
            />
          </Space>
        </Card>

        <Row gutter={[16, 16]} align="top">
          <Col xs={24} xxl={15}>
            <Space direction="vertical" size={16} style={{ display: 'flex' }}>
              <Card
                title={<Space><VideoCameraOutlined /><span>1. 选择素材</span></Space>}
                extra={(
                  <Space wrap>
                    <Button icon={<SyncOutlined />} onClick={handleGetVideoInfo} loading={loadingInfo}>
                      获取视频信息
                    </Button>
                    <Button icon={<ScissorOutlined />} onClick={handleDetectHighlights} loading={loadingInfo}>
                      识别高光
                    </Button>
                  </Space>
                )}
              >
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Input
                    value={videoPath}
                    onChange={(event) => setVideoPath(event.target.value)}
                    placeholder="例如：D:\\videos\\source.mp4"
                    addonBefore="视频路径"
                    data-testid="creative-ai-clip-video-path"
                  />
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    先确认要处理的源视频。你可以先读视频信息，也可以直接识别高光，为后续流程准备自动剪辑片段。
                  </Paragraph>

                  {videoInfo ? (
                    <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
                      <Descriptions.Item label="时长">{formatTime(videoInfo.duration)}</Descriptions.Item>
                      <Descriptions.Item label="大小">{formatSize(videoInfo.size)}</Descriptions.Item>
                      <Descriptions.Item label="分辨率">
                        {videoInfo.width} × {videoInfo.height}
                      </Descriptions.Item>
                      <Descriptions.Item label="帧率">{videoInfo.fps?.toFixed?.(2) ?? '-'}</Descriptions.Item>
                      <Descriptions.Item label="格式">{videoInfo.format || '-'}</Descriptions.Item>
                      <Descriptions.Item label="路径">
                        <Text ellipsis style={{ maxWidth: screens.md ? 320 : 220 }}>{videoInfo.path || videoPath}</Text>
                      </Descriptions.Item>
                    </Descriptions>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="尚未获取视频信息" />
                  )}
                </Space>
              </Card>

              <Card
                title={<Space><ScissorOutlined /><span>2. 配置剪辑</span></Space>}
                extra={<Tag color={segments.length > 0 ? 'processing' : 'default'}>{segments.length} 个高光片段</Tag>}
              >
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    默认推荐先识别高光，再调整目标时长。若需要补背景音、封面或手工覆写输出路径，可在下方展开高级配置。
                  </Paragraph>

                  <Card size="small" type="inner" title="目标时长">
                    <Space direction="vertical" size={4} style={{ display: 'flex' }}>
                      <Flex justify="space-between">
                        <Text type="secondary">期望成片时长</Text>
                        <Text>{targetDuration}s</Text>
                      </Flex>
                      <Slider min={15} max={180} value={targetDuration} onChange={setTargetDuration} />
                      <Text type="secondary">已识别片段总时长：{formatTime(totalSegmentDuration)}</Text>
                    </Space>
                  </Card>

                  {segments.length > 0 ? (
                    <List
                      size="small"
                      bordered
                      header={<Text strong>候选高光片段</Text>}
                      dataSource={segments}
                      renderItem={(segment, index) => (
                        <List.Item
                          key={`${segment.start}-${segment.end}-${index}`}
                          actions={[
                            <Button
                              key="remove"
                              type="link"
                              danger
                              icon={<DeleteOutlined />}
                              onClick={() => setSegments((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                            >
                              移除
                            </Button>,
                          ]}
                        >
                          <Space direction="vertical" size={2}>
                            <Text>{formatTime(segment.start)} - {formatTime(segment.end)}</Text>
                            <Text type="secondary">{segment.reason}</Text>
                          </Space>
                        </List.Item>
                      )}
                    />
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="先识别高光后再进行智能剪辑" />
                  )}

                  <Collapse
                    bordered={false}
                    defaultActiveKey={hasOptionalEnhancements ? ['optional-assets'] : []}
                    items={panelSummaryItems}
                  />
                </Space>
              </Card>
            </Space>
          </Col>

          <Col xs={24} xxl={9}>
            <Space direction="vertical" size={16} style={{ display: 'flex' }}>
              <Card title={<Space><PlayCircleOutlined /><span>3. 执行并产出</span></Space>}>
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    主流程优先运行完整处理链。如果只是想先看剪辑结果，可以使用高级区域里的单步动作。
                  </Paragraph>
                  <Button
                    type="primary"
                    size="large"
                    icon={<PlayCircleOutlined />}
                    onClick={handleFullPipeline}
                    loading={processing}
                    block
                    data-testid="creative-ai-clip-run-pipeline"
                  >
                    执行完整流程
                  </Button>
                  <Button
                    icon={<ScissorOutlined />}
                    onClick={handleSmartClip}
                    loading={processing}
                    disabled={segments.length === 0}
                    block
                  >
                    先仅生成智能剪辑
                  </Button>
                  {processing ? <Progress percent={progress} status="active" /> : null}
                  {lastOperation ? (
                    <Tag color="processing">最近完成：{operationLabelMap[lastOperation] || lastOperation}</Tag>
                  ) : null}
                </Space>
              </Card>

              <Card
                title={<Space><CheckCircleOutlined /><span>4. 预览与结果</span></Space>}
                extra={outputPath ? <Tag color="success">ready</Tag> : <Tag>等待产出</Tag>}
              >
                {outputPath ? (
                  <Space direction="vertical" size={8} style={{ display: 'flex' }}>
                    <Text type="secondary">当前输出文件</Text>
                    <Input readOnly value={outputPath} data-testid="creative-ai-clip-output-path" />
                    <Text copyable>{outputPath}</Text>
                    <Alert
                      type="success"
                      showIcon
                      message="AIClip 产物已就绪"
                      description={creativeContext ? '你可以直接把它提交为新的作品版本。' : '如果结果符合预期，可在作品详情页继续进入正式版本流程。'}
                    />
                  </Space>
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="执行流程后会在这里展示输出结果" />
                )}
              </Card>

              {creativeContext ? (
                <Card
                  title={<Title level={5} style={{ margin: 0 }}>提交为新版本</Title>}
                  data-testid="creative-ai-clip-submit-card"
                >
                  <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                    <Descriptions bordered size="small" column={1}>
                      <Descriptions.Item label="作品">
                        {creativeContext.creativeTitle || `Creative #${creativeContext.creativeId}`}
                      </Descriptions.Item>
                      <Descriptions.Item label="来源版本">
                        {creativeContext.sourceVersionLabel || creativeContext.sourceVersionId || '-'}
                      </Descriptions.Item>
                    </Descriptions>

                    <Input
                      value={workflowTitle}
                      onChange={(event) => setWorkflowTitle(event.target.value)}
                      placeholder="提交后的版本标题"
                      addonBefore="版本标题"
                    />

                    <Alert
                      type="warning"
                      showIcon
                      message="提交后会创建新的 CreativeVersion"
                      description="该动作不会直接发布；成功后只会进入 WAITING_REVIEW，继续沿用现有审核链。"
                    />

                    <Button
                      type="primary"
                      onClick={handleSubmitWorkflow}
                      loading={submitWorkflowMutation.isPending}
                      disabled={!canSubmitWorkflow}
                      data-testid="creative-ai-clip-submit"
                    >
                      提交为新版本
                    </Button>
                  </Space>
                </Card>
              ) : null}
            </Space>
          </Col>
        </Row>
      </Space>
    </div>
  )
}
