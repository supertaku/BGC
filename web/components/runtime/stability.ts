import type { NavigationMode } from "./types";

export type StabilityEvent = { start_ms: number; end_ms: number | null; duration_ms: number; mode: NavigationMode; camera: [number, number, number]; anchors: { x: number; z: number; role: string }[]; active_ids: string[]; preloading: number };
export type StabilityState = {
  zero_visible_events: StabilityEvent[];
  longest_zero_visible_ms: number;
  tile_requests: number;
  repeated_tile_requests: number;
  tile_state_transitions: number;
  focus_request_count: number;
  focus_transition_starts: number;
  focus_transition_completes: number;
  focus_transition_cancels: number;
  lod1_requests: number;
  lod1_ready_count: number;
  lod_handoff_gap_events: number;
  pointer_lock_mounts: number;
  pointer_lock_unmounts: number;
};

export const stability: StabilityState = {
  zero_visible_events: [], longest_zero_visible_ms: 0, tile_requests: 0,
  repeated_tile_requests: 0, tile_state_transitions: 0, focus_request_count: 0,
  focus_transition_starts: 0, focus_transition_completes: 0,
  focus_transition_cancels: 0, lod1_requests: 0, lod1_ready_count: 0,
  lod_handoff_gap_events: 0, pointer_lock_mounts: 0, pointer_lock_unmounts: 0,
};

export function observeVisibility(ready: boolean, visible: number, now: number, context: Omit<StabilityEvent, "start_ms" | "end_ms" | "duration_ms">) {
  const current = stability.zero_visible_events.at(-1);
  if (ready && visible === 0) {
    if (!current || current.end_ms !== null) stability.zero_visible_events.push({ ...context, start_ms: now, end_ms: null, duration_ms: 0 });
    else current.duration_ms = now - current.start_ms;
    stability.longest_zero_visible_ms = Math.max(stability.longest_zero_visible_ms, stability.zero_visible_events.at(-1)!.duration_ms);
  } else if (current?.end_ms === null) {
    current.end_ms = now;
    current.duration_ms = now - current.start_ms;
    stability.longest_zero_visible_ms = Math.max(stability.longest_zero_visible_ms, current.duration_ms);
  }
}
