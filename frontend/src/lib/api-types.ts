// TypeScript interfaces mirroring app/models/* Pydantic shapes.
// Hand-maintained for V1; OpenAPI codegen is V1.5 work.

// ---- Auth ----

export type RoleType = "user" | "founder";

export interface UserPublic {
  id: string;
  email: string;
  role_type: RoleType;
  display_name: string;
  created_at: string;
  last_active_at: string;
  onboarding_variant?: "classic" | "live";   // F-LIVE-9
}

export interface AuthResponse {
  jwt: string;
  user: UserPublic;
}

// ---- Questions / Answers ----

export type QuestionKind = "single_select" | "multi_select" | "free_text";

export interface QuestionOption {
  value: string;
  label: string;
}

export interface QuestionPayload {
  id: string;
  key: string;
  text: string;
  kind: QuestionKind;
  category: string;
  order: number;
  options: QuestionOption[];
}

export interface NextQuestionResponse {
  done: boolean;
  question: QuestionPayload | null;     // null when done=true
}

export interface AnswerCreateRequest {
  question_id: string;
  value: string | string[];              // string for single_select / free_text; list for multi_select
}

// ---- Recommendations ----

export interface OnboardingToolCard {
  slug: string;
  name: string;
  tagline: string;
  description: string;
  url: string;
  pricing_summary: string;
  category: string;
  labels: string[];
}

export type Verdict = "try" | "skip";

export interface RecommendationPick {
  tool: OnboardingToolCard;
  verdict: Verdict;
  reasoning: string;
  score: number;
}

export interface RecommendationsResponse {
  recommendations: RecommendationPick[];
  launches: RecommendationPick[];
  generated_at: string;
  from_cache: boolean;
  degraded: boolean;
}

// ---- Communities ----

export type CommunityCategory = "role" | "stack" | "outcome";

export interface CommunityCard {
  id: string;
  slug: string;
  name: string;
  description: string;
  category: CommunityCategory;
  member_count: number;
}

export interface JoinedCommunityCard extends CommunityCard {
  joined_at: string;
}

export interface CommunityListResponse {
  communities: CommunityCard[];
}

export interface JoinedCommunityListResponse {
  communities: JoinedCommunityCard[];
}

// ---- User tools (cycle #10) ----

export type UserToolStatus = "using" | "saved";
export type UserToolSource =
  | "auto_from_profile"
  | "explicit_save"
  | "manual_add";

export interface ToolCardWithFlags extends OnboardingToolCard {
  vote_score: number;
  is_founder_launched: boolean;
}

export interface UserToolCard {
  id: string;
  tool: ToolCardWithFlags;
  source: UserToolSource;
  status: UserToolStatus;
  added_at: string;
  last_updated_at: string;
}

export interface UserToolListResponse {
  tools: UserToolCard[];
}

// ---- Profile summary (cycle #13 audit pass) ----

export interface StackToolEntry {
  value: string;
  label: string;
}

export interface ProfileSummaryResponse {
  stack_tools: StackToolEntry[];
  all_answer_values: string[];
}

// ---- Founder dashboard (cycle #11) ----

export type VerificationStatus = "pending" | "approved" | "rejected";

export interface DashboardLaunchCard {
  launch_id: string;
  product_url: string;
  approved_tool_slug: string | null;
  verification_status: VerificationStatus;
  created_at: string;
  matched_count: number;
  tell_me_more_count: number;
  skip_count: number;
  total_clicks: number;
}

export interface DashboardResponse {
  dashboard: DashboardLaunchCard[];
}

// ---- Per-launch analytics (cycle #11 F-DASH-3) ----

export interface LaunchAnalyticsResponse {
  launch_id: string;
  approved_tool_slug: string | null;
  verification_status: VerificationStatus;
  matched_count: number;
  tell_me_more_count: number;
  skip_count: number;
  total_clicks: number;
  clicks_by_community: Record<string, number>;
  clicks_by_surface: Record<string, number>;
}

// ---- Posts / comments / votes (cycle #7) ----

export interface PostAuthor {
  id: string;
  display_name: string;
}

export interface PostCard {
  id: string;
  community_slug: string;
  cross_posted_to: string[];
  author: PostAuthor;
  title: string;
  body_md: string;
  attached_launch_id: string | null;
  vote_score: number;
  comment_count: number;
  user_vote: number;     // -1, 0, 1
  flagged: boolean;
  created_at: string;
  last_activity_at: string;
}

export interface PostListResponse {
  posts: PostCard[];
  next_before: string | null;   // cursor on created_at
}

export interface PostCreateRequest {
  community_slug: string;
  cross_post_slugs?: string[];
  title: string;
  body_md?: string;
}

export interface VoteRequest {
  target_type: "post" | "comment" | "tool";
  target_id: string;
  direction: 1 | -1;
}

export interface VoteResponse {
  voted: boolean;
  current_direction: number;
}

