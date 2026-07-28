# Day 45 — Unit Testing: JUnit 5 + Mockito
### Complete, From-Basics, Interview-Ready
*All examples are standalone (calculator, bank account, order service). Nothing here depends on any prior project.*

---

## HOW TO READ THIS GUIDE

Work through it **top to bottom**. Each concept follows the same 6-step pattern your teaching guide demands:

1. **What** is it?
2. **Why** does it exist?
3. **How** does it work internally?
4. **Real code** — every line explained
5. **Analogy**
6. **Interview-ready answer** (what you actually say in a room)

Don't skip Part 0. Interviewers test *why* you test before they test *how*.

---

# PART 0 — FOUNDATIONS (the "why" nobody explains)

## 0.1 What is a unit test?

A **unit test** is a small piece of code that runs **one tiny part of your application in isolation** and checks that it behaves correctly.

- "One tiny part" = a **unit** = usually **one method** (sometimes one class).
- "In isolation" = the unit is tested **without** its real dependencies (no real database, no real network, no real file system).
- "Checks behaviour" = you call the method with known inputs and **assert** the output is what you expect.

A unit test is just a **normal Java method** that:
1. sets up some input,
2. calls the method under test,
3. asserts the result.

## 0.2 What exactly is a "unit"?

A unit is the **smallest testable piece of behaviour**. In Java/Spring that is almost always **a single public method on a single class**.

Example — this whole class has two units (the two methods):

```java
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    public int divide(int a, int b) {
        return a / b;
    }
}
```

`add` is one unit. `divide` is another unit. You'd write tests for each separately.

## 0.3 Why do unit tests exist? (interviewers love this)

| Reason | What it means in practice |
|---|---|
| **Catch bugs early** | A bug caught by a unit test costs seconds. The same bug in production costs hours + reputation. |
| **Safe refactoring** | You can rewrite a method's internals; if tests still pass, you didn't break behaviour. Tests are a *safety net*. |
| **Living documentation** | A good test reads like a spec: "when balance is 100 and you withdraw 30, balance becomes 70." |
| **Design feedback** | If a class is *hard* to test, it's usually *badly designed* (too many responsibilities, hidden dependencies). |
| **Fast feedback** | Thousands of unit tests run in seconds because there's no DB/network. |

## 0.4 The Test Pyramid

```
            /\
           /  \      E2E / UI tests        (few, slow, brittle)
          /----\
         /      \    Integration tests     (some, medium speed)
        /--------\
       /          \  UNIT TESTS            (many, fast, cheap)  <-- you are here
      /------------\
```

**Why a pyramid?** Unit tests are fast and cheap, so you write **lots** of them. Integration/E2E tests are slow and fragile, so you write **fewer**. JUnit 5 + Mockito is the tooling for the **bottom layer**.

## 0.5 The structure of EVERY good test: AAA / Given-When-Then

Every single test you ever write follows this shape:

```
// Arrange  (Given) — set up inputs and dependencies
// Act      (When)  — call the one method you are testing
// Assert   (Then)  — check the result
```

Burn this into your memory. When you don't know how to start a test, write these three comments first, then fill them in.

## 0.6 FIRST — what makes a *good* unit test

| Letter | Principle | Meaning |
|---|---|---|
| **F** | Fast | Runs in milliseconds. No real DB/network. |
| **I** | Isolated / Independent | Doesn't depend on other tests or on run order. |
| **R** | Repeatable | Same result every run, on any machine. (No `LocalDateTime.now()`, no random, no real time zone surprises.) |
| **S** | Self-validating | It passes or fails automatically — no human reading logs. |
| **T** | Timely / Thorough | Written close to the code; covers the important cases. |

> **Interview answer:** *"A unit test verifies one unit of behaviour in isolation. I follow Arrange-Act-Assert and the FIRST principles — fast, isolated, repeatable, self-validating, timely. Unit tests sit at the base of the test pyramid because they're cheap and fast, so we write many of them; integration and end-to-end tests are fewer because they're slower and more brittle."*

---

# PART 1 — JUnit 5

## 1.1 What is JUnit 5? Its architecture (classic interview question)

**JUnit** is the testing **framework** — it finds your test methods, runs them, and reports pass/fail.

JUnit **5** is not one library. It is **three sub-projects** bundled together. This is the #1 JUnit architecture question:

```
JUnit 5  =  JUnit Platform  +  JUnit Jupiter  +  JUnit Vintage
```

| Piece | Job |
|---|---|
| **JUnit Platform** | The **foundation** that launches tests and lets build tools (Maven/Gradle) and IDEs discover and run them. It defines the `TestEngine` API. |
| **JUnit Jupiter** | The **new programming model** — the annotations and assertions you actually write (`@Test`, `assertEquals`, etc.). It's a `TestEngine` that runs on the Platform. |
| **JUnit Vintage** | A **backward-compatibility** engine that runs **old JUnit 3 and 4** tests on the new Platform, so teams can migrate gradually. |

**Why split it up?** So that *any* testing framework (not just JUnit) can plug into the same launcher via the `TestEngine` API. The Platform is the runway; Jupiter and Vintage are different planes that land on it.

