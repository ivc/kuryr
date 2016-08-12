========
Services
========

An application developer can choose how many replicas of the same service wants
to run. Due the volatile nature of containers, a `Replica Set`_ keeps the number
of replicas constant, by scheduling new containers when it detects some of them
are dead. `Services`_ are an abstraction layer on top of `Deployment`_ (which is
the `Replica Set`_ controller) to access to these containers, regardless of how
many of them or where they are deployed.

Raven maps services into `LBaaS v1`_ Neutron entities.  In Neutron we can see
`Replica Set`_ as Load Balancer Pool, and `Services`_ as Load Balancer VIPs.
`Pod`_\s are the Load Balancer Members.

As described on `limitations`_ section, we only support the *ClusterIP*
service type.

Creating a service
------------------

Create a service involves several steps:

1. :command:`User creates a Deployment`: Kubernetes creates the entities and its
   corresponding `Replica Set`_. It also schedules all the replicated `Pod`_\s.
2. :command:`Raven watches Pods`: There is not actual watcher on Deployment
   API endpoint, but since Kubernetes will create some `Pod`_\s (according to
   the number of replicas), Raven will see the events of these `Pod`_\s and will
   create the corresponding Neutron entities (see `the Pods guide`_
   documentation).
3. :command:`User creates a Service associated to the Deployment`: When a
   Service is created, Kubernetes chooses a ClusterIP from where the service
   will be accessible.
4. :command:`Raven watches Services`: and creates the LB Pool and the LB VIP
   in Neutron, using the `LBaaS v1`_ API. The VIP will belong to the
   *raven-default-service* Neutron network, configured via
   *cluster_service_subnet* (see `Getting Started`_)
5. :command:`Raven writes LB data entities on Services`: Neutron LB Pool and
   LB VIP info will be added on Service metadata annotation.
6. :command:`Raven watches Endpoints`: Kubenetes writes a new entry on the
   Endpoints API for each member of the `Deployment`_ . Raven sees the events
   and creates the corresponding LB Members.


This is an example of a `Deployment` replicating three nginx servers:

.. code-block:: bash

    # STEP 1: Create a deployment

    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: demo
    spec:
      replicas: 3
       template:
         metadata:
           labels:
             app: demo
         spec:
           containers:
           - name: nginx
             image: nginx
             resources:
               requests:
                 cpu: 100m
                 memory: 100Mi
             ports:
             - containerPort: 80

Copying the contents of this block on a file and run the following command:

 | kubectl create -f deployment.yaml

Should create three `Pod`_\s in Kubernetes and three ports on Neutron (see
`the Pods guide`_ explanation if you wish to check out what happens behind
scenes)

Then, if we use this data to create a service:

.. code-block:: bash

    # STEP 3: Create a service

    apiVersion: v1
    kind: Service
    metadata:
      name: demo
    spec:
      ports:
        -
          port: 80
      selector:
        app: demo

Copying the contents on a file and run the creation:

 | kubectl create -f service.yaml

Will trigger the Raven service and endpoint watchers.

.. code-block:: bash

    # STEP 4 and 6: Raven creates LB entities on neutron

    user@kuryr > neutron lb-vip-list -c name -c address -c protocol -c status
    +------+------------+----------+--------+
    | name | address    | protocol | status |
    +------+------------+----------+--------+
    | demo | 10.0.0.228 | TCP      | ACTIVE |
    +------+------------+----------+--------+
    user@kuryr > neutron lb-pool-list -c name -c provider -c protocol -c status
    +------+----------+----------+--------+
    | name | provider | protocol | status |
    +------+----------+----------+--------+
    | demo | midonet  | TCP      | ACTIVE |
    +------+----------+----------+--------+
    user@kuryr > neutron lb-member-list -c address -c protocol_port -c status
    +-------------+---------------+--------+
    | address     | protocol_port | status |
    +-------------+---------------+--------+
    | 192.168.0.3 |            80 | ACTIVE |
    | 192.168.0.5 |            80 | ACTIVE |
    | 192.168.0.4 |            80 | ACTIVE |
    +-------------+---------------+--------+

Please note the VIP is taken from the *raven-default-service* network and the
members' IPs (Pods) belongs to the namespace network.

These entities data are written on Service metadata:

