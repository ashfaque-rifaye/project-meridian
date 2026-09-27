      *================================================================*
      * LEDGREC  - LEDGER POSTING RECORD (INBOUND, QUEUE LEDGER.IN)     *
      * OWNER    - CORE LEDGER                                          *
      * ICD      - LEDG-ICD-007 REV 6                                   *
      * NOTE     - RECORD CARRIES NO CURRENCY. LEDGER BOOKS IN USD.     *
      *================================================================*
       01  LEDGER-RECORD.
           05  LR-CUSTOMER-ID          PIC X(10).
           05  LR-AMOUNT               PIC X(13).
