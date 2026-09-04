# Vintage Story Helm chart

This chart runs the [DarkMatterProductions Vintage Story image](https://github.com/DarkMatterProductions/vintagestory) as a single Kubernetes Deployment. It follows the image maintainer's guidance: persistent data at `/vintagestory/data`, TCP and UDP on port `42420`, a pinned game version, and no public raw RCON endpoint.

## Install

```bash
helm install vintage-story . \
  --namespace vintage-story \
  --create-namespace \
  --set server.name="My Vintage Story Server"
```

The default `LoadBalancer` Service exposes TCP and UDP port `42420`. Check its address with:

```bash
kubectl get service -n vintage-story vintage-story
```

Clusters without a load balancer can set `service.type=NodePort`. A plain HTTP Ingress cannot carry the game's TCP and UDP traffic.

## Credentials

For production, create a Secret instead of putting passwords in a values file:

```bash
kubectl create secret generic vintage-story-credentials \
  --namespace vintage-story \
  --from-literal=server-password='change-this' \
  --from-literal=rcon-password='change-this-too' \
  --from-literal=rcon-web-secret-key='use-a-long-random-value' \
  --from-literal=rcon-web-password='another-password'

helm upgrade --install vintage-story . \
  --namespace vintage-story \
  --create-namespace \
  --set secrets.existingSecret=vintage-story-credentials
```

The game password is optional. The three RCON values are required only when `rcon.enabled=true`.

## Configuration behavior

The container creates `serverconfig.json` on the first start and preserves it after that. Changing `server.*` values does not rewrite an existing config. To apply those changes, temporarily set `forceRegenerateConfig=true` for one upgrade, wait for a successful start, and set it back to `false`. Regeneration creates `serverconfig.json.backup` on the data volume.

The chart accepts current image options that do not yet have structured values through `extraEnv`. Use `extraEnvVars` when an environment variable comes from a Secret or ConfigMap.

The default resource request follows the official estimate of 1 GiB base memory plus roughly 300 MiB per player for the default 16-player server. Increase memory when adding mods or raising `server.maxClients`.

## RCON web UI

Raw RCON is unencrypted. The chart pins it to `127.0.0.1` inside the pod and does not create a Service for port `42425`. Set `rcon.enabled=true` to enable the bundled web UI. Supply its required secrets, then use its ClusterIP Service or configure `rcon.web.ingress` with TLS.

OAuth stays disabled in the structured defaults. The image maintainer recommends OAuth only behind HTTPS. Its provider settings can be supplied through `extraEnvVars` from a Secret.

## Upgrades and removal

Back up the PVC before changing `image.tag` or `mods`. The image maintainer specifically warns that game and mod upgrades can make worlds incompatible.

The chart-created PVC has `helm.sh/resource-policy: keep` by default, so `helm uninstall` leaves world data behind. Delete it manually only when the data is no longer needed.