> **Interview answer:** *"JUnit 5 is modular: the Platform is the launcher and engine API that IDEs and build tools talk to; Jupiter is the new test API and the engine for JUnit 5 tests; Vintage is the engine that runs legacy JUnit 4/3 tests so migration is gradual."*

## 1.2 Setup — the dependency (Maven)

You only need the **aggregator** dependency. It pulls in the API + engine + params.

```xml
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>   <!-- aggregator: api + engine + params -->
    <version>5.10.2</version>
    <scope>test</scope>                       <!-- only on the test classpath -->
</dependency>
```

Gradle:

```groovy
testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
test { useJUnitPlatform() }   // tell Gradle to run on the JUnit Platform
```

> `scope = test` is important: test code and test libraries must **never** ship in your production jar.

## 1.3 Your first test — anatomy, every line explained

```java
import org.junit.jupiter.api.Test;                  // the @Test annotation
import static org.junit.jupiter.api.Assertions.*;   // assertEquals, assertTrue, ...  (static import!)

class CalculatorTest {                               // package-private is fine — JUnit 5 doesn't need 'public'

    @Test                                            // marks this method as a test JUnit should run
    void add_returnsSumOfTwoNumbers() {              // method name = a sentence describing the behaviour
        // Arrange
        Calculator calculator = new Calculator();    // create the thing under test (the "SUT")

        // Act
        int result = calculator.add(2, 3);           // call the ONE method we're testing

        // Assert
        assertEquals(5, result);                     // expected first, actual second
    }
}
```

Line-by-line:
- `import static ... Assertions.*` — JUnit 5's assertions are **static methods**. The static import lets you write `assertEquals(...)` instead of `Assertions.assertEquals(...)`.
- `class CalculatorTest` — no `public` needed in JUnit 5 (a small but common interview trivia point — JUnit 4 *did* require public).
- `@Test` — without this annotation the method is ignored. JUnit 5's `@Test` comes from `org.junit.jupiter.api` (JUnit 4's came from `org.junit`).
- `void` and **no parameters** for a basic test (parameterized tests are the exception — see 1.10).
- `assertEquals(5, result)` — **convention: expected value first, actual value second.** Get this backwards and your failure messages read wrong.

## 1.4 Assertions — the full toolkit

Assertions are how a test decides pass/fail. If an assertion fails, it throws an `AssertionError` and the test is marked failed.

```java
import static org.junit.jupiter.api.Assertions.*;

@Test
void assertionShowcase() {
    // equality / truthiness
    assertEquals(4, 2 + 2);                      // pass if equal (.equals for objects)
    assertNotEquals(5, 2 + 2);                   // pass if NOT equal
    assertTrue(3 > 2);                           // pass if condition true
    assertFalse(2 > 3);                          // pass if condition false

    // null checks
    String name = "Deepa";
    assertNull(null);
    assertNotNull(name);

    // reference identity (same object, ==) vs value equality
    String a = new String("x");
    String b = new String("x");
    assertEquals(a, b);                          // true: same value
    assertNotSame(a, b);                         // true: different objects
    assertSame(a, a);                            // true: identical reference

    // arrays & iterables
    assertArrayEquals(new int[]{1,2,3}, new int[]{1,2,3});
    assertIterableEquals(List.of(1,2), List.of(1,2));

    // floating point needs a delta (rounding!)
    assertEquals(0.3, 0.1 + 0.2, 0.0001);        // 0.1+0.2 != 0.3 exactly in binary floating point

    // custom failure message (lazy — only built if it fails)
    assertEquals(5, 2 + 3, () -> "math is broken");
}
```

### `assertAll` — group assertions so you see ALL failures, not just the first

Normally the first failed assertion stops the test. `assertAll` runs every assertion and reports **all** failures together.

```java
@Test
void person_hasCorrectFields() {
    Person p = new Person("Asha", 30, "asha@mail.com");

    assertAll("person",
        () -> assertEquals("Asha", p.getName()),
        () -> assertEquals(30, p.getAge()),
        () -> assertEquals("asha@mail.com", p.getEmail())
    );
    // If name AND age are both wrong, you see BOTH, not just the first.
}
```

### `fail()` — force a failure

```java
@Test
void notImplementedYet() {
    fail("write this test");   // useful as a placeholder
}
```

## 1.5 Testing that an exception is thrown — `assertThrows`

This is huge. Interviewers always ask "how do you test the error path?"

```java
public class Calculator {
    public int divide(int a, int b) {
        if (b == 0) throw new ArithmeticException("cannot divide by zero");
        return a / b;
    }
}
```

```java
@Test
void divide_byZero_throwsArithmeticException() {
    Calculator calc = new Calculator();

    // assertThrows runs the lambda and checks the RIGHT exception type is thrown.
    // It RETURNS the caught exception so you can inspect it.
    ArithmeticException ex = assertThrows(
            ArithmeticException.class,        // expected type (subclasses also match)
            () -> calc.divide(10, 0)          // the code that should throw
    );

    assertEquals("cannot divide by zero", ex.getMessage());   // also assert the message
}
```

- If **no** exception is thrown → test **fails**.
- If a **different** exception type is thrown → test **fails**.
- `assertThrowsExactly(...)` is stricter: subclasses do **not** match.

