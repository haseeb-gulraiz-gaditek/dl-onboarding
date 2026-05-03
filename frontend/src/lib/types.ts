// Mesh — shared types
// Co-located with mock data; backend can replace with API responses of the same shape.

export type Axis = "role" | "tool" | "problem" | "domain";

export interface User {
  id: string;
  name: string;
  role: string;
  avatar: string; // initial or short string
  tags: string[];
}

export interface Tool {
  id: string;
  name: string;
  tag: string;
  category?: string;
  delta?: number; // % change in adoption among peers (positive = rising)
  peerPct?: number; // % of peers in same role using it
  why?: string;
}

export interface Community {
  id: string;
  name: string; // e.g. "r/staff-pms"
  axis: Axis;
  members: number | string;
  online?: number;
  pulse?: "high" | "med" | "cool";
  desc?: string;
}

export interface ThreadAuthor {
  name: string;
  tag: string;
  avatar: string;
}

export interface Thread {
  id: string;
  kind: "hot" | "sticky" | "discussion" | "discovery";
  author: ThreadAuthor;
  when: string;
  title: string;
  body: string;
  tags: string[];
  upvotes: number;
  replies: number;
  online: number;
  pulse: "high" | "med" | "cool";
  isAuto?: boolean;
}

export interface ConciergeMessage {
  id: string;
  kind: "finding" | "evidence" | "math" | "recommendation";
  when: string;
  text: string;
  evidence?: { who: string; said: string }[];
}

export interface ConciergeThread {
  id: string;
  topic: string;
  unread?: boolean;
  when: string;
  messages: ConciergeMessage[];
}
