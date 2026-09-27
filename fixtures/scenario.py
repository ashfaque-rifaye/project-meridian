"""
Meridian demo scenario: release R-26.9, flow Order-to-Ledger.

This module is the single source of truth for the synthetic enterprise used in
the demo. `fixtures/build_scenario.py` turns it into:

  * per-component git repositories with realistic history   (.meridian/repos/)
  * raw adapter outputs per environment                     (environments/<env>/adapters/)
  * deployment events and validation runs                   (environments/*.json)
  * enterprise documents (PDF / DOCX / XLSX)                (documents/)

ALL DATA IS SYNTHETIC AND FICTIONAL. Company, people, hosts, digests, and
timestamps are invented for the demonstration.
"""

ORG = "Acme Retail Group (fictional)"

# "Now" inside the scenario: the moment the investigation is run.
SNAPSHOT_TIME = "2026-09-25T16:20:00Z"

ENVIRONMENTS = ["dev", "test", "stage", "prod"]
PROMOTION_PATH = ["dev", "test", "stage", "prod"]

FLOW_ID = "order-to-ledger"
FLOW_NAME = "Order-to-Ledger"
FLOW_DESCRIPTION = (
    "A customer checkout becomes an order, a payment, a settled-order event, a billing "
    "event, a fixed-width ledger record, and finally a posted row in the Db2 ledger."
)

# --------------------------------------------------------------------------- components

COMPONENTS = [
    {
        "id": "web-checkout", "label": "web-checkout", "kind": "service",
        "platform": "GKE", "cloud": "Google Cloud", "location": "us-east4",
        "runtime": "Kubernetes Deployment", "team": "Digital Storefront",
        "deploy_tool": "Google Cloud Deploy", "adapter": "kubernetes",
        "cluster": "gke-{env}-use4", "namespace": "checkout",
        "registry": "us-east4-docker.pkg.dev/acme-storefront/apps",
    },
    {
        "id": "order-api", "label": "order-api", "kind": "service",
        "platform": "EKS", "cloud": "AWS", "location": "us-east-1",
        "runtime": "Kubernetes Deployment", "team": "Order Platform",
        "deploy_tool": "GitHub Actions + Argo CD", "adapter": "kubernetes",
        "cluster": "eks-{env}-use1", "namespace": "orders",
        "registry": "441122334455.dkr.ecr.us-east-1.amazonaws.com/orders",
    },
    {
        "id": "payment-service", "label": "payment-service", "kind": "service",
        "platform": "AKS", "cloud": "Azure", "location": "eastus2",
        "runtime": "Kubernetes Deployment", "team": "Payments",
        "deploy_tool": "Azure DevOps", "adapter": "kubernetes",
        "cluster": "aks-{env}-eus2", "namespace": "payments",
        "registry": "acmepayments.azurecr.io/payments",
    },
    {
        "id": "kafka-orders", "label": "kafka · orders.v1", "kind": "stream",
        "platform": "Kafka", "cloud": "Confluent Cloud", "location": "aws us-east-1",
        "runtime": "Topic orders.v1 · subject orders-value", "team": "Streaming Platform",
        "deploy_tool": "GitHub Actions (schema pipeline)", "adapter": "schema-registry",
        "cluster": "lkc-{env}-orders", "namespace": "orders.v1",
    },
    {
        "id": "billing-service", "label": "billing-service", "kind": "service",
        "platform": "GKE", "cloud": "Google Cloud", "location": "us-east4",
        "runtime": "Kubernetes Deployment", "team": "Billing",
        "deploy_tool": "Google Cloud Deploy", "adapter": "kubernetes",
        "cluster": "gke-{env}-use4", "namespace": "billing",
        "registry": "us-east4-docker.pkg.dev/acme-storefront/apps",
    },
    {
        "id": "mq-bridge", "label": "mq-bridge", "kind": "integration",
        "platform": "OpenShift", "cloud": "On-prem · DC2", "location": "Dallas DC2",
        "runtime": "OpenShift Deployment", "team": "Integration Services",
        "deploy_tool": "Argo CD (OpenShift GitOps)", "adapter": "kubernetes",
        "cluster": "ocp-{env}-dc2", "namespace": "integration",
        "registry": "quay.dc2.acme.internal/integration",
    },
    {
        "id": "legacy-ledger", "label": "legacy-ledger", "kind": "legacy",
        "platform": "WebSphere Liberty", "cloud": "On-prem · VMware", "location": "Dallas DC2",
        "runtime": "Liberty app LDGPOST on VM", "team": "Core Ledger",
        "deploy_tool": "Jenkins + CAB change window", "adapter": "websphere-liberty",
        "cluster": "was-{env}-ldg-03", "namespace": "ldgpost",
    },
    {
        "id": "ledger-db", "label": "ledger-db", "kind": "database",
        "platform": "Db2 LUW", "cloud": "On-prem", "location": "Dallas DC2",
        "runtime": "Database LEDGDB · schema LEDGER", "team": "Core Ledger DBA",
        "deploy_tool": "Flyway via Jenkins + CAB", "adapter": "flyway",
        "cluster": "db2-{env}-ldg01", "namespace": "LEDGER",
    },
]

