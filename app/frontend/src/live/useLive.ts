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

export function useLive(opts: { query?: string; inScope?: (job: Job) => boolean; onSignedOut: () => void }) {
  const { query = "", inScope, onSignedOut } = opts;
  const scope = useRef(inScope);
  scope.current = inScope;
  const [state, dispatch] = useReducer((s: LiveState, a: Action): LiveState => {
    if (a.kind === "load") return load(a.jobs, a.buffered);
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
  }, [query, onSignedOut]);

  return { state, status, loaded, error };
}
