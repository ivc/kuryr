===================
Current Limitations
===================

Kuryr-kubernetes is in an early stage. An user familiarized with Kubernetes may
find some lack of features for a fully functional K8s with its applications.  We
enumerate here most important, all of them included in our roadmap:

- Only container orchestration using Kubernetes API is supported (`kubectl`_ or any
  custom client based on its `specification`_). Any combination with `Magnum`_
  has not been tested yet.

- No multitenancy support: all the operations are done using *admin* user from
  Neutron service. Kubernetes native `Keystone Authentication`_ not tested.

- No mapping between `K8s resource quota`_ and `neutron service quota`_.

- No isolation between namespaces. All the namespaces are mapped into networks
  attached to the same router using the *admin* user. That means namespaces
  are not network isolated.

- NetworkPolicy is `already merged`_ as experimental in K8S v1.3, we don't
  support it yet.

- A full "public network/router/tenant networks" entities are being created in
  start up time, no possibility to reuse an existing Neutron entity yet.

- Only *ClusterIP* `service types`_ is supported.


.. _`Keystone Authentication`: http://kubernetes.io/docs/admin/authentication/
.. _`Kubernetes`: http://kubernetes.io
.. _`kubectl`: http://kubernetes.io/docs/user-guide/kubectl-overview/
.. _`specification`: http://kubernetes.io/docs/api/
.. _`Magnum`: https://wiki.openstack.org/wiki/Magnum
.. _`K8s resource quota`: http://kubernetes.io/docs/admin/resourcequota/
.. _`neutron service quota`: http://docs.openstack.org/admin-guide/cli_networking_advanced_quotas.html
.. _`already merged`: https://github.com/kubernetes/kubernetes/pull/25638
.. _`service types`: http://kubernetes.io/docs/user-guide/services/#publishing-services---service-types