# ------------------------------------------------------------------------------- edges

EDGES = [
    {
        "id": "web-checkout--order-api", "order": 1,
        "producer": "web-checkout", "consumer": "order-api",
        "interface": "REST · POST /v2/orders", "protocol": "HTTPS / JSON",
        "contract": {"kind": "OpenAPI", "ref": "orders-api v2", "formal": True},
    },
    {
        "id": "order-api--payment-service", "order": 2,
        "producer": "order-api", "consumer": "payment-service",
        "interface": "gRPC · PaymentAuthorize", "protocol": "gRPC / Protobuf",
        "contract": {"kind": "Protobuf", "ref": "payments.v1.PaymentAuthorize", "formal": True},
    },
    {
        "id": "payment-service--kafka-orders", "order": 3,
        "producer": "payment-service", "consumer": "kafka-orders",
        "interface": "Kafka produce · orders.v1", "protocol": "Kafka / Avro",
        "contract": {"kind": "Avro · Schema Registry", "ref": "orders-value (BACKWARD)", "formal": True},
    },
    {
        "id": "kafka-orders--billing-service", "order": 4,
        "producer": "kafka-orders", "consumer": "billing-service",
        "interface": "Kafka consume · orders.v1 (group billing-svc)", "protocol": "Kafka / Avro",
        "contract": {"kind": "Avro · Schema Registry", "ref": "orders-value (BACKWARD)", "formal": True},
    },
    {
        "id": "billing-service--mq-bridge", "order": 5,
        "producer": "billing-service", "consumer": "mq-bridge",
        "interface": "IBM MQ · BILL.OUT", "protocol": "IBM MQ / JSON",
        "contract": {"kind": "Sample payloads only", "ref": "wiki: BILL.OUT examples", "formal": False},
    },
    {
        "id": "mq-bridge--legacy-ledger", "order": 6,
        "producer": "mq-bridge", "consumer": "legacy-ledger",
        "interface": "IBM MQ · LEDGER.IN", "protocol": "IBM MQ / fixed-width LEDGREC",
        "contract": {
            "kind": "None — implicit in copybook + ICD spreadsheet",
            "ref": "LEDGREC.cpy · LEDG-ICD-007", "formal": False,
        },
        "probe_type": "fixed-width-record",
        "producer_entrypoint": "src/ledger_record.py:to_ledger_record",
        "consumer_entrypoint": "src/ldgpost.py:post",
    },
    {
        "id": "legacy-ledger--ledger-db", "order": 7,
        "producer": "legacy-ledger", "consumer": "ledger-db",
        "interface": "JDBC · LEDGER.TRANSACTIONS", "protocol": "Db2 / SQL",
        "contract": {"kind": "Flyway migrations (DDL)", "ref": "V14 / V15", "formal": True},
    },
]

# ---------------------------------------------------------------------------- release

RELEASE = {
    "id": "R-26.9",
    "title": "Customer ID expansion and currency code support",
    "requirement": (
        "Increase customerId capacity from 10 to 12 characters and introduce mandatory "
        "currencyCode support for ledger transactions."
    ),
    "tickets": ["LEDG-2231", "LEDG-2232", "LEDG-2233", "LEDG-2240", "LEDG-2241", "LEDG-2242"],
    "baseline_release": "R-26.8",
    "target": {
        "web-checkout": "2.3",
        "order-api": "4.8",
        "payment-service": "8.4",
        "kafka-orders": "v4",
        "billing-service": "7.2",
        "mq-bridge": "3.1",
        "legacy-ledger": "7.0",
        "ledger-db": "V15",
    },
    "baseline": {
        "web-checkout": "2.3",
        "order-api": "4.7",
        "payment-service": "8.3",
        "kafka-orders": "v3",
        "billing-service": "7.1",
        "mq-bridge": "3.0",
        "legacy-ledger": "6.9",
        "ledger-db": "V14",
    },
    "rollout_order": [
        "ledger-db V15", "legacy-ledger 7.0", "kafka-orders v4", "payment-service 8.4",
        "order-api 4.8", "billing-service 7.2", "mq-bridge 3.1",
    ],
    "dependencies": [
        "mq-bridge 3.1 emits LEDGREC rev 7 (25 bytes) and requires legacy-ledger >= 7.0 on LEDGER.IN.",
        "legacy-ledger 7.0 accepts LEDGREC rev 6 and rev 7, so it must be deployed before mq-bridge 3.1.",
        "legacy-ledger 7.0 requires ledger-db V15 (CUSTOMER_ID VARCHAR(12), CURRENCY_CODE).",
        "payment-service 8.4 publishes orders-value v4; billing-service 7.2 must consume v4.",
    ],
    "change_request": "CR-4471",
}

