# Multi-Port Service and Ingress Configuration

This Helm chart supports multiple service ports with per-path port selection in ingress.

## Service Configuration

### Single Port (Default - Backward Compatible)

```yaml
service:
  type: ClusterIP
  port: 80
  targetPort: 5000
```

### Multi-Port Configuration

```yaml
service:
  type: ClusterIP
  ports:
    - name: http
      port: 80
      targetPort: 5000
      protocol: TCP
    - name: websocket
      port: 9000
      targetPort: 9000
      protocol: TCP
```

## Ingress Configuration with Port Selection

### Using portName (Recommended)

Reference service ports by name in your ingress paths:

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
  hosts:
    - host: api.example.com
      paths:
        - path: /backend/luma-syncer/http
          pathType: Prefix
          portName: http  # References service port named "http"
        - path: /backend/luma-syncer/websocket
          pathType: Prefix
          portName: websocket  # References service port named "websocket"
```

### Using portNumber (Alternative)

You can also specify the port number directly:

```yaml
ingress:
  enabled: true
  hosts:
    - host: api.example.com
      paths:
        - path: /backend/luma-syncer
          pathType: Prefix
          portNumber: 80  # Explicit port number
```

### Default Behavior (Backward Compatible)

If neither `portName` nor `portNumber` is specified, it defaults to `service.port`:

```yaml
ingress:
  enabled: true
  hosts:
    - host: api.example.com
      paths:
        - path: /backend/luma-syncer
          pathType: Prefix
          # Uses service.port (80) by default
```

## Complete Example

Here's a complete example similar to your OCPP configuration:

```yaml
service:
  type: ClusterIP
  ports:
    - name: http
      port: 80
      targetPort: 5000
      protocol: TCP
    - name: websocket
      port: 9000
      targetPort: 9000
      protocol: TCP

ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/force-ssl-redirect: 'true'
    nginx.ingress.kubernetes.io/use-regex: 'true'
  hosts:
    - host: api.example.com
      paths:
        - path: /backend/luma-syncer/http
          pathType: Prefix
          portName: http
        - path: /backend/luma-syncer/websocket
          pathType: Prefix
          portName: websocket
  tls:
    - hosts:
        - api.example.com
      secretName: luma-syncer-tls
```

## Current Production Configuration

Your current `values-prod.yaml` uses a single port with a path prefix:

```yaml
service:
  # Uses default single port (80 -> 5000)

ingress:
  enabled: true
  hosts:
    - host: ""
      paths:
        - path: /backend/luma-syncer
          pathType: Prefix
          # Uses service.port (80) by default
```

This will work as-is. If you want to add multiple ports later, just:
1. Add `ports:` to the service section
2. Add `portName:` to the ingress paths

## Notes

- When using `portName`, the port name must match a port name defined in `service.ports`
- If `portName` is specified but the service uses single-port config, it will fall back to `service.port`
- The chart maintains backward compatibility - existing single-port configurations will continue to work

