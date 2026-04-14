export type AuthState =
  | 'unauthenticated'
  | 'authorizing'
  | 'authenticated_active'
  | 'authenticated_grace'
  | 'refresh_required'
  | 'revoked'
  | 'device_mismatch'
  | 'expired'
  | 'error'

export type AuthBootstrapStatus = 'loading' | 'ready' | 'error'

export interface LocalAuthSessionSummary {
  auth_state: AuthState
  remote_user_id?: string | null
  display_name?: string | null
  license_status?: string | null
  entitlements: string[]
  expires_at?: string | null
  last_verified_at?: string | null
  offline_grace_until?: string | null
  denial_reason?: string | null
  device_id?: string | null
}

export interface AuthStatusResponse {
  auth_state: AuthState
  remote_user_id?: string | null
  display_name?: string | null
  license_status?: string | null
  device_id?: string | null
  denial_reason?: string | null
  expires_at?: string | null
  last_verified_at?: string | null
  offline_grace_until?: string | null
  token_expires_in_seconds?: number | null
  grace_remaining_seconds?: number | null
  is_authenticated: boolean
  is_active: boolean
  is_grace: boolean
  requires_reauth: boolean
  can_read_local_data: boolean
  can_run_protected_actions: boolean
  can_run_background_tasks: boolean
}

export interface AdminSessionResponse {
  session_id: number
  auth_state: AuthState
  remote_user_id?: string | null
  display_name?: string | null
  license_status?: string | null
  device_id?: string | null
  denial_reason?: string | null
  expires_at?: string | null
  last_verified_at?: string | null
  offline_grace_until?: string | null
  has_access_token: boolean
  has_refresh_token: boolean
  is_current_session: boolean
  created_at?: string | null
  updated_at?: string | null
}