# ------------------------------------------------------------------------ git history

PEOPLE = {
    "storefront": ("Maya Okafor", "maya.okafor@acme.example"),
    "orders": ("Daniel Weiss", "daniel.weiss@acme.example"),
    "payments": ("Lucia Ferreira", "lucia.ferreira@acme.example"),
    "streaming": ("Kenji Watanabe", "kenji.watanabe@acme.example"),
    "billing": ("Aisha Rahman", "aisha.rahman@acme.example"),
    "integration": ("Tomasz Nowak", "tomasz.nowak@acme.example"),
    "ledger": ("Ruth Adeyemi", "ruth.adeyemi@acme.example"),
    "dba": ("Victor Chen", "victor.chen@acme.example"),
}

# component -> ordered list of versions; each version is a list of commits.
# A commit with "files": None applies the whole version tree.
GIT_HISTORY = {
    "web-checkout": {"owner": "storefront", "versions": [
        ("2.3", [
            ("2026-08-04T10:12:00+00:00", "Submit carts to order-api /v2/orders", None),
        ]),
    ]},
    "order-api": {"owner": "orders", "versions": [
        ("4.7", [
            ("2026-08-06T09:20:00+00:00", "Order intake validation for /v2/orders", None),
        ]),
        ("4.8", [
            ("2026-09-15T14:02:00+00:00", "LEDG-2231: accept 12-character customer IDs", None),
            ("2026-09-16T11:40:00+00:00", "LEDG-2233: require currencyCode on orders", None),
        ]),
    ]},
    "payment-service": {"owner": "payments", "versions": [
        ("8.3", [
            ("2026-08-07T16:05:00+00:00", "Publish settled orders to orders.v1 (orders-value v3)", None),
        ]),
        ("8.4", [
            ("2026-09-16T10:18:00+00:00", "LEDG-2231, LEDG-2233: orders-value v4 with currencyCode", None),
        ]),
    ]},
    "kafka-orders": {"owner": "streaming", "versions": [
        ("v3", [
            ("2026-08-03T08:30:00+00:00", "orders-value v3", None),
        ]),
        ("v4", [
            ("2026-09-15T09:45:00+00:00", "LEDG-2233: orders-value v4 adds currencyCode (default USD)", None),
        ]),
    ]},
    "billing-service": {"owner": "billing", "versions": [
        ("7.1", [
            ("2026-08-10T13:00:00+00:00", "Publish billing events to BILL.OUT", None),
        ]),
        ("7.2", [
            ("2026-09-16T15:30:00+00:00", "LEDG-2233: propagate currencyCode to BILL.OUT", None),
        ]),
    ]},
    "mq-bridge": {"owner": "integration", "versions": [
        ("3.0", [
            ("2026-08-11T10:05:00+00:00", "LEDG-2101: LEDGREC v6 record builder", ["src/ledger_record.py"]),
            ("2026-08-12T15:22:00+00:00", "BILL.OUT listener and MQ configuration", None),
        ]),
        ("3.1", [
            ("2026-09-15T13:10:00+00:00", "LEDG-2231: widen customerId to 12 characters in LEDGREC", ["src/ledger_record.py"]),
            ("2026-09-16T09:48:00+00:00", "LEDG-2232: add mandatory currencyCode (LEDGREC rev 7)", None),
        ]),
    ]},
    "legacy-ledger": {"owner": "ledger", "versions": [
        ("6.9", [
            ("2026-08-20T11:30:00+00:00", "LDGPOST: copybook-driven LEDGREC parser", ["copybooks/LEDGREC.cpy", "src/ldgpost.py"]),
            ("2026-08-21T09:15:00+00:00", "Liberty server configuration for LEDGER.IN", None),
        ]),
        ("7.0", [
            ("2026-09-16T14:20:00+00:00", "LEDG-2240: LEDGREC rev 7 copybook (CUSTOMER-ID X(12), CURRENCY-CODE X(3))",
             ["copybooks/LEDGREC.cpy", "copybooks/LEDGREC6.cpy"]),
            ("2026-09-17T10:05:00+00:00", "LEDG-2241: route records by length; accept rev 6 and rev 7", ["src/ldgpost.py"]),
            ("2026-09-18T08:40:00+00:00", "Release 7.0", None),
        ]),
    ]},
    "ledger-db": {"owner": "dba", "versions": [
        ("V14", [
            ("2026-08-18T12:00:00+00:00", "V14: LEDGER.TRANSACTIONS", None),
        ]),
        ("V15", [
            ("2026-09-17T15:10:00+00:00", "LEDG-2242: V15 widen CUSTOMER_ID, add CURRENCY_CODE", None),
        ]),
    ]},
}