.. code-block:: bash

    # STEP 5: Raven writes metadata on K8s service entity

    user@kuryr > kubectl get service demo -o template --template={{.metadata.annotations}}

    map[kuryr.org/neutron-pool:
        {"members": [], "status_description": null, "status": "ACTIVE", "subnet_id": "67c6c4f0-49ca-4619-9c94-07092635fb2c", "id":
         "72cf1c69-a70b-4b76-b3f8-de5baae12934", "provider": "midonet", "description": "", "name": "demo", "lb_method": "ROUND_ROBIN",
         "protocol": "TCP", "health_monitors_status": [], "tenant_id": "48a5b6b9a0db414592aced182af6f89a", "vip_id": null,
         "health_monitors": [], "admin_state_up": true}
        kuryr.org/neutron-vip:
        {"port_id": "d70fac2f-0564-4533-878e-e2e045e5614c", "connection_limit": -1, "status_description": null,
         "status": "PENDING_CREATE", "subnet_id": "ff13afd0-640b-40ba-bfb7-620812064c21", "protocol_port": 80, "id":
         "953228bb-e8c8-42ad-be28-3f55220e8468", "description": "", "name": "demo", "pool_id": "72cf1c69-a70b-4b76-b3f8-de5baae12934",
         "protocol": "TCP", "address": "10.0.0.228", "tenant_id": "48a5b6b9a0db414592aced182af6f89a",
         "session_persistence": null, "admin_state_up": true}]~


External Services
-----------------

Kubernetes services can have one or more external IP which allow traffic from
outside the cluster.

Raven maps external IP's to Neutron `Floating Ip`_\s. As described on
`limitations`_ section, only one external IP per service is presently supported.

When Raven detects the "externalIPs" field in a Service, it will create the
Floating IP on Neutron that matches with the *first* "externalIPs" on the list.

That "externalIP" **MUST** belong to the IP range defined on
*cluster_external_subnet* Raven configuration variable.  To create an external
IP, it must be on that range. In case the IP does not belong to that range, the
external IP **will be ignored**.

Let's add an external IP on the Service created on the previous section by using
the *kubectl patch* utility.

.. code-block:: bash

   user@kuryr > kubectl patch service demo -p '{"spec": {"externalIPs": ["172.16.0.4"]}}'


Since the FloatingIP is in the range of the *cluster_external_subnet*, we can
check that has been created on Neutron:


.. code-block:: bash

   user@kuryr > neutron floatingip-list
   +--------------------------------------+------------------+---------------------+
   | id                                   | fixed_ip_address | floating_ip_address |
   +--------------------------------------+------------------+---------------------+
   | 18696206-b472-4fa7-805b-52a2e50da977 | 10.0.0.228       | 172.16.0.4          |
   +--------------------------------------+------------------+---------------------+

Please note the *fixed_ip_address* belongs to the LoadBalancer VIP created in
the previous section.


Delete Service
--------------

Deleting a Service deletes all the Load Balancer entities:

.. code-block:: bash

    ~ > kubectl delete service demo
    service "demo" deleted
    ~ > neutron lb-vip-list

    ~ > neutron lb-pool-list

    ~ > neutron lb-member-list


But does not delete the `Pod`_\s neither the ports:

.. code-block:: bash

    user@kuryr > neutron port-list -c name -c fixed_ips
    +----------------------+------------------------------------------------------------------------------------+
    | name                 | fixed_ips                                                                          |
    +----------------------+------------------------------------------------------------------------------------+
    | demo-914545731-ralez | {"subnet_id": "67c6c4f0-49ca-4619-9c94-07092635fb2c", "ip_address": "192.168.0.5"} |
    | demo-914545731-6l59z | {"subnet_id": "67c6c4f0-49ca-4619-9c94-07092635fb2c", "ip_address": "192.168.0.3"} |
    | demo-914545731-0xewm | {"subnet_id": "67c6c4f0-49ca-4619-9c94-07092635fb2c", "ip_address": "192.168.0.4"} |
    +----------------------+------------------------------------------------------------------------------------+

    user@kuryr > kubectl get pod
    NAME                   READY     STATUS    RESTARTS   AGE
    demo-914545731-0xewm   1/1       Running   0          1h
    demo-914545731-6l59z   1/1       Running   0          1h
    demo-914545731-ralez   1/1       Running   0          1h

To do so, you have to delete the deployment:

.. code-block:: bash

    user@kuryr > kubectl delete delpoyment demo
    deployment "demo" deleted
    user@kuryr > kubectl get pod
    NAME                   READY     STATUS    RESTARTS   AGE



.. _`Kubernetes services`: http://kubernetes.io/docs/user-guide/services/
.. _`Replica Set`: http://kubernetes.io/docs/user-guide/replicasets/
.. _`Pod`: http://kubernetes.io/docs/user-guide/pods/
.. _`Deployment`: http://kubernetes.io/docs/user-guide/deployments/
.. _`LBaaS v1`: http://developer.openstack.org/api-ref/networking/v2-ext/index.html#lbaas-1-0-deprecated
.. _`the Pods guide`: ./pods.html
.. _`limitations`: ../limitations.html
.. _`Getting Started`: ../getting_started.html
.. _`external IP`: http://kubernetes.io/docs/user-guide/services/#external-ips
.. _`Floating IP`: http://docs.openstack.org/user-guide/cli-manage-ip-addresses.html
