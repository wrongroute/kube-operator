import os
import hvac
import base64
import json
import logging
import argparse
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from termcolor import colored

### Parsing args

#TODO: Param versions
def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("--namespace", default='default', type=str, help=("Namespace to use."))
  parser.add_argument("--secretname", type=str, help=("Secret name to use"))

  args, _ = parser.parse_known_args()
  return args

args = parse_args()
namespace = args.namespace
name = args.secretname

### Get secrets from Vault

client = hvac.Client(url='http://127.0.0.1:8200')

client.token = os.environ['VAULT_TOKEN']

logging.info("Is authentificated in Vault: %s" % (client.is_authenticated()))

mount_point = 'secret/amd/web/dev'
secret_path = 'app-params'

read_secret_result = client.secrets.kv.v1.read_secret(
    path=secret_path,
    mount_point=mount_point,
)

app_param = read_secret_result['data']

#print(app_param)

### Kube-work

config.load_kube_config("C:\\kuber-operator\\config")

v1_api = client.CoreV1Api()

def secret_create(secret_data, name, namespace="default"):
    """Create a K8S Secret.

    Args:
        secret_data (dict): Data to store in t as key/value hash.
        name (str): Name of the Secret.
        namespace (str): Name of namespace.
    """
    # TODO: We should check that Secret exists before we create it
    app_param_copy = app_param.copy()
    for key, value in secret_data.items():
        if isinstance(value, str):
            value = value.encode("ascii")
        secret_data[key] = base64.b64encode(value).decode("utf-8")
    secret = client.V1Secret()
    secret.metadata = client.V1ObjectMeta(name=name)
    secret.type = "Opaque"
    secret.data = app_param_copy
    v1_api.create_namespaced_secret(namespace=namespace, body=secret)
    logging.info("Created Secret %s in namespace %s" % (name, namespace))