There's also `assertDoesNotThrow(() -> calc.divide(10, 2))` to assert the happy path doesn't blow up.

## 1.6 Lifecycle annotations — setup & teardown

Tests often share setup. JUnit gives you hooks that run **around** your tests.

```java
import org.junit.jupiter.api.*;

class BankAccountTest {

    BankAccount account;

    @BeforeAll                                  // runs ONCE before all tests in the class
    static void beforeAll() {                   // must be static (by default — see lifecycle below)
        System.out.println("opening test suite (e.g. start a shared resource)");
    }

    @BeforeEach                                 // runs before EACH test — fresh state per test!
    void setUp() {
        account = new BankAccount(100);         // every test gets a brand-new account with balance 100
    }

    @Test
    void deposit_increasesBalance() {
        account.deposit(50);
        assertEquals(150, account.getBalance());
    }

    @Test
    void withdraw_decreasesBalance() {
        account.withdraw(40);
        assertEquals(60, account.getBalance());   // 60, not 110 — because @BeforeEach reset it
    }

    @AfterEach                                  // runs after EACH test — cleanup
    void tearDown() {
        account = null;
    }

    @AfterAll                                   // runs ONCE after all tests
    static void afterAll() {
        System.out.println("closing test suite");
    }
}
```

**Order of execution for a 2-test class:**
```
@BeforeAll
   @BeforeEach -> test1 -> @AfterEach
   @BeforeEach -> test2 -> @AfterEach
@AfterAll
```

**Why `@BeforeEach` instead of doing setup once?** Because of the **I** in FIRST — *Isolated*. Each test must start from a clean state, so tests can't pollute each other. `@BeforeEach` guarantees freshness.

## 1.7 Test instance lifecycle — `PER_METHOD` vs `PER_CLASS` (favourite interview trap)

**Default behaviour:** JUnit 5 creates a **brand-new instance of your test class for every single `@Test` method** (`PER_METHOD`). This is *why* `@BeforeAll`/`@AfterAll` must be **static** — there's no single instance to hang them on.

You can change it:

```java
@TestInstance(TestInstance.Lifecycle.PER_CLASS)   // ONE instance shared across all tests
class MyTest {
    @BeforeAll
    void beforeAll() { }       // now it can be NON-static, because one instance exists
}
```

| | `PER_METHOD` (default) | `PER_CLASS` |
|---|---|---|
| Instances created | One per test method | One for the whole class |
| `@BeforeAll`/`@AfterAll` | must be `static` | can be non-static |
| State between tests | not shared (good for isolation) | shared (be careful!) |

> **Interview answer:** *"By default JUnit 5 instantiates the test class once per test method to keep tests isolated, which is why `@BeforeAll`/`@AfterAll` are static. With `@TestInstance(PER_CLASS)` it reuses one instance, so those lifecycle methods can be non-static — handy for expensive shared setup, but you must avoid leaking state between tests."*

## 1.8 Readability & control annotations

```java
@Test
@DisplayName("withdrawing more than the balance throws")   // human-friendly name in reports
void withdraw_overdraft_throws() { ... }

@Test
@Disabled("flaky — fix in TICKET-123")   // skip this test, with a reason
void temporarilyOff() { ... }

@Test
@Tag("slow")                              // categorise tests; run/exclude by tag in CI
void bigTest() { ... }
```

## 1.9 Assumptions — skip a test when a precondition isn't met

An **assertion** *fails* the test if false. An **assumption** *aborts (skips)* the test if false — it's not a failure, just "not applicable here."

```java
import static org.junit.jupiter.api.Assumptions.*;

@Test
void onlyOnLinux() {
    assumeTrue(System.getProperty("os.name").contains("Linux"));   // if not Linux -> test is skipped, not failed
    // ... Linux-specific assertions
}
```

Use sparingly — mostly for environment-specific tests.

## 1.10 Parameterized tests — run the SAME test with MANY inputs (high value)

Instead of copy-pasting a test 6 times for 6 inputs, run it once per input.

Add the dependency (already included in the `junit-jupiter` aggregator): `junit-jupiter-params`.

```java
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;

class NumberUtilsTest {

    // @ValueSource: one simple argument per run
    @ParameterizedTest
    @ValueSource(ints = {2, 4, 6, 100, -8})
    void isEven_returnsTrueForEvenNumbers(int number) {
        assertTrue(NumberUtils.isEven(number));     // runs 5 times, once per value
    }

    // @CsvSource: multiple arguments per run, comma-separated
    @ParameterizedTest
    @CsvSource({
        "2, 3, 5",      // input1, input2, expected
        "0, 0, 0",
        "-1, 1, 0",
        "10, 20, 30"
    })
    void add_addsCorrectly(int a, int b, int expected) {
        assertEquals(expected, new Calculator().add(a, b));
    }

    // @EnumSource: one run per enum constant
    @ParameterizedTest
    @EnumSource(Day.class)
    void everyDay_hasAName(Day day) {
        assertNotNull(day.name());
    }

    // @MethodSource: arguments come from a method returning a Stream<Arguments>
    @ParameterizedTest
    @MethodSource("discountCases")
    void discount_isCalculated(double price, int percent, double expected) {
        assertEquals(expected, DiscountCalculator.apply(price, percent), 0.001);
    }

    static Stream<Arguments> discountCases() {
        return Stream.of(
            Arguments.of(100.0, 10, 90.0),
            Arguments.of(50.0, 50, 25.0),
            Arguments.of(0.0, 20, 0.0)
        );
    }

    // @NullAndEmptySource + @ValueSource: classic for input validation
    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {" ", "   "})
    void isBlank_detectsBlankStrings(String input) {
        assertTrue(StringUtils.isBlank(input));     // tests null, "", " ", "   "
    }
}
```

