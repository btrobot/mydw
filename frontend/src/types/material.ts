/**
 * Material/Product/Topic domain types
 *
 * Prefer generated API types as the source of truth.
 * This file now acts as a compatibility re-export surface for existing imports.
 */

export type {
  AudioResponse,
  CopywritingCreate,
  CopywritingListResponse,
  CopywritingResponse,
  CoverResponse,
  GlobalTopicResponse as GlobalTopicsResponse,
  ProductCreate,
  ProductDetailResponse,
  ProductListResponse,
  ProductMaterialsResponse,
  ProductResponse,
  TopicCreate,
  TopicGroupCreate,
  TopicGroupListResponse,
  TopicGroupResponse,
  TopicGroupUpdate,
  TopicListResponse,
  TopicResponse,
  VideoCreate,
  VideoListResponse,
  VideoResponse,
} from '@/api'

export type BatchDeleteResponse = import('@/api').SchemasBatchDeleteResponse
export type ParseStatus = 'pending' | 'parsing' | 'parsed' | 'error'

export interface ParseMaterialsResponse {
  videos_downloaded: number
  covers_downloaded: number
  topics: Array<{ id?: number; name?: string } | string>
}

export interface SetGlobalTopicsRequest {
  topic_ids: number[]
}
