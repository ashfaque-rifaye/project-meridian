      *================================================================*
      * LEDGREC  - LEDGER POSTING RECORD (INBOUND, QUEUE LEDGER.IN)     *
      * OWNER    - CORE LEDGER                                          *
      * ICD      - LEDG-ICD-007 REV 7   (R-26.9, LEDG-2240)             *
      * CHANGE   - CUSTOMER-ID WIDENED 10 -> 12, CURRENCY-CODE ADDED    *
      *================================================================*
       01  LEDGER-RECORD.
           05  LR-CUSTOMER-ID          PIC X(12).
           05  LR-CURRENCY-CODE        PIC X(3).
           05  LR-AMOUNT               PIC X(10).