> **Interview answer:** *"Parameterized tests run the same logic against many inputs. I use `@ValueSource` for a single arg, `@CsvSource`/`@MethodSource` for multiple args, `@EnumSource` for enums, and `@NullAndEmptySource` for validation edge cases. It removes duplication and forces me to think about boundary values."*

## 1.11 `@RepeatedTest` and `@Nested`

```java
@RepeatedTest(5)                       // run this test 5 times (e.g. to surface flakiness)
void shuffle_producesValidDeck() { ... }
```

`@Nested` groups related tests into inner classes for readability — like chapters:

```java
class BankAccountTest {

    @Nested
    @DisplayName("when depositing")
    class Deposits {
        @Test void positiveAmount_increasesBalance() { ... }
        @Test void negativeAmount_throws() { ... }
    }

    @Nested
    @DisplayName("when withdrawing")
    class Withdrawals {
        @Test void withinBalance_succeeds() { ... }
        @Test void overdraft_throws() { ... }
    }
}
```

## 1.12 Naming conventions (interviewers judge this instantly)

Three common styles — pick one and be consistent:

```
methodUnderTest_condition_expectedResult     // withdraw_whenOverdraft_throwsException
should_expected_when_condition               // should_throw_whenOverdraft
given_when_then                              // givenOverdraft_whenWithdraw_thenThrow
```

A good test name lets a reader understand the behaviour **without reading the body**.

---

# PART 2 — MOCKITO

## 2.1 The problem Mockito solves

Real classes have **dependencies**. Look at this service:

```java
public class OrderService {

    private final PaymentGateway paymentGateway;     // talks to a real payment provider (network!)
    private final InventoryRepository inventory;     // talks to a real database!

    public OrderService(PaymentGateway paymentGateway, InventoryRepository inventory) {
        this.paymentGateway = paymentGateway;
        this.inventory = inventory;
    }

    public String placeOrder(String item, int qty) {
        if (!inventory.isAvailable(item, qty)) {
            return "OUT_OF_STOCK";
        }
        boolean paid = paymentGateway.charge(item, qty);
        if (!paid) {
            return "PAYMENT_FAILED";
        }
        inventory.reduce(item, qty);
        return "CONFIRMED";
    }
}
```

To **unit test** `placeOrder`, you must NOT call the real payment provider or real database, because:
- it's **slow** (network/DB),
- it's **unreliable** (provider could be down),
- it has **side effects** (real money, real data),
- you can't easily force the "payment failed" case on demand.

You need **fake stand-ins** for `PaymentGateway` and `InventoryRepository` that you control. That's exactly what **Mockito** creates.

## 2.2 Test doubles taxonomy (interviewers ask the difference)

"Test double" is the umbrella term for any fake object that stands in for a real one (like a movie stunt double).

| Type | What it does |
|---|---|
| **Dummy** | Passed around but never used. Just fills a parameter slot. |
| **Stub** | Returns hard-coded answers to calls. ("When asked X, return Y.") |
| **Mock** | A stub that also **records interactions**, so you can verify it was called correctly. |
| **Spy** | Wraps a **real** object; real methods run unless you stub them. (Partial mock.) |
| **Fake** | A working but lightweight implementation (e.g. an in-memory `HashMap` instead of a DB). |

Mockito's `mock()` creates **mocks** (which you also use as stubs). `spy()` creates **spies**.

> **Interview answer:** *"A stub provides canned responses; a mock additionally lets me verify how it was called; a spy wraps a real object for partial mocking; a fake is a real but simplified implementation. Mockito gives me mocks and spies."*

## 2.3 Creating a mock — the manual way (understand this first)

```java
import static org.mockito.Mockito.*;

@Test
void placeOrder_whenInStockAndPaid_confirms() {
    // Arrange — create FAKE dependencies
    PaymentGateway payment = mock(PaymentGateway.class);     // a fake PaymentGateway
    InventoryRepository inventory = mock(InventoryRepository.class);

    // Program the fakes (STUBBING): tell them what to return
    when(inventory.isAvailable("book", 1)).thenReturn(true);
    when(payment.charge("book", 1)).thenReturn(true);

    OrderService service = new OrderService(payment, inventory);  // inject the fakes

    // Act
    String result = service.placeOrder("book", 1);

    // Assert
    assertEquals("CONFIRMED", result);
}
```

What `mock(PaymentGateway.class)` does internally: Mockito generates a **subclass/proxy** of `PaymentGateway` at runtime (using bytecode generation). Every method on that proxy returns a **default value** until you stub it:
- objects → `null`
- `int`/`long` → `0`
- `boolean` → `false`
- collections → empty collection

That default behaviour is why an un-stubbed mock won't crash — it just returns "nothing."

