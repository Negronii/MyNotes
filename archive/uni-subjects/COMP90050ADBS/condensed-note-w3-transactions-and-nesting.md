# What do transaction boundaries, savepoints, and nested transactions mean? / 事务边界、保存点与嵌套事务意味着什么？

A transaction groups protected database actions so the system can commit or roll them back together. Savepoints and the course’s closed-nesting model retain useful structure inside a larger unit; an ancestor abort still removes provisional child work. / 事务把受保护的数据库操作组合起来，使系统能一起提交或回滚。保存点与课程的封闭嵌套模型为较大工作单元保留内部结构；祖先事务中止仍会撤销子事务的临时结果。

## Transactions / 事务
### Transaction - A unit of work in a database
- A transaction can have any number and type of operations in it
- Either happens as a whole or not
- Transactions ideally have four properties, commonly known as ACID properties

### ACID (Atomicity, Consistency, Isolation, Durability) properties:
- Atomicity - All changes to data are performed as if they are a single operation. That is, all the changes are performed, or none of them are.
  Example – A transaction that (i) subtracts $100 if balance >100 (ii) deposits $100 to another account
  (both actions with either happen together or none will happen)
- Consistency - Data is in a ‘consistent’ state when a transaction starts and when it ends – in other words, any data written to the database must be valid according to all defined rules (e.g., no duplicate student ID, no negative fund transfer, etc.)
  - What is ‘consistent’ - depends on the application and context constraints
  - It is not easily computable in general
  - Serializable execution orders participating transactions as if they ran one at a time. It does not enforce an application invariant unless the relevant constraints are declared or every transaction checks them correctly.
- Isolation controls how concurrent transactions observe one another. Together with atomic commit, it prevents another transaction from observing only one side of a completed transfer; isolation alone does not make the debit and credit atomic.
- Durability- the system should tolerate system failures and any committed updates should not be lost.

### Types of Actions
- Unprotected actions - no ACID property
- Protected actions - these actions are not externalised before they are completely done. These actions are controlled and can be rolled back if required. These have ACID property.
- Real actions - these are real physical actions once performed cannot be undone. In many situations, atomicity is not possible with real actions (e.g., firing two rockets as a single atomic action)

