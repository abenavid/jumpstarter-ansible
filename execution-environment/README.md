# Execution Environment Build and Publish Guide

This guide explains how to build and publish the Jumpstarter Ansible Execution Environment to your AAP Private Automation Hub on ROSA.

## Prerequisites

1. **ansible-builder** installed:
   ```bash
   pip install ansible-builder
   ```

2. **podman** or **docker** installed (podman recommended for RHEL/ROSA)

3. **Access to your ROSA cluster** with appropriate permissions

4. **Authentication to your AAP Private Automation Hub registry**

## Building the Execution Environment

### Step 1: Navigate to the execution-environment directory

```bash
cd execution-environment
```

### Step 2: Build the EE using ansible-builder

```bash
ansible-builder build -f new-execution-environment.yml -t jumpstarter-ee:latest
```

This will:
- Create a `context/` directory with build artifacts
- Generate a Containerfile
- Build the container image using podman/docker
- Tag the image as `jumpstarter-ee:latest`

### Step 3: Verify the build

```bash
podman images | grep jumpstarter-ee
```

## Finding Your AAP Private Automation Hub URL on ROSA

The AAP Private Automation Hub is typically deployed as part of the Ansible Automation Platform on ROSA. Here's how to find the registry URL:

### Option 1: From OpenShift Console

1. Log into your ROSA OpenShift Console
2. Navigate to **Networking** → **Routes**
3. Filter by namespace (usually `ansible-automation-platform` or similar)
4. Look for routes with names containing:
   - `automation-hub`
   - `galaxy`
   - `registry`
5. The route URL will be in the format: `https://automation-hub-<namespace>.<cluster-domain>`

### Option 2: Using OpenShift CLI

```bash
# List routes in the AAP namespace
oc get routes -n ansible-automation-platform

# Or search for automation hub routes
oc get routes -n ansible-automation-platform | grep -i hub

# Get the registry route specifically
oc get route automation-hub-registry -n ansible-automation-platform -o jsonpath='{.spec.host}'
```

### Option 3: From AAP Controller UI

1. Log into your Ansible Automation Platform Controller
2. Navigate to **Administration** → **Execution Environments**
3. Click on **Registry** or **Private Automation Hub**
4. The registry URL should be displayed in the interface

### Typical URL Format

The registry URL typically looks like:
```
automation-hub-registry-ansible-automation-platform.apps.<cluster-name>.<region>.aroapp.io
```

Or for internal registry:
```
image-registry.openshift-image-registry.svc:5000/ansible-automation-platform
```

## Authenticating to the Registry

### Get Authentication Token

You'll need to authenticate to push images. Get your token:

```bash
# Get your OpenShift token
oc whoami -t

# Or get a service account token
oc create serviceaccount ee-publisher -n ansible-automation-platform
oc policy add-role-to-user system:image-builder system:serviceaccount:ansible-automation-platform:ee-publisher
oc get secret $(oc get sa ee-publisher -n ansible-automation-platform -o jsonpath='{.secrets[0].name}') -n ansible-automation-platform -o jsonpath='{.data.token}' | base64 -d
```

### Login to the Registry

```bash
# Login using podman (AAP Private Automation Hub uses --tls-verify=false)
podman login --tls-verify=false <registry-url> -u <username> -p <token>

# Example for ROSA AAP registry:
# podman login --tls-verify=true dev-sandbox-aap-aap.apps.rosa.sdp.tc3b.p3.openshiftapps.com -u <username> -p <token>

# Or using docker
docker login <registry-url> -u <username> -p <token>
```

## Publishing the Execution Environment

### Step 1: Tag the Image for Your Registry

```bash
# Set your registry URL
REGISTRY_URL="dev-sandbox-aap-aap.apps.rosa.sdp.tc3b.p3.openshiftapps.com"

# Tag the image
podman tag jumpstarter-ee:latest ${REGISTRY_URL}/jumpstarter-ee:latest
podman tag jumpstarter-ee:latest ${REGISTRY_URL}/jumpstarter-ee:$(date +%Y%m%d)
```

### Step 2: Push the Image

```bash
# Push to registry (AAP Private Automation Hub uses --tls-verify=false)
podman push --tls-verify=false ${REGISTRY_URL}/jumpstarter-ee:latest
podman push --tls-verify=false ${REGISTRY_URL}/jumpstarter-ee:$(date +%Y%m%d)
```

### Quick Reference: Complete Publish Workflow

```bash
# 1. Set registry URL
REGISTRY_URL="dev-sandbox-aap-aap.apps.rosa.sdp.tc3b.p3.openshiftapps.com"

# 2. Login to registry
podman login --tls-verify=false ${REGISTRY_URL} -u <username> -p <token>

# 3. Tag the image
podman tag jumpstarter-ee:latest ${REGISTRY_URL}/jumpstarter-ee:latest

# 4. Push the image
podman push --tls-verify=false ${REGISTRY_URL}/jumpstarter-ee:latest
```

### Step 3: Verify in AAP

1. Log into your Ansible Automation Platform Controller
2. Navigate to **Administration** → **Execution Environments**
3. You should see your `jumpstarter-ee` image listed
4. You can also check in **Resources** → **Private Automation Hub** → **Execution Environments**

## Alternative: Using ansible-builder with Registry

You can also build and push in one step:

```bash
# Build and push directly
REGISTRY_URL="dev-sandbox-aap-aap.apps.rosa.sdp.tc3b.p3.openshiftapps.com"

ansible-builder build -f new-execution-environment.yml \
  -t ${REGISTRY_URL}/jumpstarter-ee:latest \
  --container-runtime podman

podman push --tls-verify=false ${REGISTRY_URL}/jumpstarter-ee:latest
```

## Troubleshooting

### Authentication Issues

If you get authentication errors:
- Verify your token is valid: `oc whoami -t`
- Check token expiration
- Ensure you have `image-builder` role in the namespace

### Registry Not Found

If you can't find the registry route:
- Check if AAP is fully installed: `oc get pods -n ansible-automation-platform`
- Verify the automation-hub operator is running
- Check route creation: `oc get routes -n ansible-automation-platform --all-namespaces`

### Push Permission Denied

If push fails:
- Verify namespace permissions: `oc auth can-i push images -n ansible-automation-platform`
- Check if you need to create an ImageStream first:
  ```bash
  oc create imagestream jumpstarter-ee -n ansible-automation-platform
  ```

## Using the EE in Ansible Navigator

After publishing, you can use the EE in your playbooks:

```yaml
# ansible-navigator.yml
---
ansible-navigator:
  execution-environment:
    image: ${REGISTRY_URL}/jumpstarter-ee:latest
    pull:
      policy: always
```

Or reference it directly in your playbook runs:

```bash
REGISTRY_URL="dev-sandbox-aap-aap.apps.rosa.sdp.tc3b.p3.openshiftapps.com"

ansible-navigator run playbook.yml \
  --eei ${REGISTRY_URL}/jumpstarter-ee:latest
```
