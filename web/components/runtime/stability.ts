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
  map_dom_element: string;
  map_events_connected: string;
  map_pointer_down_left: number;
  map_pointer_down_middle: number;
  map_pointer_down_right: number;
  map_pointer_moves: number;
  map_pointer_ups: number;
  map_contextmenus: number;
  map_pointer_type: string;
  map_pointer_start: [number, number];
  map_pointer_distance_px: number;
  map_control_starts: number;
  map_control_changes: number;
  map_control_ends: number;
  map_pan_changes: number;
  map_rotate_changes: number;
  map_target_clamp_events: number;
  street_queries: number;
  street_changes: number;
  street_candidate_segments: number;
  current_street_id: string | null;
  current_street_name: string | null;
  current_street_distance_m: number | null;
};

export const stability: StabilityState = {
  zero_visible_events: [], longest_zero_visible_ms: 0, tile_requests: 0,
  repeated_tile_requests: 0, tile_state_transitions: 0, focus_request_count: 0,
  focus_transition_starts: 0, focus_transition_completes: 0,
  focus_transition_cancels: 0, lod1_requests: 0, lod1_ready_count: 0,
  lod_handoff_gap_events: 0, pointer_lock_mounts: 0, pointer_lock_unmounts: 0,
  map_dom_element: "UNKNOWN", map_events_connected: "UNKNOWN",
  map_pointer_down_left: 0, map_pointer_down_middle: 0, map_pointer_down_right: 0,
  map_pointer_moves: 0, map_pointer_ups: 0, map_contextmenus: 0,
  map_pointer_type: "", map_pointer_start: [0, 0], map_pointer_distance_px: 0,
  map_control_starts: 0, map_control_changes: 0, map_control_ends: 0,
  map_pan_changes: 0, map_rotate_changes: 0, map_target_clamp_events: 0,
  street_queries: 0, street_changes: 0, street_candidate_segments: 0,
  current_street_id: null, current_street_name: null, current_street_distance_m: null,
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