# ------------------------------------------------------------------ environment history

# State of each environment before R-26.9 started moving (R-26.8 everywhere).
BASELINE_DEPLOYED_AT = {
    "dev": "2026-09-14T09:00:00Z",
    "test": "2026-09-15T09:00:00Z",
    "stage": "2026-09-16T09:00:00Z",
}
PROD_BASELINE_DEPLOYED_AT = {
    "web-checkout": "2026-09-10T08:04:00Z",
    "order-api": "2026-09-14T06:31:00Z",
    "payment-service": "2026-09-14T06:12:00Z",
    "kafka-orders": "2026-09-14T06:00:00Z",
    "billing-service": "2026-09-14T07:33:00Z",
    "mq-bridge": "2026-09-14T11:02:00Z",
    "legacy-ledger": "2026-09-21T18:03:00Z",
    "ledger-db": "2026-09-21T18:10:00Z",
}

# (env, component, from_version, to_version, timestamp, note)
DEPLOYMENTS = [
    # R-26.8 CAB change on Monday evening: legacy-ledger 6.8 -> 6.9 in prod.
    ("prod", "legacy-ledger", "6.8", "6.9", "2026-09-21T18:03:00Z", "CR-4402 · R-26.8 CAB window"),
    ("prod", "ledger-db", "V13", "V14", "2026-09-21T18:10:00Z", "CR-4402 · R-26.8 CAB window"),

    # DEV · Tuesday
    ("dev", "kafka-orders", "v3", "v4", "2026-09-22T09:10:00Z", None),
    ("dev", "payment-service", "8.3", "8.4", "2026-09-22T09:20:00Z", None),
    ("dev", "order-api", "4.7", "4.8", "2026-09-22T09:25:00Z", None),
    ("dev", "billing-service", "7.1", "7.2", "2026-09-22T09:40:00Z", None),
    ("dev", "mq-bridge", "3.0", "3.1", "2026-09-22T10:15:00Z", None),
    ("dev", "ledger-db", "V14", "V15", "2026-09-22T15:35:00Z", None),
    ("dev", "legacy-ledger", "6.9", "7.0", "2026-09-22T15:40:00Z", None),

    # TEST · Wednesday (bridge lands before the ledger; the pair sits idle for 4.5h)
    ("test", "kafka-orders", "v3", "v4", "2026-09-23T08:30:00Z", None),
    ("test", "payment-service", "8.3", "8.4", "2026-09-23T08:40:00Z", None),
    ("test", "order-api", "4.7", "4.8", "2026-09-23T08:45:00Z", None),
    ("test", "billing-service", "7.1", "7.2", "2026-09-23T08:55:00Z", None),
    ("test", "mq-bridge", "3.0", "3.1", "2026-09-23T09:00:00Z", None),
    ("test", "ledger-db", "V14", "V15", "2026-09-23T13:20:00Z", None),
    ("test", "legacy-ledger", "6.9", "7.0", "2026-09-23T13:30:00Z", None),

    # STAGE · Thursday, follows the release runbook (ledger first)
    ("stage", "ledger-db", "V14", "V15", "2026-09-24T09:00:00Z", "Runbook step 1"),
    ("stage", "legacy-ledger", "6.9", "7.0", "2026-09-24T09:30:00Z", "Runbook step 2"),
    ("stage", "mq-bridge", "3.0", "3.1", "2026-09-24T10:00:00Z", "Runbook step 7 (run early, ledger already on 7.0)"),
    ("stage", "kafka-orders", "v3", "v4", "2026-09-24T10:20:00Z", "Runbook step 3"),
    ("stage", "payment-service", "8.3", "8.4", "2026-09-24T10:30:00Z", "Runbook step 4"),
    ("stage", "order-api", "4.7", "4.8", "2026-09-24T10:35:00Z", "Runbook step 5"),
    ("stage", "billing-service", "7.1", "7.2", "2026-09-24T10:45:00Z", "Runbook step 6"),

    # PROD · Friday. Cloud teams promote continuously in the morning.
    ("prod", "kafka-orders", "v3", "v4", "2026-09-25T06:00:00Z", None),
    ("prod", "payment-service", "8.3", "8.4", "2026-09-25T06:10:00Z", None),
    ("prod", "order-api", "4.7", "4.8", "2026-09-25T06:30:00Z", None),
    ("prod", "billing-service", "7.1", "7.2", "2026-09-25T07:30:00Z", None),
    # The integration team's Argo CD app auto-syncs after release/R-26.9 is merged
    # into env/prod. legacy-ledger 7.0 is still waiting for Sunday's CAB window.
    ("prod", "mq-bridge", "3.0", "3.1", "2026-09-25T11:42:00Z",
     "Argo CD auto-sync after PR #1882 merged release/R-26.9 into env/prod"),
]

