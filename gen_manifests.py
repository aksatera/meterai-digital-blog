#!/usr/bin/env python3
"""Generate all K3s manifests for Meterai Digital Blog"""
import subprocess, os

os.chdir("/opt/data/meterai-digital-blog")
os.makedirs("k8s", exist_ok=True)

# Generate htpasswd
p1 = subprocess.run(["openssl", "passwd", "-apr1", "PatriaBlog2024"], capture_output=True, text=True)
p2 = subprocess.run(["openssl", "passwd", "-apr1", "NuzulBlog2024"], capture_output=True, text=True)
htpasswd = f"patria:{p1.stdout.strip()}\nnuzul:{p2.stdout.strip()}"
print("htpasswd generated")

# Secret
secret = f"""apiVersion: v1
kind: Secret
metadata:
  name: blog-credentials
  namespace: mdi
type: Opaque
stringData:
  auth: |
{chr(10).join('    ' + line for line in htpasswd.splitlines())}
  GITHUB_PAT: "****"
  HUGO_PAT: "****"
"""
with open("k8s/secret.yaml", "w") as f:
    f.write(secret)

# ConfigMap
with open("k8s/configmap.yaml", "w") as f:
    f.write("""apiVersion: v1
kind: ConfigMap
metadata:
  name: blog-nginx-config
  namespace: mdi
data:
  default.conf: |
    server {
        listen 80;
        root /usr/share/nginx/html;
        location /healthz { return 200 "ok"; }
        location /admin/ { index index.html; try_files $uri $uri/ =404; }
        location / { try_files $uri $uri/ $uri.html =404; }
    }
""")

# Deployment
with open("k8s/deployment.yaml", "w") as f:
    f.write("""apiVersion: apps/v1
kind: Deployment
metadata:
  name: meterai-blog
  namespace: mdi
spec:
  replicas: 1
  selector:
    matchLabels:
      app: meterai-blog
  template:
    metadata:
      labels:
        app: meterai-blog
    spec:
      initContainers:
      - name: hugo-build
        image: klakegg/hugo:latest
        env:
        - name: GITHUB_PAT
          valueFrom:
            secretKeyRef:
              name: blog-credentials
              key: HUGO_PAT
        command:
        - sh
        - -c
        - |
          git config --global user.email "contact@aksatera.co.id"
          git config --global user.name "IT Support"
          git clone https://aksatera:${GITHUB_PAT}@github.com/aksatera/meterai-digital-blog.git /src
          cd /src
          hugo --minify
          cp -r public/* /output/
        volumeMounts:
        - name: site-data
          mountPath: /output
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: site-data
          mountPath: /usr/share/nginx/html
          readOnly: true
        - name: nginx-config
          mountPath: /etc/nginx/conf.d/default.conf
          subPath: default.conf
          readOnly: true
        resources:
          requests:
            cpu: 20m
            memory: 32Mi
          limits:
            cpu: 100m
            memory: 64Mi
      volumes:
      - name: site-data
        emptyDir: {}
      - name: nginx-config
        configMap:
          name: blog-nginx-config
""")

# Service
with open("k8s/service.yaml", "w") as f:
    f.write("""apiVersion: v1
kind: Service
metadata:
  name: meterai-blog
  namespace: mdi
spec:
  selector:
    app: meterai-blog
  ports:
  - port: 80
    targetPort: 80
""")

# Ingress
with open("k8s/ingress.yaml", "w") as f:
    f.write("""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: meterai-blog
  namespace: mdi
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - blog.meterai.digital
    secretName: blog-meterai-tls
  rules:
  - host: blog.meterai.digital
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: meterai-blog
            port:
              number: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: meterai-blog-admin
  namespace: mdi
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: blog-credentials
    nginx.ingress.kubernetes.io/auth-realm: "Meterai Digital Admin"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - admin.blog.meterai.digital
    secretName: admin-blog-meterai-tls
  rules:
  - host: admin.blog.meterai.digital
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: meterai-blog
            port:
              number: 80
""")

print("All manifests generated successfully")
for f in os.listdir("k8s"):
    print(f"  k8s/{f}")
