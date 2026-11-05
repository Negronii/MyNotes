# What does module voting guarantee under failvote and failfast? / failvote 与 failfast 的模块投票能保证什么？

Failvote accepts an output only when a strict majority of configured replicas agree. Failfast can continue with one survivor only under the self-checking-survivor assumption. These are different failure models and require different availability calculations. / failvote 只在配置副本的输出达到严格多数一致时接受结果。failfast 只有在幸存模块可自检这一假设下，才能依靠一个幸存模块继续运行。两者属于不同故障模型，需要不同的可用性计算。

## Fault Tolerance by Voting / 多数表决容错
### Definition of majority here
if n nodes, then:

- if n is odd, majority means $\frac{(n + 1)}{2}$
- if n is even, majority means $\frac{n}{2} + 1$

### Failvote
In the fail-vote/fail-fast model described by [Saltzer and Kaashoek, ch. 8](https://live.ocw.mit.edu/courses/res-6-004-principles-of-computer-system-design-an-introduction-spring-2009/6b31587ec59b1b002cb7a710d9781453_faults_open_5_0.pdf), a failvote voter accepts an output only when a strict majority of all configured replicas agrees. For three replicas, two matching outputs suffice; for four, three are required. A replica being powered on does not prove that its output is correct.

### Failfast
A self-checking fail-fast replica model can continue with one surviving replica after failed replicas are detected. An ordinary untrusted survivor cannot validate its answer by comparison with another result, so this is a model prerequisite rather than a guarantee for every fail-fast design. Detection errors and common-mode failures remain outside this simple model.

### Supermodule
A supermodule combines modules with a voter or comparator. Its failure condition depends on the design: a design that remains usable with one self-checking module fails only when all modules are unavailable; failvote has a stricter output-agreement threshold. Do not use the all-modules-down formula below for a failvote system.

#### Fault Tolerance with Repair
Assume independent module failures with a constant rate, immediate detection, and repair time with mean MTTR. In a two-state up/down model, one module's long-run unavailability is
$$q = \frac{MTTR}{MTTF + MTTR} \approx \frac{MTTR}{MTTF}$$
when MTTR is much smaller than MTTF. Values such as MTTR of a few hours to one day and MTTF of 750,000 hours (about 85.6 years) are illustrative inputs for this model, not a general current disk specification.

#### Approximate Failure Rate of a One-Available-Module Supermodule
For a supermodule that can operate with any one self-checking module available, the approximate rate of total failure is
$$\lambda_{sys} \approx n\lambda q^{n-1}, \qquad \lambda=1/MTTF,$$
when failures are rare, independent, and repaired independently. This follows because any of the n modules can fail while the other n-1 are unavailable. The result has units of failures per time; its reciprocal is an approximate MTTDL. It excludes common-cause failures, repair queues, latent errors, and voter failures. Failvote/failfast systems with a different voting threshold need a different failure-state calculation.
