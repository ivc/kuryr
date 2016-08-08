==============================
Midonet Kuryr Operations Guide
==============================

Abstract
--------

This documentation provides information about operating with
Kubernetes using Neutron as a backend.

`Kuryr-Kubernetes`_ is a project that brings Neutron networking into a Kubernetes cluster.

It is based on two components:

- An asynchronous service (called Raven) that connects to K8s API endpoints listening
  `chunked-encoded`_ events as soon as they happen. These events will eventually be
  translated to Neutron API calls to perform backend tasks, such as requesting an IP
  for a new created Pod or configure a LBaaS for Service implementation.

- A `CNI`_ driver (Kubernetes must be `configured accordingly`_) that does the
  actual binding between Neutron ports and Docker containers.

In this guide we'll see how Kubernetes entities are mapped into Neutron and
learn the design decisions made to make this project work.

The `Current Limitations`_ section will enumerate the list of features that we
have in mind (and in roadmap) but have not been included in this release.

The `Getting Started`_ guide will discuss the Raven start-up and the Neutron
infrastructure that prepares for binding the K8s Pods to the networks.

The rest of the documents explains all the features that `Kuryr-Kubernetes`_
supports and how they are mapped into Neutron.

What this document is not
-------------------------

* This **IS NOT** a deployment guide. A properly configured and running
  Kuryr-Kubernetes is assumed.
* This **IS NOT** a Kubernetes guide. `Kubernetes`_ has a great documentation
  about its entities, philosophy and project goal. How to use its `command line
  tool`_ it is a good resource too. Some knowledge about Kubernetes or some
  initiative to read another documentation is assumed too.

Contents
--------

.. toctree::
   :maxdepth: 2

   limitations
   getting_started
   features/pods
   features/namespaces
   features/services
   features/security_groups


Search in this guide
--------------------

 * :ref:`search`

.. _`Kuryr-Kubernetes`: http://github.com/midonet/kuryr
.. _`chunked-encoded`: https://en.wikipedia.org/wiki/Chunked_transfer_encoding
.. _`CNI`: https://github.com/containernetworking/cni
.. _`configured accordingly`: http://kubernetes.io/docs/admin/network-plugins/#cni
.. _`Getting Started`: ./features/getting_started.html
.. _`Current Limitations`: ./limitations.html
.. _`Kubernetes`: http://kubernetes.io
.. _`command line tool`: http://kubernetes.io/docs/user-guide/kubectl-overview/
