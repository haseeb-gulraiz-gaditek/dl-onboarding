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
