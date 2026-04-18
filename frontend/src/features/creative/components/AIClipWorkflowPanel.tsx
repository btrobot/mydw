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
  smart_clip: '\u667a\u80fd\u526a\u8f91',
  add_audio: '\u6dfb\u52a0\u80cc\u666f\u97f3',
  add_cover: '\u6dfb\u52a0\u5c01\u9762',
  full_pipeline: '\u5b8c\u6574\u6d41\u7a0b',
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
      const reason = typeof candidate.reason === 'string' ? candidate.reason : '\u672a\u6807\u6ce8\u539f\u56e0'

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
        ? `${creativeContext.creativeTitle} AIClip \u7248\u672c`
        : 'AIClip \u518d\u521b\u4f5c\u7248\u672c',
    )
  }, [creativeContext?.creativeId, creativeContext?.creativeTitle])

  const ensureVideoPath = () => {
    if (!videoPath.trim()) {
      message.warning('\u8bf7\u5148\u586b\u5199\u6e90\u89c6\u9891\u8def\u5f84')
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

    message.error(response?.error || '\u5904\u7406\u5931\u8d25')
  }

  const handleGetVideoInfo = async () => {
    if (!ensureVideoPath()) {
      return
    }

    try {
      const response = await videoInfoMutation.mutateAsync({ video_path: videoPath.trim() })
      setVideoInfo(response)
      message.success('\u5df2\u83b7\u53d6\u89c6\u9891\u4fe1\u606f')
    } catch {
      setVideoInfo(null)
      message.error('\u83b7\u53d6\u89c6\u9891\u4fe1\u606f\u5931\u8d25')
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
      message.success(`\u5df2\u8bc6\u522b ${nextSegments.length} \u4e2a\u9ad8\u5149\u7247\u6bb5`)
    } catch {
      message.error('\u9ad8\u5149\u8bc6\u522b\u5931\u8d25')
    }
  }

  const handleSmartClip = async () => {
    if (!ensureVideoPath()) {
      return
    }

    if (segments.length === 0) {
      message.warning('\u8bf7\u5148\u8bc6\u522b\u9ad8\u5149\u7247\u6bb5')
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
      applyClipResult(response as ClipResultResponse, nextOutputPath, 'smart_clip', '\u667a\u80fd\u526a\u8f91\u5b8c\u6210')
    } catch {
      message.error('\u667a\u80fd\u526a\u8f91\u5931\u8d25')
    } finally {
      setProgress(0)
    }
  }

  const handleAddAudio = async () => {
    if (!ensureVideoPath()) {
      return
    }

    if (!audioPath.trim()) {
      message.warning('\u8bf7\u586b\u5199\u80cc\u666f\u97f3\u9891\u8def\u5f84')
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
      applyClipResult(response as ClipResultResponse, nextOutputPath, 'add_audio', '\u80cc\u666f\u97f3\u5df2\u52a0\u5165')
    } catch {
      message.error('\u6dfb\u52a0\u80cc\u666f\u97f3\u5931\u8d25')
    } finally {
      setProgress(0)
    }
  }

  const handleAddCover = async () => {
    if (!ensureVideoPath()) {
      return
    }

    if (!coverPath.trim()) {
      message.warning('\u8bf7\u586b\u5199\u5c01\u9762\u8def\u5f84')
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
      applyClipResult(response as ClipResultResponse, nextOutputPath, 'add_cover', '\u5c01\u9762\u5df2\u52a0\u5165')
    } catch {
      message.error('\u6dfb\u52a0\u5c01\u9762\u5931\u8d25')
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
        'AIClip \u5b8c\u6574\u6d41\u7a0b\u5df2\u5b8c\u6210',
      )
    } catch {
      message.error('AIClip \u5b8c\u6574\u6d41\u7a0b\u5931\u8d25')
    } finally {
      setProgress(0)
    }
  }

  const handleSubmitWorkflow = async () => {
    if (!creativeContext?.creativeId || !creativeContext.sourceVersionId) {
      message.error('\u5f53\u524d\u4f5c\u54c1\u7f3a\u5c11\u53ef\u63d0\u4ea4\u7684\u7248\u672c\u4e0a\u4e0b\u6587')
      return
    }

    if (!outputPath.trim()) {
      message.warning('\u8bf7\u5148\u751f\u6210\u53ef\u63d0\u4ea4\u7684\u8f93\u51fa\u6587\u4ef6')
      return
    }

    const derivedTitle = workflowTitle.trim()
      || `${creativeContext.creativeTitle || 'AIClip'} ${operationLabelMap[lastOperation ?? ''] || '\u65b0\u7248\u672c'}`

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
          ? `\u5df2\u63d0\u4ea4\u4e3a V${response.version.version_no}\uff0c\u8fdb\u5165\u5f85\u5ba1\u6838`
          : '\u5df2\u63d0\u4ea4\u4e3a\u65b0\u7248\u672c\uff0c\u8fdb\u5165\u5f85\u5ba1\u6838',
      )
      creativeContext.onSubmitted?.(response)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '\u63d0\u4ea4\u5de5\u4f5c\u6d41\u5931\u8d25')
    }
  }

  const panelSummaryItems = [
    {
      key: 'optional-assets',
      label: '\u53ef\u9009\u589e\u5f3a\u7d20\u6750',
      children: (
        <Space direction="vertical" size={12} style={{ display: 'flex' }}>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            \u80cc\u666f\u97f3\u548c\u5c01\u9762\u4f1a\u53c2\u4e0e\u5b8c\u6574\u6d41\u7a0b\uff1b\u5982\u679c\u4f60\u53ea\u60f3\u5feb\u901f\u4ea7\u51fa\uff0c\u53ef\u4ee5\u5148\u7559\u7a7a\uff0c\u540e\u7eed\u518d\u8865\u5145\u3002
          </Paragraph>
          <Input
            value={audioPath}
            onChange={(event) => setAudioPath(event.target.value)}
            placeholder="\u53ef\u9009\uff1a\u80cc\u666f\u97f3\u9891\u8def\u5f84"
            addonBefore="\u97f3\u9891\u8def\u5f84"
          />
          <Space direction="vertical" size={4} style={{ display: 'flex' }}>
            <Flex justify="space-between">
              <Text type="secondary">\u97f3\u91cf</Text>
              <Text>{Math.round(audioVolume * 100)}%</Text>
            </Flex>
            <Slider min={0} max={1} step={0.1} value={audioVolume} onChange={setAudioVolume} />
          </Space>
          <Input
            value={coverPath}
            onChange={(event) => setCoverPath(event.target.value)}
            placeholder="\u53ef\u9009\uff1a\u5c01\u9762\u56fe\u7247\u8def\u5f84"
            addonBefore="\u5c01\u9762\u8def\u5f84"
          />
        </Space>
      ),
    },
    {
      key: 'advanced-settings',
      label: '\u9ad8\u7ea7\u5904\u7406\u4e0e\u8f93\u51fa',
      children: (
        <Space direction="vertical" size={12} style={{ display: 'flex' }}>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            \u4ec5\u5728\u9700\u8981\u590d\u7528\u5df2\u6709\u7d20\u6750\u6216\u8986\u76d6\u9ed8\u8ba4\u8f93\u51fa\u4f4d\u7f6e\u65f6\uff0c\u518d\u5c55\u5f00\u8fd9\u4e9b\u53c2\u6570\u3002
          </Paragraph>
          <Input
            value={outputDir}
            onChange={(event) => setOutputDir(event.target.value)}
            placeholder="\u53ef\u9009\uff1a\u8f93\u51fa\u76ee\u5f55"
            addonBefore="\u8f93\u51fa\u76ee\u5f55"
          />
          <Input
            value={outputPath}
            onChange={(event) => setOutputPath(event.target.value)}
            placeholder="\u5904\u7406\u5b8c\u6210\u540e\u4f1a\u81ea\u52a8\u56de\u586b\uff0c\u4e5f\u53ef\u624b\u5de5\u8c03\u6574"
            addonBefore="\u8f93\u51fa\u6587\u4ef6"
          />
          <Space wrap>
            <Button
              icon={<ScissorOutlined />}
              onClick={handleSmartClip}
              loading={processing}
              disabled={segments.length === 0}
            >
              \u4ec5\u751f\u6210\u667a\u80fd\u526a\u8f91
            </Button>
            <Button
              icon={<AudioOutlined />}
              onClick={handleAddAudio}
              loading={processing}
              disabled={!audioPath.trim()}
            >
              \u4ec5\u6dfb\u52a0\u80cc\u666f\u97f3
            </Button>
            <Button
              icon={<PictureOutlined />}
              onClick={handleAddCover}
              loading={processing}
              disabled={!coverPath.trim()}
            >
              \u4ec5\u6dfb\u52a0\u5c01\u9762
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
          message={creativeContext ? '\u5728\u5f53\u524d\u4f5c\u54c1\u5185\u751f\u6210 AIClip \u7248\u672c' : '\u72ec\u7acb\u5b8c\u6210\u4e00\u6b21 AIClip \u5904\u7406\u6d41\u7a0b'}
          description={creativeContext
            ? '\u5efa\u8bae\u6309\u201c\u9009\u62e9\u7d20\u6750 \u2192 \u914d\u7f6e \u2192 \u6267\u884c \u2192 \u63d0\u4ea4\u201d\u7684\u987a\u5e8f\u5b8c\u6210\uff0c\u672c\u6b21\u4ea7\u7269\u4f1a\u4f5c\u4e3a\u65b0\u7684 CreativeVersion \u8fdb\u5165\u65e2\u6709\u5ba1\u6838\u94fe\u3002'
            : '\u8fd9\u4e2a\u9875\u9762\u4fdd\u7559\u4e3a\u72ec\u7acb\u5165\u53e3\uff0c\u9002\u5408\u5148\u8bd5\u8dd1 AIClip \u6d41\u7a0b\uff1b\u5982\u679c\u9700\u8981\u8fdb\u5165\u6b63\u5f0f\u7248\u672c\u94fe\u8def\uff0c\u8bf7\u56de\u5230\u4f5c\u54c1\u8be6\u60c5\u9875\u63d0\u4ea4\u3002'}
        />

        <Card styles={{ body: { padding: screens.md ? 24 : 16 } }}>
          <Space direction="vertical" size={16} style={{ display: 'flex' }}>
            <div>
              <Title level={4} style={{ marginBottom: 8 }}>
                {creativeContext ? 'AIClip \u7248\u672c\u5de5\u4f5c\u6d41' : 'AIClip \u72ec\u7acb\u5de5\u4f5c\u6d41'}
              </Title>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                \u628a\u4e3b\u6d41\u7a0b\u805a\u7126\u5728\u7d20\u6750\u9009\u62e9\u3001\u526a\u8f91\u914d\u7f6e\u3001\u6267\u884c\u4ea7\u51fa\u548c\u7ed3\u679c\u63d0\u4ea4\uff1b\u9ad8\u7ea7\u53c2\u6570\u4ecd\u53ef\u5c55\u5f00\uff0c\u4f46\u4e0d\u518d\u5e72\u6270\u4e3b\u8981\u64cd\u4f5c\u94fe\u8def\u3002
              </Paragraph>
            </div>
            <Steps
              current={currentStep}
              size={screens.md ? 'default' : 'small'}
              responsive
              items={[
                { title: '\u9009\u62e9\u7d20\u6750', description: '\u786e\u8ba4\u6e90\u89c6\u9891' },
                { title: '\u914d\u7f6e', description: '\u9ad8\u5149\u4e0e\u589e\u5f3a\u7d20\u6750' },
                { title: '\u6267\u884c', description: '\u751f\u6210 AIClip \u4ea7\u7269' },
                { title: creativeContext ? '\u9884\u89c8 / \u63d0\u4ea4' : '\u9884\u89c8 / \u5bfc\u51fa', description: '\u786e\u8ba4\u8f93\u51fa\u7ed3\u679c' },
              ]}
            />
          </Space>
        </Card>

        <Row gutter={[16, 16]} align="top">
          <Col xs={24} xxl={15}>
            <Space direction="vertical" size={16} style={{ display: 'flex' }}>
              <Card
                title={<Space><VideoCameraOutlined /><span>1. \u9009\u62e9\u7d20\u6750</span></Space>}
                extra={(
                  <Space wrap>
                    <Button icon={<SyncOutlined />} onClick={handleGetVideoInfo} loading={loadingInfo}>
                      \u83b7\u53d6\u89c6\u9891\u4fe1\u606f
                    </Button>
                    <Button icon={<ScissorOutlined />} onClick={handleDetectHighlights} loading={loadingInfo}>
                      \u8bc6\u522b\u9ad8\u5149
                    </Button>
                  </Space>
                )}
              >
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Input
                    value={videoPath}
                    onChange={(event) => setVideoPath(event.target.value)}
                    placeholder="\u4f8b\u5982\uff1aD:\\videos\\source.mp4"
                    addonBefore="\u89c6\u9891\u8def\u5f84"
                    data-testid="creative-ai-clip-video-path"
                  />
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    \u5148\u786e\u8ba4\u8981\u5904\u7406\u7684\u6e90\u89c6\u9891\u3002\u4f60\u53ef\u4ee5\u5148\u8bfb\u89c6\u9891\u4fe1\u606f\uff0c\u4e5f\u53ef\u4ee5\u76f4\u63a5\u8bc6\u522b\u9ad8\u5149\uff0c\u4e3a\u540e\u7eed\u6d41\u7a0b\u51c6\u5907\u81ea\u52a8\u526a\u8f91\u7247\u6bb5\u3002
                  </Paragraph>

                  {videoInfo ? (
                    <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
                      <Descriptions.Item label="\u65f6\u957f">{formatTime(videoInfo.duration)}</Descriptions.Item>
                      <Descriptions.Item label="\u5927\u5c0f">{formatSize(videoInfo.size)}</Descriptions.Item>
                      <Descriptions.Item label="\u5206\u8fa8\u7387">
                        {videoInfo.width} \u00d7 {videoInfo.height}
                      </Descriptions.Item>
                      <Descriptions.Item label="\u5e27\u7387">{videoInfo.fps?.toFixed?.(2) ?? '-'}</Descriptions.Item>
                      <Descriptions.Item label="\u683c\u5f0f">{videoInfo.format || '-'}</Descriptions.Item>
                      <Descriptions.Item label="\u8def\u5f84">
                        <Text ellipsis style={{ maxWidth: screens.md ? 320 : 220 }}>{videoInfo.path || videoPath}</Text>
                      </Descriptions.Item>
                    </Descriptions>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="\u5c1a\u672a\u83b7\u53d6\u89c6\u9891\u4fe1\u606f" />
                  )}
                </Space>
              </Card>

              <Card
                title={<Space><ScissorOutlined /><span>2. \u914d\u7f6e\u526a\u8f91</span></Space>}
                extra={<Tag color={segments.length > 0 ? 'processing' : 'default'}>{segments.length} \u4e2a\u9ad8\u5149\u7247\u6bb5</Tag>}
              >
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    \u9ed8\u8ba4\u63a8\u8350\u5148\u8bc6\u522b\u9ad8\u5149\uff0c\u518d\u8c03\u6574\u76ee\u6807\u65f6\u957f\u3002\u82e5\u9700\u8981\u8865\u80cc\u666f\u97f3\u3001\u5c01\u9762\u6216\u624b\u5de5\u8986\u5199\u8f93\u51fa\u8def\u5f84\uff0c\u53ef\u5728\u4e0b\u65b9\u5c55\u5f00\u9ad8\u7ea7\u914d\u7f6e\u3002
                  </Paragraph>

                  <Card size="small" type="inner" title="\u76ee\u6807\u65f6\u957f">
                    <Space direction="vertical" size={4} style={{ display: 'flex' }}>
                      <Flex justify="space-between">
                        <Text type="secondary">\u671f\u671b\u6210\u7247\u65f6\u957f</Text>
                        <Text>{targetDuration}s</Text>
                      </Flex>
                      <Slider min={15} max={180} value={targetDuration} onChange={setTargetDuration} />
                      <Text type="secondary">\u5df2\u8bc6\u522b\u7247\u6bb5\u603b\u65f6\u957f\uff1a{formatTime(totalSegmentDuration)}</Text>
                    </Space>
                  </Card>

                  {segments.length > 0 ? (
                    <List
                      size="small"
                      bordered
                      header={<Text strong>\u5019\u9009\u9ad8\u5149\u7247\u6bb5</Text>}
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
                              \u79fb\u9664
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
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="\u5148\u8bc6\u522b\u9ad8\u5149\u540e\u518d\u8fdb\u884c\u667a\u80fd\u526a\u8f91" />
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
              <Card title={<Space><PlayCircleOutlined /><span>3. \u6267\u884c\u5e76\u4ea7\u51fa</span></Space>}>
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    \u4e3b\u6d41\u7a0b\u4f18\u5148\u8fd0\u884c\u5b8c\u6574\u5904\u7406\u94fe\u3002\u5982\u679c\u53ea\u662f\u60f3\u5148\u770b\u526a\u8f91\u7ed3\u679c\uff0c\u53ef\u4ee5\u4f7f\u7528\u9ad8\u7ea7\u533a\u57df\u91cc\u7684\u5355\u6b65\u52a8\u4f5c\u3002
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
                    \u6267\u884c\u5b8c\u6574\u6d41\u7a0b
                  </Button>
                  <Button
                    icon={<ScissorOutlined />}
                    onClick={handleSmartClip}
                    loading={processing}
                    disabled={segments.length === 0}
                    block
                  >
                    \u5148\u4ec5\u751f\u6210\u667a\u80fd\u526a\u8f91
                  </Button>
                  {processing ? <Progress percent={progress} status="active" /> : null}
                  {lastOperation ? (
                    <Tag color="processing">\u6700\u8fd1\u5b8c\u6210\uff1a{operationLabelMap[lastOperation] || lastOperation}</Tag>
                  ) : null}
                </Space>
              </Card>

              <Card
                title={<Space><CheckCircleOutlined /><span>4. \u9884\u89c8\u4e0e\u7ed3\u679c</span></Space>}
                extra={outputPath ? <Tag color="success">ready</Tag> : <Tag>\u7b49\u5f85\u4ea7\u51fa</Tag>}
              >
                {outputPath ? (
                  <Space direction="vertical" size={8} style={{ display: 'flex' }}>
                    <Text type="secondary">\u5f53\u524d\u8f93\u51fa\u6587\u4ef6</Text>
                    <Input readOnly value={outputPath} data-testid="creative-ai-clip-output-path" />
                    <Text copyable>{outputPath}</Text>
                    <Alert
                      type="success"
                      showIcon
                      message="AIClip \u4ea7\u7269\u5df2\u5c31\u7eea"
                      description={creativeContext ? '\u4f60\u53ef\u4ee5\u76f4\u63a5\u628a\u5b83\u63d0\u4ea4\u4e3a\u65b0\u7684\u4f5c\u54c1\u7248\u672c\u3002' : '\u5982\u679c\u7ed3\u679c\u7b26\u5408\u9884\u671f\uff0c\u53ef\u5728\u4f5c\u54c1\u8be6\u60c5\u9875\u7ee7\u7eed\u8fdb\u5165\u6b63\u5f0f\u7248\u672c\u6d41\u7a0b\u3002'}
                    />
                  </Space>
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="\u6267\u884c\u6d41\u7a0b\u540e\u4f1a\u5728\u8fd9\u91cc\u5c55\u793a\u8f93\u51fa\u7ed3\u679c" />
                )}
              </Card>

              {creativeContext ? (
                <Card
                  title={<Title level={5} style={{ margin: 0 }}>\u63d0\u4ea4\u4e3a\u65b0\u7248\u672c</Title>}
                  data-testid="creative-ai-clip-submit-card"
                >
                  <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                    <Descriptions bordered size="small" column={1}>
                      <Descriptions.Item label="\u4f5c\u54c1">
                        {creativeContext.creativeTitle || `Creative #${creativeContext.creativeId}`}
                      </Descriptions.Item>
                      <Descriptions.Item label="\u6765\u6e90\u7248\u672c">
                        {creativeContext.sourceVersionLabel || creativeContext.sourceVersionId || '-'}
                      </Descriptions.Item>
                    </Descriptions>

                    <Input
                      value={workflowTitle}
                      onChange={(event) => setWorkflowTitle(event.target.value)}
                      placeholder="\u63d0\u4ea4\u540e\u7684\u7248\u672c\u6807\u9898"
                      addonBefore="\u7248\u672c\u6807\u9898"
                    />

                    <Alert
                      type="warning"
                      showIcon
                      message="\u63d0\u4ea4\u540e\u4f1a\u521b\u5efa\u65b0\u7684 CreativeVersion"
                      description="\u8be5\u52a8\u4f5c\u4e0d\u4f1a\u76f4\u63a5\u53d1\u5e03\uff1b\u6210\u529f\u540e\u53ea\u4f1a\u8fdb\u5165 WAITING_REVIEW\uff0c\u7ee7\u7eed\u6cbf\u7528\u73b0\u6709\u5ba1\u6838\u94fe\u3002"
                    />

                    <Button
                      type="primary"
                      onClick={handleSubmitWorkflow}
                      loading={submitWorkflowMutation.isPending}
                      disabled={!canSubmitWorkflow}
                      data-testid="creative-ai-clip-submit"
                    >
                      \u63d0\u4ea4\u4e3a\u65b0\u7248\u672c
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
