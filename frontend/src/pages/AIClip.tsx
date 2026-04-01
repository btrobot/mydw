import { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Input,
  Slider,
  Table,
  Typography,
  Row,
  Col,
  message,
  Progress,
  Alert,
  Divider,
  Descriptions,
  Tag
} from 'antd'
import {
  ScissorOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  PictureOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
  SyncOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { useVideoInfo, useDetectHighlights, useSmartClip, useAddAudio, useAddCover, useFullPipeline } from '../hooks'

const { Text, Title, Paragraph } = Typography

interface VideoInfo {
  path: string
  duration: number
  width: number
  height: number
  fps: number
  size: number
  format: string
}

interface HighlightSegment {
  start: number
  end: number
  reason: string
}

export default function AIClip() {
  const [videoPath, setVideoPath] = useState('')
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
  const [segments, setSegments] = useState<HighlightSegment[]>([])
  const [targetDuration, setTargetDuration] = useState(60)
  const [audioPath, setAudioPath] = useState('')
  const [audioVolume, setAudioVolume] = useState(0.3)
  const [coverPath, setCoverPath] = useState('')
  const [outputDir, setOutputDir] = useState('')
  const [outputPath, setOutputPath] = useState('')

  const [progress, setProgress] = useState(0)

  // 使用 React Query hooks
  const videoInfoMutation = useVideoInfo()
  const detectHighlightsMutation = useDetectHighlights()
  const smartClipMutation = useSmartClip()
  const addAudioMutation = useAddAudio()
  const addCoverMutation = useAddCover()
  const fullPipelineMutation = useFullPipeline()

  // 统一 loading 状态
  const loading = videoInfoMutation.isPending || detectHighlightsMutation.isPending
  const clipping = smartClipMutation.isPending || addAudioMutation.isPending || addCoverMutation.isPending || fullPipelineMutation.isPending

  // 获取视频信息
  const handleGetVideoInfo = async () => {
    if (!videoPath.trim()) {
      message.warning('请输入视频路径')
      return
    }
    try {
      const res = await videoInfoMutation.mutateAsync({ video_path: videoPath })
      setVideoInfo(res)
      message.success('视频信息获取成功')
    } catch (error: unknown) {
      message.error('获取视频信息失败')
      setVideoInfo(null)
    }
  }

  // 检测高光
  const handleDetectHighlights = async () => {
    if (!videoPath.trim()) {
      message.warning('请输入视频路径')
      return
    }
    try {
      const res = await detectHighlightsMutation.mutateAsync({ video_path: videoPath })
      setSegments((res.segments as unknown as HighlightSegment[]) || [])
      message.success(`检测到 ${res.count || 0} 个高光片段`)
    } catch (error: unknown) {
      message.error('检测高光失败')
    }
  }

  // 智能剪辑
  const handleSmartClip = async () => {
    if (!videoPath.trim()) {
      message.warning('请输入视频路径')
      return
    }
    if (segments.length === 0) {
      message.warning('请先检测高光片段')
      return
    }
    try {
      setProgress(10)
      const timestamp = new Date().getTime()
      const output = outputDir
        ? `${outputDir}/clip_${timestamp}.mp4`
        : videoPath.replace(/\.[^.]+$/, `_clip_${timestamp}.mp4`)

      setProgress(30)
      const res = await smartClipMutation.mutateAsync({
        video_path: videoPath,
        segments: segments,
        output_path: output,
        target_duration: targetDuration
      }) as { success?: boolean; output_path?: string; error?: string }

      setProgress(80)
      if (res.success) {
        setProgress(100)
        setOutputPath(res.output_path || output)
        message.success('视频剪辑完成')
      } else {
        message.error(res.error || '剪辑失败')
      }
    } catch (error: unknown) {
      message.error('剪辑失败')
    } finally {
      setProgress(0)
    }
  }

  // 添加背景音乐
  const handleAddAudio = async () => {
    if (!videoPath.trim() || !audioPath.trim()) {
      message.warning('请输入视频和音频路径')
      return
    }
    try {
      setProgress(10)
      const timestamp = new Date().getTime()
      const output = outputDir
        ? `${outputDir}/audio_${timestamp}.mp4`
        : videoPath.replace(/\.[^.]+$/, `_audio_${timestamp}.mp4`)

      setProgress(50)
      const res = await addAudioMutation.mutateAsync({
        video_path: videoPath,
        audio_path: audioPath,
        output_path: output,
        volume: audioVolume
      }) as { success?: boolean; output_path?: string; error?: string }

      setProgress(100)
      if (res.success) {
        setOutputPath(res.output_path || output)
        message.success('背景音乐添加成功')
      } else {
        message.error(res.error || '添加失败')
      }
    } catch (error: unknown) {
      message.error('添加背景音乐失败')
    } finally {
      setProgress(0)
    }
  }

  // 添加封面
  const handleAddCover = async () => {
    if (!videoPath.trim() || !coverPath.trim()) {
      message.warning('请输入视频和封面路径')
      return
    }
    try {
      setProgress(50)
      const timestamp = new Date().getTime()
      const output = outputDir
        ? `${outputDir}/cover_${timestamp}.mp4`
        : videoPath.replace(/\.[^.]+$/, `_cover_${timestamp}.mp4`)

      const res = await addCoverMutation.mutateAsync({
        video_path: videoPath,
        cover_path: coverPath,
        output_path: output
      }) as { success?: boolean; output_path?: string; error?: string }

      setProgress(100)
      if (res.success) {
        setOutputPath(res.output_path || output)
        message.success('封面添加成功')
      } else {
        message.error(res.error || '添加失败')
      }
    } catch (error: unknown) {
      message.error('添加封面失败')
    } finally {
      setProgress(0)
    }
  }

  // 完整流程
  const handleFullPipeline = async () => {
    if (!videoPath.trim()) {
      message.warning('请输入视频路径')
      return
    }
    try {
      setProgress(10)

      const res = await fullPipelineMutation.mutateAsync({
        video_path: videoPath,
        audio_path: audioPath || undefined,
        cover_path: coverPath || undefined,
        target_duration: targetDuration,
        output_dir: outputDir || undefined
      }) as { success?: boolean; output_path?: string; error?: string }

      setProgress(100)
      if (res.success) {
        setOutputPath(res.output_path || '')
        message.success('AI 剪辑流程完成')
      } else {
        message.error(res.error || '处理失败')
      }
    } catch (error: unknown) {
      message.error('AI 剪辑失败')
    } finally {
      setProgress(0)
    }
  }

  // 删除片段
  const handleDeleteSegment = (index: number) => {
    setSegments(prev => prev.filter((_, i) => i !== index))
  }

  // 格式化时间
  const formatTime = (seconds: number): string => {
    if (isNaN(seconds) || seconds < 0) return '00:00.00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    const ms = Math.floor((seconds % 1) * 100)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`
  }

  // 格式化文件大小
  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const segmentColumns = [
    {
      title: '序号',
      dataIndex: 'index',
      key: 'index',
      width: 60,
      render: (_: unknown, __: unknown, index: number) => index + 1
    },
    {
      title: '开始时间',
      dataIndex: 'start',
      key: 'start',
      width: 120,
      render: (val: number) => formatTime(val)
    },
    {
      title: '结束时间',
      dataIndex: 'end',
      key: 'end',
      width: 120,
      render: (val: number) => formatTime(val)
    },
    {
      title: '时长',
      key: 'duration',
      width: 80,
      render: (_: unknown, record: HighlightSegment) => formatTime(record.end - record.start)
    },
    {
      title: '原因',
      dataIndex: 'reason',
      key: 'reason'
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, __: unknown, index: number) => (
        <Button
          type="link"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteSegment(index)}
        >
          删除
        </Button>
      )
    }
  ]

  return (
    <div>
      <Title level={4}>
        <ScissorOutlined /> AI 智能剪辑
      </Title>
      <Paragraph type="secondary">
        基于 FFmpeg 的智能视频剪辑工具，支持高光检测、自动剪辑、添加背景音乐和封面
      </Paragraph>

      <Alert
        message="使用说明"
        description="1. 输入视频路径获取视频信息 → 2. 检测高光片段 → 3. 选择剪辑方式（智能剪辑/完整流程）→ 4. 导出最终视频"
        type="info"
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16}>
        {/* 左侧：视频信息 */}
        <Col span={12}>
          <Card
            title={<><VideoCameraOutlined /> 视频信息</>}
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<SyncOutlined />}
                  onClick={handleGetVideoInfo}
                  loading={loading}
                >
                  获取信息
                </Button>
                <Button
                  icon={<ScissorOutlined />}
                  onClick={handleDetectHighlights}
                  loading={loading}
                >
                  检测高光
                </Button>
              </Space>
            }
          >
            <Input
              addonBefore="视频路径"
              value={videoPath}
              onChange={e => setVideoPath(e.target.value)}
              placeholder="请输入视频文件路径，如：D:\ videos\test.mp4"
              style={{ marginBottom: 16 }}
            />

            {videoInfo && (
              <Descriptions column={2} size="small" bordered>
                <Descriptions.Item label="时长">{formatTime(videoInfo.duration)}</Descriptions.Item>
                <Descriptions.Item label="大小">{formatSize(videoInfo.size)}</Descriptions.Item>
                <Descriptions.Item label="分辨率">{videoInfo.width} x {videoInfo.height}</Descriptions.Item>
                <Descriptions.Item label="帧率">{videoInfo.fps.toFixed(2)} fps</Descriptions.Item>
                <Descriptions.Item label="格式">{videoInfo.format}</Descriptions.Item>
                <Descriptions.Item label="预计剪辑后时长">{Math.min(targetDuration, videoInfo.duration).toFixed(0)}s</Descriptions.Item>
              </Descriptions>
            )}
          </Card>

          {/* 高光片段 */}
          {segments.length > 0 && (
            <Card
              title={<><ScissorOutlined /> 高光片段 ({segments.length}个)</>}
              style={{ marginTop: 16 }}
              extra={
                <Text type="secondary">
                  总时长: {formatTime(segments.reduce((acc, s) => acc + (s.end - s.start), 0))}
                </Text>
              }
            >
              <Table
                columns={segmentColumns}
                dataSource={segments.map((s, i) => ({ ...s, key: i }))}
                pagination={false}
                size="small"
              />

              <Divider />

              <Space>
                <Text>目标时长: </Text>
                <Slider
                  min={15}
                  max={180}
                  value={targetDuration}
                  onChange={setTargetDuration}
                  style={{ width: 200 }}
                />
                <Text>{targetDuration}秒</Text>
              </Space>
            </Card>
          )}
        </Col>

        {/* 右侧：剪辑选项 */}
        <Col span={12}>
          <Card title={<><AudioOutlined /> 背景音乐</>}>
            <Input
              addonBefore="音频路径"
              value={audioPath}
              onChange={e => setAudioPath(e.target.value)}
              placeholder="可选，留空则不添加背景音乐"
              style={{ marginBottom: 12 }}
            />
            <Space>
              <Text>音量: </Text>
              <Slider
                min={0}
                max={1}
                step={0.1}
                value={audioVolume}
                onChange={setAudioVolume}
                style={{ width: 200 }}
              />
              <Text>{(audioVolume * 100).toFixed(0)}%</Text>
            </Space>
          </Card>

          <Card
            title={<><PictureOutlined /> 视频封面</>}
            style={{ marginTop: 16 }}
          >
            <Input
              addonBefore="封面路径"
              value={coverPath}
              onChange={e => setCoverPath(e.target.value)}
              placeholder="可选，留空则不添加封面"
            />
          </Card>

          <Card
            title="输出设置"
            style={{ marginTop: 16 }}
          >
            <Input
              addonBefore="输出目录"
              value={outputDir}
              onChange={e => setOutputDir(e.target.value)}
              placeholder="可选，留空则输出到视频同目录"
            />
          </Card>

          {/* 剪辑操作 */}
          <Card style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                block
                type="primary"
                size="large"
                icon={<ScissorOutlined />}
                onClick={handleSmartClip}
                loading={clipping}
                disabled={segments.length === 0}
              >
                智能剪辑
              </Button>

              <Button
                block
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={handleAddAudio}
                loading={clipping}
                disabled={!audioPath}
              >
                添加背景音乐
              </Button>

              <Button
                block
                size="large"
                icon={<PictureOutlined />}
                onClick={handleAddCover}
                loading={clipping}
                disabled={!coverPath}
              >
                添加封面
              </Button>

              <Divider />

              <Button
                block
                type="dashed"
                size="large"
                icon={<ScissorOutlined />}
                onClick={handleFullPipeline}
                loading={clipping}
              >
                一键 AI 剪辑（完整流程）
              </Button>
            </Space>

            {clipping && (
              <Progress
                percent={progress}
                status="active"
                strokeColor="#1890ff"
                style={{ marginTop: 16 }}
              />
            )}
          </Card>

          {/* 输出结果 */}
          {outputPath && (
            <Card
              title={<><CheckCircleOutlined /> 剪辑完成</>}
              style={{ marginTop: 16 }}
              extra={<Tag color="success">成功</Tag>}
            >
              <Paragraph>
                <Text type="secondary">输出路径：</Text>
                <Text copyable>{outputPath}</Text>
              </Paragraph>
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}