export interface CommunityDetailResponse {
  community: CommunityCard;
  is_member: boolean;
}

// ---- Tools browse (cycle #10) ----

export interface ToolsBrowseResponse {
  tools: ToolCardWithFlags[];
  next_before: string | null;     // cursor on `name`
}

export interface BrowsedLaunchMeta {
  founder_display_name: string;
  problem_statement: string;
  approved_at: string | null;
}

export interface BrowsedLaunchCard {
  tool: ToolCardWithFlags;
  launch_meta: BrowsedLaunchMeta;
  in_my_communities: string[];
}

export interface BrowsedLaunchListResponse {
  launches: BrowsedLaunchCard[];
  next_before: string | null;     // cursor on reviewed_at
}

// ---- Admin launches (cycle #8) ----

export interface LaunchAdminCard {
  id: string;
  founder_email: string;
  product_url: string;
  problem_statement: string;
  verification_status: VerificationStatus;
  created_at: string;
}

export interface LaunchAdminListResponse {
  launches: LaunchAdminCard[];
}

export interface LaunchAdminDetail {
  id: string;
  founder_email: string;
  founder_user_id: string;
  product_url: string;
  problem_statement: string;
  icp_description: string;
  existing_presence_links: string[];
  target_community_slugs: string[];
  verification_status: VerificationStatus;
  rejection_comment: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  approved_tool_slug: string | null;
  created_at: string;
}

// ---- Admin catalog (cycle #3) ----

export interface AdminCatalogTool {
  slug: string;
  name: string;
  tagline: string;
  description: string;
  url: string;
  pricing_summary: string;
  category: string;
  labels: string[];
  curation_status: "pending" | "approved" | "rejected";
  rejection_comment: string | null;
  source: string;
}

export interface AdminCatalogListResponse {
  tools: AdminCatalogTool[];
}

// ---- Notifications mark-all-read (cycle #12 F-NOTIF-6) ----

export interface MarkAllReadResponse {
  updated: number;
}

// ---- Notifications (cycle #12) ----

export interface NotificationCard {
  id: string;
  kind: string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: NotificationCard[];
  next_before: string | null;
}

export interface UnreadCountResponse {
  count: number;
}

export interface BannerResponse {
  notification: NotificationCard | null;
}

// ---- Product page (cycle #9 F-PUB-4) ----

export interface ProductCard {
  slug: string;
  name: string;
  tagline: string;
  description: string;
  url: string;
  pricing_summary: string;
  category: string;
  labels: string[];
  vote_score: number;
  is_founder_launched: boolean;
}

export interface LaunchMeta {
  founder_email: string;
  founder_display_name: string;
  problem_statement: string;
  icp_description: string;
  approved_at: string | null;
}

export interface ProductPageResponse {
  tool: ProductCard;
  launch: LaunchMeta | null;
}

// ---- Founder launch submission ----

export interface LaunchSubmitRequest {
  product_url: string;
  problem_statement: string;
  icp_description: string;
  existing_presence_links: string[];
  target_community_slugs: string[];
}

export interface LaunchResponse {
  id: string;
  product_url: string;
  problem_statement: string;
  icp_description: string;
  existing_presence_links: string[];
  target_community_slugs: string[];
  verification_status: "pending" | "approved" | "rejected";
  rejection_comment: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  approved_tool_slug: string | null;
  created_at: string;
  publish_summary?: { community_posts_count: number; nudge_count: number } | null;
}

// ---- Live-narrowing onboarding (cycle #15) ----

export type LiveQuestionKind = "dropdowns_3" | "multi_select" | "single_select";

export interface LiveOption {
  value: string;
  label: string;
}

export interface LiveQuestion {
  q_index: 1 | 2 | 3 | 4;
  key: string;
  text: string;
  helper?: string | null;
  kind: LiveQuestionKind;
  sub_dropdowns?: Record<string, LiveOption[]> | null;
  options?: LiveOption[] | null;
  options_per_role?: Record<string, LiveOption[]> | null;
  fallback_options?: LiveOption[] | null;
}

export interface LiveQuestionsResponse {
  questions: LiveQuestion[];
}

export interface LiveOptionsResponse {
  options: LiveOption[];
  role_key_resolved: string;
}

export type LiveAnswerValue =
  | { job_title: string; level: string; industry: string }
  | { selected_values: string[] }
  | { selected_value: string };

export interface LiveStepRequest {
  q_index: 1 | 2 | 3 | 4;
  answer_value: LiveAnswerValue;
}

export interface LiveStepTool {
  slug: string;
  name: string;
  tagline?: string | null;
  category?: string | null;
  score: number;
  layer: "general" | "relevant" | "niche" | null;
  reasoning_hook: string;
}

export interface LiveStepResponse {
  step: number;
  top: LiveStepTool[];
  wildcard: LiveStepTool | null;
  count_kept: number;
  degraded: boolean;
}
