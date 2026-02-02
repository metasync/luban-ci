import os
import hmac
import hashlib
import json
import urllib.request
import urllib.error
import ssl
import subprocess
import base64
import time

def get_secret():
    """Retrieve the webhook secret from Kubernetes."""
    cmd = [
        "kubectl", "get", "secret", "github-webhook-secret",
        "-n", "luban-ci",
        "-o", "jsonpath={.data.secret}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return base64.b64decode(result.stdout).decode('utf-8').strip()

def send_webhook(secret, gateway_url, payload):
    """Send the signed webhook request."""
    body = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={signature}",
        "X-GitHub-Event": "push",
        "User-Agent": "GitHub-Hookshot/test"
    }
    
    print(f"Sending webhook to {gateway_url}...")
    
    # Create a context that ignores self-signed certs (equivalent to verify=False)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(gateway_url, data=body.encode('utf-8'), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            print(f"Response Status: {response.status}")
            print(f"Response Body: {response.read().decode('utf-8')}")
            
            if response.status == 200:
                print("\nWebhook delivered successfully!")
                return True
            else:
                print("\nWebhook delivery failed.")
                return False
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        try:
            print(f"Response Body: {e.read().decode('utf-8')}")
        except:
            print("Response Body: <empty or non-utf8>")
        return False
    except Exception as e:
        print(f"Error sending request: {e}")
        return False

def check_workflow():
    """Check for the latest triggered workflow."""
    print("\nChecking for triggered workflows...")
    cmd = [
        "kubectl", "get", "wf", "-n", "luban-ci",
        "--sort-by=.metadata.creationTimestamp"
    ]
    subprocess.run(cmd)

def main():
    gateway_url = os.environ.get("GATEWAY_URL", "https://webhook.luban.metasync.cc/push")
    repo_url = os.environ.get("REPO_URL", "https://github.com/metasync/luban-hello-world-py.git")
    revision = os.environ.get("REVISION", "main")
    tag = os.environ.get("TAG", "")
    app_name = os.environ.get("APP_NAME", "luban-hello-world-py")
    
    # Construct payload matching the sensor expectation
    if tag:
        ref = f"refs/tags/{tag}"
    else:
        ref = f"refs/heads/{revision}"

    payload = {
        "ref": ref,
        "after": revision, # Simulating commit SHA with revision for now
        "repository": {
            "clone_url": repo_url,
            "name": app_name
        }
    }

    try:
        secret = get_secret()
        if send_webhook(secret, gateway_url, payload):
            time.sleep(2) # Give a moment for workflow creation
            check_workflow()
    except subprocess.CalledProcessError as e:
        print(f"Failed to get secret from K8s: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