## 2.4 The annotation way — `@Mock`, `@InjectMocks`, `@ExtendWith`

Cleaner, and what you'll see in real codebases.

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)            // 1. activates Mockito annotations for this class
class OrderServiceTest {

    @Mock PaymentGateway payment;              // 2. Mockito creates a mock and assigns it here
    @Mock InventoryRepository inventory;       //    (same as: payment = mock(PaymentGateway.class))

    @InjectMocks OrderService service;         // 3. Mockito creates a real OrderService and INJECTS
                                               //    the two mocks above into it (via constructor)

    @Test
    void placeOrder_whenOutOfStock_returnsOutOfStock() {
        when(inventory.isAvailable("pen", 5)).thenReturn(false);   // force out-of-stock

        String result = service.placeOrder("pen", 5);

        assertEquals("OUT_OF_STOCK", result);
        verify(payment, never()).charge(anyString(), anyInt());     // payment must NOT be charged
    }
}
```

Three pieces:
- `@ExtendWith(MockitoExtension.class)` — the JUnit 5 hook that processes the Mockito annotations before each test. (In JUnit 4 it was `@RunWith(MockitoJUnitRunner.class)` — common trivia.)
- `@Mock` — "create a mock and store it in this field."
- `@InjectMocks` — "create a *real* object here and inject all the `@Mock` fields into it."

**`@InjectMocks` injection order (interview detail):** Mockito tries, in order:
1. **Constructor injection** (preferred),
2. **setter injection**,
3. **field injection**.

> **Interview answer:** *"`@ExtendWith(MockitoExtension.class)` enables Mockito's annotations. `@Mock` creates mocks; `@InjectMocks` builds a real instance and injects those mocks, preferring constructor injection, then setters, then fields. It's the cleaner equivalent of calling `mock()` and wiring by hand."*

## 2.5 Stubbing — `thenReturn`, `thenThrow`, `thenAnswer`

Stubbing = "when this method is called with these args, do this."

```java
// return a value
when(inventory.isAvailable("book", 1)).thenReturn(true);

// return different values on consecutive calls
when(inventory.count("book")).thenReturn(5, 4, 3);   // 1st call->5, 2nd->4, 3rd->3, then ->3 forever

// throw an exception (test the error path)
when(payment.charge("book", 1)).thenThrow(new RuntimeException("gateway down"));

// compute the answer dynamically from the actual arguments
when(payment.charge(anyString(), anyInt()))
        .thenAnswer(invocation -> {
            String item = invocation.getArgument(0);   // read the real arg passed at call time
            int qty = invocation.getArgument(1);
            return qty < 100;                           // "succeeds" only for small quantities
        });
```

## 2.6 Verification — `verify`, and verification modes

Stubbing controls **inputs**; verification checks **interactions** (was the dependency called the right way?).

```java
@Test
void placeOrder_whenConfirmed_reducesInventory() {
    when(inventory.isAvailable("book", 2)).thenReturn(true);
    when(payment.charge("book", 2)).thenReturn(true);

    service.placeOrder("book", 2);

    // verify the side effect happened with the EXACT arguments
    verify(inventory).reduce("book", 2);              // called exactly once (default)
}
```

Verification modes:

```java
verify(inventory, times(1)).reduce("book", 2);   // exactly once (same as default)
verify(payment, never()).charge(any(), anyInt()); // never called
verify(inventory, atLeastOnce()).isAvailable(any(), anyInt());
verify(inventory, atLeast(2)).isAvailable(any(), anyInt());
verify(inventory, atMost(3)).isAvailable(any(), anyInt());

verifyNoInteractions(payment);                    // mock was never touched at all
verifyNoMoreInteractions(inventory);              // nothing happened beyond what we already verified
```

**Order verification** with `InOrder`:

```java
InOrder inOrder = inOrder(payment, inventory);
inOrder.verify(inventory).isAvailable("book", 2);   // must happen first
inOrder.verify(payment).charge("book", 2);          // then this
inOrder.verify(inventory).reduce("book", 2);        // then this
```

## 2.7 Argument matchers — `any()`, `eq()`, `argThat()` (a classic gotcha)

When you don't care about the exact argument, use **matchers**.

```java
when(inventory.isAvailable(anyString(), anyInt())).thenReturn(true);
verify(payment).charge(anyString(), eq(2));   // any item, but qty must equal 2
```

Common matchers: `any()`, `anyString()`, `anyInt()`, `anyList()`, `eq(value)`, `isNull()`, `argThat(predicate)`.

### THE GOTCHA (you WILL be asked or burned by this)

> **If you use even ONE matcher in a call, you must use matchers for ALL arguments of that call.** You cannot mix a raw value with a matcher.

```java
// ❌ WRONG — mixing raw value "book" with matcher anyInt()
verify(payment).charge("book", anyInt());     // throws InvalidUseOfMatchersException

// ✅ RIGHT — wrap the raw value in eq()
verify(payment).charge(eq("book"), anyInt());
```

**Why?** Matchers aren't real values — they register themselves on an internal stack as a side effect. Mixing a real value confuses the stack. So: all-matchers or all-raw, never a mix.

## 2.8 `ArgumentCaptor` — capture and inspect what a mock was called with

Sometimes you want to assert on a **complex object** that was passed to a dependency.

```java
import org.mockito.ArgumentCaptor;

