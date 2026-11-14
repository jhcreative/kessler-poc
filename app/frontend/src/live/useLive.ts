// One live connection per view. Order matters, so nothing falls in a gap:
//   1. open the socket, and buffer what arrives;
//   2. on "hello", load the list over HTTP, then apply the buffer (the store ignores anything older);
//   3. after that, apply frames as they come.
// On a drop, reconnect with backoff and ask for everything after the last event seen. On "resync", reload the list.
import { useEffect, useReducer, useRef, useState } from "react";
import { api } from "../api/client";
import type { Job, LiveEvent, LiveMessage } from "../api/types";
import { apply, empty, load, type LiveState } from "./store";

export type LiveStatus = "connecting" | "live" | "reconnecting";

type Action = { kind: "load"; jobs: Job[]; buffered: LiveEvent[] } | { kind: "event"; msg: LiveEvent };

export function useLive(opts: {
  query?: string;
  inScope?: (job: Job) => boolean;
  onSignedOut: () => void;
  // Reload the list after a drop instead of replaying (cold review, finding 2): replay is filtered by who holds a
  // job now, so a job reassigned away while a tech was offline would never be replayed to them. A tech's list is
  // short; a reload is cheap and always right.
  reloadOnReconnect?: boolean;
}) {
  const { query = "", inScope, onSignedOut, reloadOnReconnect = false } = opts;
  const scope = useRef(inScope);
  scope.current = inScope;
  const [state, dispatch] = useReducer((s: LiveState, a: Action): LiveState => {
    if (a.kind === "load") return load(a.jobs, a.buffered, scope.current);
    return apply(s, a.msg, scope.current ? { inScope: scope.current } : {});
  }, empty);
  const [status, setStatus] = useState<LiveStatus>("connecting");
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const last = useRef(0);
  last.current = state.lastEventId;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let stopped = false;
    let attempt = 0;
    let timer: number | undefined;
    let listLoaded = false;
    let buffer: LiveEvent[] = [];

    const connect = () => {
      const after = listLoaded ? `?after=${last.current}` : "";
      const proto = location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${proto}://${location.host}/api/ws${after}`);
      socket.onmessage = (frame) => {
        const msg = JSON.parse(String(frame.data)) as LiveMessage;
        if (msg.type === "hello") {
          attempt = 0;
          setStatus("live");
          if (!listLoaded) {
            api
              .jobs(query)
              .then((jobs) => {
                listLoaded = true;
                dispatch({ kind: "load", jobs, buffered: buffer });
                buffer = [];
                setLoaded(true);
                setError(null);
              })
              .catch((e: unknown) => setError(e instanceof Error ? e.message : "The jobs didn't load"));
          }
        } else if (msg.type === "event") {
          if (listLoaded) dispatch({ kind: "event", msg });
          else buffer.push(msg);
        } else if (msg.type === "resync") {
          listLoaded = false; // the next hello reloads the list
        }
      };
      socket.onclose = (ev) => {
        if (stopped) return;
        if (ev.code === 4401) return onSignedOut();
        setStatus("reconnecting");
        if (reloadOnReconnect) listLoaded = false;
        attempt += 1;
        timer = window.setTimeout(connect, Math.min(10_000, 500 * 2 ** attempt));
      };
    };
    connect();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
      socket?.close();
    };
  }, [query, onSignedOut, reloadOnReconnect]);

  return { state, status, loaded, error };
}
