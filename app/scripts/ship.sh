#!/usr/bin/env bash
# Ship the app to the JHC apps box, behind its shared edge Caddy (Tailor HOST-02), the IMAGES=local way: build here,
# `docker save | ssh docker load`, no registry and no CI (reference: deploy without GitHub).
#
#   scripts/ship.sh --box <ssh-host> --dry-run          everything local: gate, amd64 images, compose check. No ssh.
#   scripts/ship.sh --box <ssh-host> --first            first deploy: also routes the domain at the edge, seeds,
#                                                        and sets the demo logins
#   scripts/ship.sh --box <ssh-host>                    a redeploy of the current commit
#   scripts/ship.sh --box <ssh-host> --rollback <tag>   back to an earlier tag's images (still on the box)
#
# OPS-5: a real run (anything but --dry-run) happens on John's go, after the gate and the cold review are green, and
# only with a fresh snapshot: set SNAPSHOT_TAKEN=yes once Rob has taken it (ovh-vps.py, one slot). The deploy and its
# rollback are one pair.
#
# Before the first deploy, Rob prepares the box once (it isn't scripted, because the secrets are John's):
#   /srv/ofs/.env (0600): COMPOSE_FILE=docker-compose.yml:docker-compose.edge.yml, POSTGRES_PASSWORD, SESSION_SECRET
#     (48+ chars, new for the box), COOKIE_SECURE=1, ALLOWED_ORIGINS=https://ofs.apps.johnhiemstra.com,
#     TRUSTED_PROXY=10.240.0.2/32, ANTHROPIC_ENV_FILE=/srv/ofs/anthropic.env, OFS_TAG=
#   /srv/ofs/anthropic.env (0600), /srv/ofs/demo-logins.env (0600: five new email=password lines)
#   the edge itself: /srv/_edge/edge.sh ensure --email <acme email> (Tailor's provision-site.sh --edge installs it)
#
# Every step ends on a gate; the first failure stops the run and says what to do.
set -euo pipefail
cd "$(dirname "$0")/.."
DOMAIN=ofs.apps.johnhiemstra.com
REMOTE=/srv/ofs
BOX=""; FIRST=0; DRY=0; ROLLBACK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --box) BOX="$2"; shift 2 ;;
    --first) FIRST=1; shift ;;
    --dry-run) DRY=1; shift ;;
    --rollback) ROLLBACK="$2"; shift 2 ;;
    *) sed -n '2,24p' "$0"; exit 2 ;;
  esac
done
[ -n "$BOX" ] || { echo "STOP: --box <ssh-host> is required"; exit 2; }
fail() { echo "STOP: $*" >&2; exit 1; }
on_box() { ssh -o BatchMode=yes "$BOX" "$@"; }

if [ -n "$ROLLBACK" ]; then
  [ "${SNAPSHOT_TAKEN:-}" = yes ] || fail "OPS-5: no rollback without John's go and SNAPSHOT_TAKEN=yes"
  on_box "docker image inspect ofs-backend:$ROLLBACK ofs-web:$ROLLBACK >/dev/null" || fail "the box doesn't hold tag $ROLLBACK"
  on_box "cd $REMOTE && sed -i 's/^OFS_TAG=.*/OFS_TAG=$ROLLBACK/' .env && docker compose up -d --wait --no-build"
  echo "rolled back to $ROLLBACK; run scripts/check-live.py https://$DOMAIN --logins <file>"
  exit 0
fi

# 1. The commit is clean, and the gate is green on it.
[ -z "$(git status --porcelain -- .)" ] || fail "app/ has uncommitted changes: ship a commit, not a working tree"
TAG="$(git rev-parse --short HEAD)"
echo "== 1. gate at $TAG"; scripts/gate.sh >/dev/null || fail "the gate is red at $TAG"

# 2. Images for the box's architecture (x86_64), tagged with the commit.
echo "== 2. images ofs-backend:$TAG ofs-web:$TAG (linux/amd64)"
docker buildx build --platform linux/amd64 -t "ofs-backend:$TAG" --load backend >/dev/null
docker buildx build --platform linux/amd64 -t "ofs-web:$TAG" --load frontend >/dev/null
for i in "ofs-backend:$TAG" "ofs-web:$TAG"; do
  [ "$(docker image inspect -f '{{.Architecture}}' "$i")" = amd64 ] || fail "$i isn't amd64"
  ! docker history --no-trunc "$i" | grep -qiE "sk-ant|SESSION_SECRET=|POSTGRES_PASSWORD=" || fail "$i carries a secret in a layer"
done

# 3. The box's compose files parse together (edge network declared, no host ports).
echo "== 3. compose with the edge override"
OFS_TAG="$TAG" POSTGRES_PASSWORD=x SESSION_SECRET=x docker compose -f docker-compose.yml -f docker-compose.edge.yml config -q
if [ "$DRY" = 1 ]; then echo "dry run: local steps green at $TAG; nothing sent to $BOX"; exit 0; fi

# 4. John's go, a snapshot, and a box that's ready.
[ "${SNAPSHOT_TAKEN:-}" = yes ] || fail "OPS-5: a real run needs John's go and a fresh snapshot (SNAPSHOT_TAKEN=yes)"
echo "== 4. box $BOX"
on_box "test -x /srv/_edge/edge.sh" || fail "no edge on $BOX: run Tailor's provision-site.sh --edge, or edge.sh ensure"
on_box "test -f $REMOTE/.env && test -f $REMOTE/anthropic.env" || fail "$REMOTE/.env or anthropic.env missing: Rob prepares them (header)"
on_box "grep -q '^COOKIE_SECURE=1' $REMOTE/.env && grep -q '^TRUSTED_PROXY=10.240.0.2/32' $REMOTE/.env" \
  || fail "$REMOTE/.env must set COOKIE_SECURE=1 and TRUSTED_PROXY=10.240.0.2/32"
if [ "$FIRST" = 1 ]; then on_box "/srv/_edge/edge.sh free $DOMAIN" || fail "$DOMAIN is already routed: this isn't a first deploy"; fi

# 5. Ship the images and the compose files; start the new tag.
echo "== 5. load and start $TAG"
docker save "ofs-backend:$TAG" "ofs-web:$TAG" | gzip | on_box "gunzip | docker load" >/dev/null
scp -q docker-compose.yml docker-compose.edge.yml "$BOX:$REMOTE/"
on_box "cd $REMOTE && sed -i 's/^OFS_TAG=.*/OFS_TAG=$TAG/' .env && docker compose up -d --wait --no-build"

# 6. First deploy: the route, the data, the logins.
if [ "$FIRST" = 1 ]; then
  echo "== 6. route $DOMAIN at the edge; seed; logins"
  on_box "/srv/_edge/edge.sh add $DOMAIN"
  on_box "cd $REMOTE && docker compose exec -T backend python -m ofs.seed"
  on_box "cd $REMOTE && docker compose run --rm -T -v $REMOTE/demo-logins.env:/tmp/logins.env:ro backend python -m ofs.logins --file /tmp/logins.env"
fi
on_box "/srv/_edge/edge.sh check $DOMAIN" || fail "the edge doesn't route $DOMAIN to exactly one container"

echo "shipped $TAG to $BOX. Now: scripts/check-live.py https://$DOMAIN --logins <the box's logins file>"