@Test
void register_savesUserWithTrimmedEmail() {
    UserRepository repo = mock(UserRepository.class);
    UserService service = new UserService(repo);

    service.register("Asha", "  asha@mail.com  ");   // note the spaces

    // capture the User object that was passed to repo.save(...)
    ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
    verify(repo).save(captor.capture());             // capture during verification

    User saved = captor.getValue();                  // pull out the captured argument
    assertEquals("asha@mail.com", saved.getEmail()); // assert email was trimmed before saving
    assertEquals("Asha", saved.getName());
}
```

Use a captor when the argument is built **inside** the method and you need to verify its contents.

## 2.9 Mocking `void` methods — `doNothing`, `doThrow`

You **cannot** write `when(mock.voidMethod())` — `void` returns nothing, so there's nothing to pass to `when(...)`. Use the `do*` family instead:

```java
EmailService email = mock(EmailService.class);   // sendEmail(...) returns void

doNothing().when(email).sendEmail(anyString());           // explicit no-op (default anyway)
doThrow(new RuntimeException("smtp down"))                // make a void method throw
        .when(email).sendEmail("bad@mail.com");

// verify a void method was called
verify(email).sendEmail("good@mail.com");
```

## 2.10 `@Spy` and the `doReturn` vs `thenReturn` trap (top interview gotcha)

A **spy** wraps a **real** object. Real methods run for real **unless** you stub them.

```java
List<String> realList = new ArrayList<>();
List<String> spyList = spy(realList);

spyList.add("a");                 // REAL add runs — actually adds to the list
assertEquals(1, spyList.size());  // real size() runs -> 1

// you can still stub specific methods:
doReturn(100).when(spyList).size();   // now size() is faked
assertEquals(100, spyList.size());
```

### Why `doReturn().when()` and not `when().thenReturn()` on a spy?

```java
// ❌ DANGEROUS on a spy:
when(spyList.get(99)).thenReturn("x");
// Problem: when() must EVALUATE spyList.get(99) to register the stub.
// On a spy, that calls the REAL get(99) FIRST -> IndexOutOfBoundsException!

// ✅ SAFE on a spy:
doReturn("x").when(spyList).get(99);
// doReturn(...).when(spy) does NOT call the real method while stubbing.
```

> **Interview answer:** *"A spy is a partial mock around a real object — real methods execute unless stubbed. On a spy I stub with `doReturn(...).when(spy).method()` rather than `when(spy.method()).thenReturn(...)`, because the second form actually invokes the real method while setting up the stub, which can throw or cause side effects."*

## 2.11 BDD-style Mockito — `given` / `willReturn`

Same behaviour, more readable Given-When-Then vocabulary. Many teams prefer it.

```java
import static org.mockito.BDDMockito.*;

given(inventory.isAvailable("book", 1)).willReturn(true);   // == when(...).thenReturn(...)
given(payment.charge("book", 1)).willReturn(true);

String result = service.placeOrder("book", 1);

then(inventory).should().reduce("book", 1);                 // == verify(inventory).reduce(...)
```

## 2.12 Strictness & `UnnecessaryStubbingException`

`MockitoExtension` runs in **strict stubs** mode by default. If you write a stub that is **never used**, the test fails with `UnnecessaryStubbingException`.

```java
// This will FAIL if charge(...) is never actually called during the test:
when(payment.charge("book", 1)).thenReturn(true);   // unused stub -> UnnecessaryStubbingException
```

**Why strict?** Unused stubs are usually a bug or dead code — they signal the test doesn't exercise what you think it does. To deliberately allow a sometimes-unused stub, use `lenient()`:

```java
lenient().when(payment.charge(any(), anyInt())).thenReturn(true);
```

> **Interview answer:** *"`MockitoExtension` is strict by default and flags unused stubs with `UnnecessaryStubbingException`, which catches dead or wrong stubbing. I use `lenient()` only when a stub is intentionally shared across tests where some don't use it."*

## 2.13 Mocking `static` methods — `mockStatic` (modern, advanced)

Historically you couldn't mock static methods. Mockito 5 (and Mockito 3.4+ with `mockito-inline`) can, via `mockStatic`. In Mockito 5 the inline mock maker is the default, so no extra dependency is needed.

```java
// Suppose: public final class IdGenerator { public static String newId() { ... } }