### Embedded SQL example in C
This partial example targets PostgreSQL ECPG: assume the connection is established and the surrounding C program includes the required headers. ECPG preprocesses embedded EXEC SQL statements before the C compiler; this is not ODBC ([ECPG documentation](https://www.postgresql.org/docs/18/ecpg-concept.html)).

```c
EXEC SQL INCLUDE sqlca;

int main(void) {
    EXEC SQL BEGIN DECLARE SECTION;
    /* Host variables used to exchange values with SQL */
    int order_id;
    int cust_id;
    char salesperson[10];
    char status[6];
    EXEC SQL END DECLARE SECTION;

    EXEC SQL WHENEVER SQLERROR GOTO query_error;
    EXEC SQL WHENEVER NOT FOUND GOTO bad_number;
    printf("Enter order number: ");
    scanf("%d", &order_id);
    EXEC SQL SELECT CustID, SalesPerson, Status
        INTO :cust_id, :salesperson, :status
        FROM Orders
        WHERE OrderID = :order_id;
    printf("Customer number: %d\n", cust_id);
    printf("Salesperson: %s\n", salesperson);
    printf("Status: %s\n", status);
    return 0;

query_error:
    fprintf(stderr, "SQL error: %ld\n", sqlca.sqlcode);
    return 1;
bad_number:
    fprintf(stderr, "Invalid order number.\n");
    return 1;
    EXEC SQL WHENEVER SQLERROR CONTINUE;
    EXEC SQL WHENEVER NOT FOUND CONTINUE;
}
```

- **Host Variables** - Declared in a section enclosed by the **BEGIN** DECLARE SECTION and **END** DECLARE SECTION. While accessing these variables, they are prefixed by a colon “:”. The colon is essential to distinguish between host variables and database objects (for example tables and columns).
- **Data Types** - The data types supported by a DBMS and a host language can be quite different. e.g. if we have int type id in DB, we can't use string id in C
- **Error Handling** - The DBMS reports run-time errors to the applications program through an SQL Communications Area (SQLCA) by INCLUDE SQLCA. The WHENEVER...GOTO statement tells the pre-processor to generate error- handling code to process errors returned by the DBMS.
- **Singleton SELECT** - The statement used to return the data is a singleton SELECT statement; that is, it returns only a single row of data. Therefore, the code
  example does not declare or use cursors.

### Flat Transaction
Everything inside the BEGIN WORK and COMMIT WORK is at the same level. The transaction will either survive together with everything else (commit) Or it will be rolled back with everything else (abort) – if some errors happen

```c
/* PostgreSQL ECPG fragment; assumes an open connection and the preceding sample's global sqlca. */
long BuySomething(long acc_id, long amount) {
    EXEC SQL BEGIN DECLARE SECTION;
    long sql_acc_id;
    long sql_amount;
    long balance_after;
    EXEC SQL END DECLARE SECTION;
    sql_acc_id = acc_id;
    sql_amount = amount;

    EXEC SQL WHENEVER SQLERROR CONTINUE;
    EXEC SQL INSERT INTO history(AccId, Amount, time)
        VALUES (:sql_acc_id, :sql_amount, CURRENT_TIMESTAMP);
    if (sqlca.sqlcode < 0) return -1;
    EXEC SQL UPDATE accounts
        SET AccBalance = AccBalance - :sql_amount
        WHERE AccId = :sql_acc_id;
    if (sqlca.sqlcode < 0) return -1;
    EXEC SQL SELECT AccBalance INTO :balance_after
        FROM accounts
        WHERE AccId = :sql_acc_id;
    if (sqlca.sqlcode != 0) return -1;
    return balance_after; /* the post-update balance */
}

int process_purchase(long acc_id, long amount) {
    long acc_balance;
    EXEC SQL BEGIN WORK;
    if (sqlca.sqlcode < 0) return -1;
    acc_balance = BuySomething(acc_id, amount);
    if (sqlca.sqlcode < 0 || acc_balance < 0) {
        EXEC SQL ROLLBACK WORK;
        return -1;
    }
    EXEC SQL COMMIT WORK;
    return sqlca.sqlcode < 0 ? -1 : 0;
}
```

#### Flat Transaction - Limitation
Flat transactions do not model many real applications.

```
BEGIN WORK
S1 : book flight from Melbourne to Singapore S2: book flight from Singapore to London
S3: book flight from London to Dublin
END WORK
```

From Dublin if we cannot reach our final destination instead we wish to fly to Paris from Singapore and then reach our final destination.

If we roll back we need to redo the booking from Melbourne to Singapore which is a waste.

#### Flat Transaction – Solution: Save Points
![save-points](./save-points.png)

- The only reason why an application program needs an identifier for a savepoint is that it may later want to re-establish (return to) that savepoint.
- To do that, the application invokes the ROLLBACK WORK function, but rather than requesting the entire transaction to be aborted, it passes the number of the savepoint it wants to be restored.

### Nested Transaction
![nested transaction](nestedTransaction.png)
It is a tree of executions, T1 can have more T11 and T12.... The left hand side is called parent transaction.

#### Rules to follow in Nested Transaction
##### Commit rule
- In the course's closed-nesting model, a child may provisionally commit before its parent finishes; that result becomes visible to the parent but is not durable or externally visible until the root transaction commits.
- If an ancestor aborts, the provisional effects of its descendants are rolled back.

##### Roll back rules
- If a subtransaction rolls back all its children are forced to roll back

##### Visibility rules
- Changes made by a subtransaction are visible to the parent only when the subtransaction commits.
- All objects of parent are visible to its children.

Implication of this is that the parent should not modify objects while children are accessing them. This is not a problem as parent is not run in parallel with its children.

This course model does not run a parent and its child in parallel; sibling children may run in parallel.

### Transaction Processing Monitor (TP Monitor)
The main function of a TP monitor is to integrate other system components and manage resources.

- TP monitors manage the transfer of data between clients and servers
- breaks down applications or code into transactions and ensures that all databases are updated properly
- It also takes appropriate actions if any error occurs

### TP Monitor Services
- **Heterogeneity**: A transaction spanning different resource managers needs a coordinated outcome. Two-phase commit can coordinate atomic commit; isolation and application consistency require separate mechanisms.
- **Control communication**: If the application communicates with other **remote processes**, the local TP monitor should maintain the communication status among the processes to be able to recover from a crash.
- **Terminal management**: Since many terminals run client software, the TP monitor should provide appropriate ACID property between the client and the server processes.
- **Presentation service**: this is similar to terminal management in the sense it has to deal with different presentation ( user interface) software -- e.g. X-windows
- **Context management**: E.g. maintaining the sessions etc.
  Start/Restart: There is no difference between start and restart in TP based system.