# How each component is deployed (used to render realistic pipeline metadata).
DEPLOY_TOOLING = {
    "web-checkout": ("Google Cloud Deploy", "clouddeploy-sa@acme-storefront.iam", "rollout"),
    "order-api": ("Argo CD (EKS)", "argocd-application-controller", "sync"),
    "payment-service": ("Azure DevOps", "svc-payments-release", "pipeline"),
    "kafka-orders": ("GitHub Actions", "schema-registry-promote", "workflow"),
    "billing-service": ("Google Cloud Deploy", "clouddeploy-sa@acme-storefront.iam", "rollout"),
    "mq-bridge": ("Argo CD (OpenShift GitOps)", "openshift-gitops-application-controller", "auto-sync"),
    "legacy-ledger": ("Jenkins + CAB", "jenkins-ledger-deploy", "change"),
    "ledger-db": ("Flyway via Jenkins", "flyway_svc", "change"),
}

# Upcoming, not yet executed.
SCHEDULED_CHANGES = [
    {
        "change_request": "CR-4471",
        "environment": "prod",
        "window_start": "2026-09-27T02:00:00Z",
        "window_end": "2026-09-27T04:00:00Z",
        "changes": [("ledger-db", "V14", "V15"), ("legacy-ledger", "6.9", "7.0")],
        "status": "Scheduled · CAB approved 2026-09-24",
        "dependency_note": "Must be completed before mq-bridge 3.1 is promoted to Production.",
    }
]

# ---------------------------------------------------------------------- validation runs

# The probe corpus. Stage validated R-26.9 with exactly these records.
LEDGER_FIXTURES = [
    {
        "id": "fx-new-customer-usd",
        "label": "New 12-character customer, USD",
        "event": {"billingId": "BL-100482", "customerId": "CUST12345678", "currencyCode": "USD", "amount": "149.50"},
    },
    {
        "id": "fx-existing-customer-eur",
        "label": "Existing 10-character customer, EUR",
        "event": {"billingId": "BL-100483", "customerId": "CUST000042", "currencyCode": "EUR", "amount": "20.00"},
    },
    {
        "id": "fx-existing-customer-usd",
        "label": "Existing 10-character customer, USD",
        "event": {"billingId": "BL-100484", "customerId": "CUST000017", "currencyCode": "USD", "amount": "1250.00"},
    },
]

R268 = {
    "web-checkout--order-api": ("2.3", "4.7"),
    "order-api--payment-service": ("4.7", "8.3"),
    "payment-service--kafka-orders": ("8.3", "v3"),
    "kafka-orders--billing-service": ("v3", "7.1"),
    "billing-service--mq-bridge": ("7.1", "3.0"),
    "mq-bridge--legacy-ledger": ("3.0", "6.9"),
    "legacy-ledger--ledger-db": ("6.9", "V14"),
}
R269 = {
    "web-checkout--order-api": ("2.3", "4.8"),
    "order-api--payment-service": ("4.8", "8.4"),
    "payment-service--kafka-orders": ("8.4", "v4"),
    "kafka-orders--billing-service": ("v4", "7.2"),
    "billing-service--mq-bridge": ("7.2", "3.1"),
    "mq-bridge--legacy-ledger": ("3.1", "7.0"),
    "legacy-ledger--ledger-db": ("7.0", "V15"),
}

