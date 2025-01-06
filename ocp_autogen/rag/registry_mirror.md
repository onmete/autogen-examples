= Creating a mirror registry with mirror registry for Red Hat OpenShift

The _mirror registry for Red Hat OpenShift_ is a small and streamlined container registry that you can use as a target for mirroring the required container images of {product-title} for disconnected installations.

If you already have a container image registry, such as Red Hat Quay, you can skip this section and go straight to xref:../../disconnected/mirroring/installing-mirroring-installation-images.adoc#installation-mirror-repository_installing-mirroring-installation-images[Mirroring the OpenShift Container Platform image repository].

== Prerequisites

* An {product-title} subscription.
* {op-system-base-full} 8 and 9 with Podman 3.4.2 or later and OpenSSL installed.
* Fully qualified domain name for the Red Hat Quay service, which must resolve through a DNS server.
* Key-based SSH connectivity on the target host. SSH keys are automatically generated for local installs. For remote hosts, you must generate your own SSH keys.
* 2 or more vCPUs.
* 8 GB of RAM.
* About 12 GB for {product-title} {product-version} release images, or about 358 GB for {product-title} {product-version} release images and {product-title} {product-version} Red Hat Operator images. Up to 1 TB per stream or more is suggested.
+
[IMPORTANT]
====
These requirements are based on local testing results with only release images and Operator images. Storage requirements can vary based on your organization's needs. You might require more space, for example, when you mirror multiple z-streams. You can use standard link:https://access.redhat.com/documentation/en-us/red_hat_quay/3/html/use_red_hat_quay/index[Red Hat Quay functionality] or the proper link:https://access.redhat.com/documentation/en-us/red_hat_quay/3/html-single/red_hat_quay_api_guide/index#deletefulltag[API callout] to remove unnecessary images and free up space.
====