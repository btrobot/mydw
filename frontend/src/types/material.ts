/**
 * Material domain types — aligned with backend schemas (SP2-01)
 */

// ============ Batch Delete ============

export interface BatchDeleteResponse {
  deleted: number
  skipped: number
  skipped_ids: number[]
}

// ============ Product ============

export interface ProductResponse {
  id: number
  name: string
  link: string | null
  description: string | null
  dewu_url: string | null
  image_url: string | null
  created_at: string
  updated_at: string
}

export interface ProductListResponse {
  total: number
  items: ProductResponse[]
}

export interface ProductCreate {
  name: string
  link?: string | null
  description?: string | null
  dewu_url?: string | null
  image_url?: string | null
}

// ============ Video ============

export interface VideoResponse {
  id: number
  product_id: number | null
  product_name: string | null
  name: string
  file_path: string
  file_size: number | null
  duration: number | null
  width: number | null
  height: number | null
  file_hash: string | null
  source_type: string
  file_exists?: boolean
  created_at: string
  updated_at: string
}

export interface VideoListResponse {
  total: number
  items: VideoResponse[]
}

export interface VideoCreate {
  name: string
  file_path: string
  product_id?: number | null
  file_size?: number | null
  duration?: number | null
}

// ============ Copywriting ============

export interface CopywritingResponse {
  id: number
  product_id: number | null
  product_name: string | null
  content: string
  source_type: string
  source_ref: string | null
  created_at: string
  updated_at: string
}

export interface CopywritingListResponse {
  total: number
  items: CopywritingResponse[]
}

export interface CopywritingCreate {
  content: string
  product_id?: number | null
  source_type?: string
  source_ref?: string | null
}

// ============ Cover ============

export interface CoverResponse {
  id: number
  video_id: number | null
  file_path: string
  file_size: number | null
  width: number | null
  height: number | null
  created_at: string
}

// ============ Audio ============

export interface AudioResponse {
  id: number
  name: string
  file_path: string
  file_size: number | null
  duration: number | null
  created_at: string
}

// ============ Parse Materials ============

export interface ParseMaterialsResponse {
  success: boolean
  product_id: number
  title: string
  topics: string[]
  videos_downloaded: number
  covers_downloaded: number
  errors: string[]
}

// ============ Topic ============

export interface TopicResponse {
  id: number
  name: string
  heat: number
  source: string
  last_synced: string | null
  created_at: string
}

export interface TopicListResponse {
  total: number
  items: TopicResponse[]
}

export interface TopicCreate {
  name: string
  heat?: number
  source?: string
}

export interface GlobalTopicsResponse {
  topic_ids: number[]
  topics: TopicResponse[]
}

export interface SetGlobalTopicsRequest {
  topic_ids: number[]
}