@Test
void usesGeneratedId() {
    try (MockedStatic<IdGenerator> mocked = mockStatic(IdGenerator.class)) {   // scoped!
        mocked.when(IdGenerator::newId).thenReturn("FIXED-123");

        assertEquals("FIXED-123", IdGenerator.newId());                        // returns the stub

        mocked.verify(IdGenerator::newId);                                     // verify it was called
    }
    // OUTSIDE the try-with-resources, IdGenerator behaves normally again.
}
```

The **try-with-resources** is essential: the static mock is active only inside the block, and only on the current thread. Leaking it would corrupt other tests.

> Use static mocking as a **last resort**. Static dependencies are a design smell; prefer injecting dependencies so you can mock them normally.

## 2.14 What you can / should NOT mock

- **Don't mock the class you're testing** — you'd be testing the mock, not your code.
- **Don't mock value objects / DTOs** (e.g. `String`, `Integer`, a simple `Money`) — just create real ones.
- **Don't mock types you don't own** blindly (3rd-party clients) — wrap them behind your own interface and mock that.
- **Can't mock** `final` classes/methods or `static`/`private` with the *legacy* mock maker — but the inline mock maker (default in Mockito 5) handles `final` and `static`.
- **Mock the things at the boundary:** repositories, gateways, external services, anything slow or with side effects.

---

# PART 3 — PUTTING IT ALL TOGETHER (a full, realistic service test)

The class under test (neutral domain — an order service):

```java
public class OrderService {
    private final PaymentGateway payment;
    private final InventoryRepository inventory;
    private final EmailService email;

    public OrderService(PaymentGateway payment, InventoryRepository inventory, EmailService email) {
        this.payment = payment;
        this.inventory = inventory;
        this.email = email;
    }

    public String placeOrder(String item, int qty, String customerEmail) {
        if (qty <= 0) throw new IllegalArgumentException("qty must be positive");
        if (!inventory.isAvailable(item, qty)) return "OUT_OF_STOCK";

        boolean paid = payment.charge(item, qty);
        if (!paid) return "PAYMENT_FAILED";

        inventory.reduce(item, qty);
        email.sendEmail(customerEmail);     // void
        return "CONFIRMED";
    }
}
```

The complete test class — covering every branch:

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock PaymentGateway payment;
    @Mock InventoryRepository inventory;
    @Mock EmailService email;
    @InjectMocks OrderService service;

    @Test
    @DisplayName("non-positive quantity is rejected")
    void placeOrder_zeroQty_throws() {
        IllegalArgumentException ex = assertThrows(
                IllegalArgumentException.class,
                () -> service.placeOrder("book", 0, "a@mail.com"));
        assertEquals("qty must be positive", ex.getMessage());

        verifyNoInteractions(payment, inventory, email);   // bailed out before touching anything
    }

    @Test
    @DisplayName("out of stock -> no payment, no email")
    void placeOrder_outOfStock() {
        when(inventory.isAvailable("book", 3)).thenReturn(false);

        String result = service.placeOrder("book", 3, "a@mail.com");

        assertEquals("OUT_OF_STOCK", result);
        verify(payment, never()).charge(any(), anyInt());
        verify(email, never()).sendEmail(any());
    }

    @Test
    @DisplayName("payment fails -> inventory not reduced, no email")
    void placeOrder_paymentFails() {
        when(inventory.isAvailable("book", 1)).thenReturn(true);
        when(payment.charge("book", 1)).thenReturn(false);

        String result = service.placeOrder("book", 1, "a@mail.com");

        assertEquals("PAYMENT_FAILED", result);
        verify(inventory, never()).reduce(any(), anyInt());
        verify(email, never()).sendEmail(any());
    }

    @Test
    @DisplayName("happy path -> charge, reduce stock, email sent, CONFIRMED")
    void placeOrder_success() {
        when(inventory.isAvailable("book", 2)).thenReturn(true);
        when(payment.charge("book", 2)).thenReturn(true);

        String result = service.placeOrder("book", 2, "a@mail.com");

        assertEquals("CONFIRMED", result);

        InOrder order = inOrder(inventory, payment, email);
        order.verify(inventory).isAvailable("book", 2);
        order.verify(payment).charge("book", 2);
        order.verify(inventory).reduce("book", 2);
        order.verify(email).sendEmail("a@mail.com");
    }

    @Test
    @DisplayName("gateway throws -> exception propagates, stock untouched")
    void placeOrder_gatewayThrows() {
        when(inventory.isAvailable("book", 1)).thenReturn(true);
        when(payment.charge("book", 1)).thenThrow(new RuntimeException("gateway down"));

        assertThrows(RuntimeException.class,
                () -> service.placeOrder("book", 1, "a@mail.com"));

        verify(inventory, never()).reduce(any(), anyInt());
    }
}
```

Notice the strategy: **one test per branch** of the method (validation, out-of-stock, payment-fail, success, exception). That's how you get to meaningful coverage.

---

# PART 4 — BEST PRACTICES & CODE COVERAGE

## 4.1 Do / Don't

**Do:**
- One **behaviour** per test (not necessarily one assertion, but one logical thing).
- Name tests so the behaviour is obvious without reading the body.
- Test the **public behaviour**, not private internals.
- Cover the **edge cases**: null, empty, zero, negative, boundary, max.
- Keep tests **fast and independent** (FIRST).

**Don't:**
- Don't test the framework or getters/setters with no logic.
- Don't over-mock — if you mock everything, you test nothing real.
- Don't write tests that depend on run order or shared mutable state.
- Don't assert on implementation details that legitimate refactors would break.

## 4.2 Code coverage — and its trap

**Code coverage** = the % of your code lines/branches executed by tests (measured by **JaCoCo**).

The trap interviewers probe: **100% coverage does NOT mean correct.** You can execute every line and assert nothing meaningful:

```java
@Test
void uselessButFullCoverage() {
    new Calculator().divide(10, 2);   // line executed... but NO assertion. Proves nothing.
}
```

