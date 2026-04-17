import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Empty,
  Flex,
  Input,
  List,
  Progress,
  Row,
  Slider,
  Space,
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

const { Text, Title } = Typography

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

  const totalSegmentDuration = useMemo(
    () => segments.reduce((total, segment) => total + Math.max(segment.end - segment.start, 0), 0),
    [segments],
  )

  const ensureVideoPath = () => {
    if (!videoPath.trim()) {
      message.warning('请先填写源视频路径')
      return false
    }

    return true
  }

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

    const nextOutputPath = buildOutputPath(videoPath, outputDir, 'smart_clip')

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

    const nextOutputPath = buildOutputPath(videoPath, outputDir, 'audio_mix')

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

    const nextOutputPath = buildOutputPath(videoPath, outputDir, 'cover_mix')

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

  return (
    <div data-testid={creativeContext ? 'creative-ai-clip-panel' : 'ai-clip-panel'}>
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Alert
          type="info"
          showIcon
          message={creativeContext ? '在作品上下文中执行 AIClip' : 'AIClip 独立工具页'}
          description={creativeContext
            ? '先完成 AIClip 处理，再把产物提交为新的 CreativeVersion；提交后仍走既有 review 流程。'
            : '该页面保留为独立工具页 wrapper，可单独执行 AIClip 处理，不直接写入 Creative 工作流。'}
        />

        <Row gutter={16} align="top">
          <Col xs={24} xl={12}>
            <Card
              title={<Space><VideoCameraOutlined /><span>源视频与分析</span></Space>}
              extra={(
                <Space>
                  <Button icon={<SyncOutlined />} onClick={handleGetVideoInfo} loading={loadingInfo}>
                    视频信息
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

                {videoInfo ? (
                  <Descriptions bordered size="small" column={2}>
                    <Descriptions.Item label="时长">{formatTime(videoInfo.duration)}</Descriptions.Item>
                    <Descriptions.Item label="大小">{formatSize(videoInfo.size)}</Descriptions.Item>
                    <Descriptions.Item label="分辨率">
                      {videoInfo.width} × {videoInfo.height}
                    </Descriptions.Item>
                    <Descriptions.Item label="帧率">{videoInfo.fps?.toFixed?.(2) ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="格式">{videoInfo.format || '-'}</Descriptions.Item>
                    <Descriptions.Item label="路径">
                      <Text ellipsis style={{ maxWidth: 260 }}>{videoInfo.path || videoPath}</Text>
                    </Descriptions.Item>
                  </Descriptions>
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="尚未获取视频信息" />
                )}

                <Divider style={{ margin: '8px 0' }} />

                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Flex justify="space-between" align="center">
                    <Text strong>高光片段</Text>
                    <Tag>{segments.length} 段</Tag>
                  </Flex>

                  {segments.length > 0 ? (
                    <>
                      <List
                        size="small"
                        bordered
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
                      <Space direction="vertical" size={4} style={{ display: 'flex' }}>
                        <Flex justify="space-between">
                          <Text type="secondary">目标时长</Text>
                          <Text>{targetDuration}s</Text>
                        </Flex>
                        <Slider min={15} max={180} value={targetDuration} onChange={setTargetDuration} />
                        <Text type="secondary">片段总时长：{formatTime(totalSegmentDuration)}</Text>
                      </Space>
                    </>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="先识别高光后再进行智能剪辑" />
                  )}
                </Space>
              </Space>
            </Card>
          </Col>

          <Col xs={24} xl={12}>
            <Space direction="vertical" size={16} style={{ display: 'flex' }}>
              <Card title={<Space><AudioOutlined /><span>增强素材</span></Space>}>
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
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
              </Card>

              <Card title={<Space><PictureOutlined /><span>输出配置</span></Space>}>
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
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
                    data-testid="creative-ai-clip-output-path"
                  />
                  {lastOperation ? (
                    <Tag color="processing">最近操作：{operationLabelMap[lastOperation] || lastOperation}</Tag>
                  ) : null}
                </Space>
              </Card>

              <Card title={<Space><PlayCircleOutlined /><span>处理动作</span></Space>}>
                <Space direction="vertical" size={12} style={{ display: 'flex' }}>
                  <Button
                    type="primary"
                    icon={<ScissorOutlined />}
                    onClick={handleSmartClip}
                    loading={processing}
                    disabled={segments.length === 0}
                    block
                  >
                    智能剪辑
                  </Button>
                  <Button
                    icon={<AudioOutlined />}
                    onClick={handleAddAudio}
                    loading={processing}
                    disabled={!audioPath.trim()}
                    block
                  >
                    添加背景音
                  </Button>
                  <Button
                    icon={<PictureOutlined />}
                    onClick={handleAddCover}
                    loading={processing}
                    disabled={!coverPath.trim()}
                    block
                  >
                    添加封面
                  </Button>
                  <Divider style={{ margin: 0 }} />
                  <Button
                    type="dashed"
                    icon={<PlayCircleOutlined />}
                    onClick={handleFullPipeline}
                    loading={processing}
                    block
                    data-testid="creative-ai-clip-run-pipeline"
                  >
                    运行完整流程
                  </Button>

                  {processing ? (
                    <Progress percent={progress} status="active" />
                  ) : null}
                </Space>
              </Card>

              {outputPath ? (
                <Card
                  title={<Space><CheckCircleOutlined /><span>输出结果</span></Space>}
                  extra={<Tag color="success">ready</Tag>}
                >
                  <Space direction="vertical" size={8} style={{ display: 'flex' }}>
                    <Text type="secondary">当前输出文件</Text>
                    <Text copyable>{outputPath}</Text>
                  </Space>
                </Card>
              ) : null}

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