SEMANTIC_ASSERTIONS = {
    "web-checkout--order-api": 6,
    "order-api--payment-service": 5,
    "payment-service--kafka-orders": 4,
    "kafka-orders--billing-service": 4,
    "billing-service--mq-bridge": 5,
    "mq-bridge--legacy-ledger": 9,
    "legacy-ledger--ledger-db": 6,
}

VALIDATION_RUNS = [
    {
        "run_id": "val-stage-r268-e2e-0917",
        "environment": "stage", "release": "R-26.8",
        "suite": "stage-e2e-order-to-ledger", "method": "End-to-end business flow with semantic assertions",
        "pipeline": "Jenkins · release-validation #2211",
        "started_at": "2026-09-17T14:00:00Z", "finished_at": "2026-09-17T14:22:00Z",
        "pairs": R268, "messages": 240, "semantic": True, "result": "PASS",
        "fixtures": ["fx-existing-customer-usd"],
    },
    {
        "run_id": "val-dev-r269-smoke-0922",
        "environment": "dev", "release": "R-26.9",
        "suite": "ledger-connectivity-smoke", "method": "Post-deploy smoke test (MQ ACK + posting status only)",
        "pipeline": "Argo CD PostSync hook · mq-bridge",
        "started_at": "2026-09-22T11:05:00Z", "finished_at": "2026-09-22T11:05:40Z",
        "pairs": {
            "billing-service--mq-bridge": ("7.2", "3.1"),
            "mq-bridge--legacy-ledger": ("3.1", "6.9"),
        },
        "messages": 1, "semantic": False, "result": "PASS",
        "checks": ["MQ ACK received from LEDGER.IN", "LDGPOST status = POSTED"],
        "fixtures": ["fx-existing-customer-usd"],
    },
    {
        "run_id": "val-dev-r269-e2e-0922",
        "environment": "dev", "release": "R-26.9",
        "suite": "dev-e2e-order-to-ledger", "method": "End-to-end business flow with semantic assertions",
        "pipeline": "Jenkins · release-validation #2230",
        "started_at": "2026-09-22T16:30:00Z", "finished_at": "2026-09-22T16:51:00Z",
        "pairs": R269, "messages": 180, "semantic": True, "result": "PASS",
        "fixtures": [f["id"] for f in LEDGER_FIXTURES],
    },
    {
        "run_id": "val-test-r269-sit-0923",
        "environment": "test", "release": "R-26.9",
        "suite": "sit-order-to-ledger", "method": "System integration test with semantic assertions",
        "pipeline": "Jenkins · release-validation #2241",
        "started_at": "2026-09-23T15:00:00Z", "finished_at": "2026-09-23T15:38:00Z",
        "pairs": R269, "messages": 620, "semantic": True, "result": "PASS",
        "fixtures": [f["id"] for f in LEDGER_FIXTURES],
    },
    {
        "run_id": "val-stage-r269-e2e-0924",
        "environment": "stage", "release": "R-26.9",
        "suite": "stage-e2e-order-to-ledger", "method": "End-to-end business flow with semantic assertions",
        "pipeline": "Jenkins · release-validation #2256",
        "started_at": "2026-09-24T14:30:00Z", "finished_at": "2026-09-24T14:57:00Z",
        "pairs": R269, "messages": 1420, "semantic": True, "result": "PASS",
        "fixtures": [f["id"] for f in LEDGER_FIXTURES],
    },
]

# ------------------------------------------------------------ non-flow workloads (noise)

# Workloads that share clusters with the flow. They exist so that a naive
# environment diff looks like it does in real life: mostly irrelevant noise.
NEIGHBOURS = {
    "gke": [("search-api", {"stage": "5.12", "prod": "5.11"}), ("recommendations", {"stage": "3.4", "prod": "3.2"})],
    "eks": [("cart-api", {"stage": "2.19", "prod": "2.18"}), ("inventory-api", {"stage": "6.1", "prod": "6.1"})],
    "aks": [("fraud-scoring", {"stage": "1.14", "prod": "1.13"})],
    "ocp": [("edi-gateway", {"stage": "4.2", "prod": "4.2"}), ("file-transfer", {"stage": "1.8", "prod": "1.7"})],
}