> **Interview answer:** *"Coverage tells me what code my tests touched, not whether the behaviour is correct. I treat ~80% as a healthy guideline, focus coverage on business logic and branches, and never chase 100% with assertion-free tests. Meaningful assertions matter more than the number."*

## 4.3 Mockito + Spring Boot (just so you recognise it)

In Spring Boot tests you'll see `@MockBean` (older) / `@MockitoBean` (newer) which put a Mockito mock **into the Spring context**, replacing the real bean. But **pure unit tests don't need Spring at all** — plain `@ExtendWith(MockitoExtension.class)` is faster because it doesn't start a context. Prefer the plain unit test for testing logic; reserve Spring-context tests for integration.

---

# PART 5 — INTERVIEW Q&A BANK

**Rapid-fire (one-liners):**

1. **JUnit 4 vs 5 package?** 4: `org.junit` / `@RunWith`. 5: `org.junit.jupiter.api` / `@ExtendWith`.
2. **Three parts of JUnit 5?** Platform, Jupiter, Vintage.
3. **`@Before` (JUnit4) equivalent in 5?** `@BeforeEach`. `@BeforeClass` → `@BeforeAll`.
4. **Why are `@BeforeAll`/`@AfterAll` static?** Default `PER_METHOD` lifecycle = new instance per test, so no instance to attach them to.
5. **Assert exception thrown?** `assertThrows(Type.class, () -> code())`.
6. **assertEquals arg order?** `(expected, actual)`.
7. **`@Mock` vs `@InjectMocks`?** Mock creates a fake; InjectMocks builds the real object and injects the mocks.
8. **Stub a void method?** `doNothing()/doThrow().when(mock).method()`.
9. **Spy stubbing form?** `doReturn(x).when(spy).method()` (avoids running the real method).
10. **Matcher rule?** All args matchers or all raw — never mix; wrap raw in `eq()`.
11. **`when().thenReturn()` vs `verify()`?** Stubbing inputs vs verifying interactions.
12. **`UnnecessaryStubbingException`?** A stub was never used; Mockito is strict by default; use `lenient()` to allow.
13. **Mock a static method?** `mockStatic(...)` inside try-with-resources (Mockito 5 inline by default).
14. **What returns an un-stubbed mock method?** Default value: null / 0 / false / empty collection.

**Deeper questions to rehearse out loud:**

- *"Walk me through how you'd unit test a service that calls a repository and an external API."* → Mock both dependencies, stub their returns, inject via `@InjectMocks`, test each branch (happy path, each failure), verify the right side effects and that no forbidden calls happened.
- *"How is a mock different from a spy?"* → See 2.10.
- *"Your test passes but the feature is broken in prod. How can a unit test miss a bug?"* → Over-mocking (mocked the very thing that's broken), missing branch/edge case, testing implementation not behaviour, or the bug is at an integration boundary that unit tests don't cover — which is why the test pyramid also has integration tests.
- *"How do you test time-dependent code (`LocalDateTime.now()`)?"* → Inject a `Clock`; in tests use `Clock.fixed(...)` so results are repeatable (the R in FIRST). Avoid calling `now()` directly inside business logic.

---

# PART 6 — DO IT YOURSELF (practice — this is where it sticks)

Reading isn't learning; writing tests is. Implement these tiny classes and test them fully:

1. **`StringUtils.reverse(String)`** — test: normal word, empty string, single char, `null` (decide: throw or return null, then test that).
2. **`Calculator.divide(int,int)`** — test: normal, divide-by-zero throws, negative numbers. Make it a **parameterized** test.
3. **`BankAccount`** with `deposit`, `withdraw`, `getBalance` — test: deposit increases, withdraw decreases, overdraft throws, negative deposit throws. Use `@BeforeEach` to create a fresh account.
4. **`NotificationService`** that depends on a mocked `MessageSender` (void `send(String)`) and a mocked `UserRepository` (`findEmail(id)`) — test: when user exists, email is sent to the right address (use `ArgumentCaptor` or `verify(... ).send(eq(email))`); when user not found, sender is **never** called.
5. **`DiscountCalculator.apply(price, percent)`** — parameterized with `@CsvSource`, include boundary cases (0%, 100%, price 0).

When you finish each, paste it to me and ask: *"Review this and tell me what a senior engineer would say."* — and I'll critique it the way your guide intends.

---

## TODAY'S CHECKLIST (Day 45)

- [ ] Can explain unit test, the unit, the test pyramid, AAA, FIRST — out loud.
- [ ] Can explain the 3 parts of JUnit 5.
- [ ] Wrote tests using `@Test`, assertions, `assertThrows`, lifecycle hooks, a parameterized test.
- [ ] Can explain `PER_METHOD` vs `PER_CLASS`.
- [ ] Created mocks with `@Mock` + `@InjectMocks` + `@ExtendWith(MockitoExtension.class)`.
- [ ] Used `when/thenReturn`, `verify`, matchers (and know the mixing rule), `ArgumentCaptor`, void stubbing.
- [ ] Can explain mock vs spy and the `doReturn` rule.
- [ ] Did at least 3 of the Part 6 exercises.

Aim for being able to **explain each interview answer aloud without notes** before moving to Day 46.
